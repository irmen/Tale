"""
Mud driver (server).

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import collections
from functools import total_ordering
import datetime
import sys
import time
import os
import heapq
import inspect
import argparse
import pickle
import threading
from . import mud_context
from . import errors
from . import util
from . import soul
from . import cmds
from . import player
from . import __version__ as tale_version_str
from .io import vfs
from .io.iobase import TabCompleter
from .io import DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_DELAY


@total_ordering
class Deferred(object):
    __slots__ = ("due", "owner", "callable", "vargs", "kwargs")

    def __init__(self, due, owner, callable, vargs, kwargs):
        assert due is None or isinstance(due, datetime.datetime)
        self.due = due   # in game time
        self.owner = owner
        self.callable = callable
        self.vargs = vargs
        self.kwargs = kwargs

    def __eq__(self, other):
        return self.due == other.due

    def __lt__(self, other):
        return self.due < other.due   # deferreds must be sortable

    def when_due(self, game_clock, realtime=False):
        """
        In what timeframe is this deferred due to occur? (timedelta)
        Normally it is in terms of game-time, but if you pass realtime=True,
        you will get the real-time timedelta.
        """
        secs = (self.due - game_clock.clock).total_seconds()
        if realtime:
            secs = int(secs / game_clock.times_realtime)
        return datetime.timedelta(seconds=secs)

    def __call__(self, *args, **kwargs):
        self.kwargs = self.kwargs or {}
        if "driver" in kwargs:
            self.kwargs["driver"] = kwargs["driver"]  # always add a 'driver' keyword argument for convenience
        if self.owner is None:
            # deferred callable is stored as a normal callable object
            self.callable(*self.vargs, **self.kwargs)
        else:
            # deferred callable is stored as a name, so we need to obtain the actual function
            callable = getattr(self.owner, self.callable, None)
            if callable:
                callable(*self.vargs, **self.kwargs)


class Commands(object):
    def __init__(self):
        self.commands_per_priv = {None: {}}
        self.no_soul_parsing = set()

    def add(self, verb, func, privilege=None):
        self.validateFunc(func)
        for commands in self.commands_per_priv.values():
            if verb in commands:
                raise ValueError("command defined more than once: " + verb)
        self.commands_per_priv.setdefault(privilege, {})[verb] = func

    def override(self, verb, func, privilege=None):
        self.validateFunc(func)
        if verb in self.commands_per_priv[privilege]:
            existing = self.commands_per_priv[privilege][verb]
            self.commands_per_priv[privilege][verb] = func
            return existing
        raise KeyError("command not defined: " + verb)

    def validateFunc(self, func):
        if not hasattr(func, "is_tale_command_func"):
            raise ValueError("the function '%s' is not a proper command function (did you forget the decorator?)" % func.__name__)

    def get(self, privileges):
        result = self.commands_per_priv[None]  # always include the cmds for None
        for priv in privileges:
            if priv in self.commands_per_priv:
                result.update(self.commands_per_priv[priv])
        return result

    def adjust_available_commands(self, story_config):
        # disable commands flagged with the given game_mode
        # disable soul verbs flagged with override
        # mark non-soul commands
        for cmds in self.commands_per_priv.values():
            for cmd, func in list(cmds.items()):
                disabled_mode = getattr(func, "disabled_in_mode", None)
                if story_config.server_mode == disabled_mode:
                    del cmds[cmd]
                elif getattr(func, "overrides_soul", False):
                    del soul.VERBS[cmd]
                if getattr(func, "no_soul_parse", False):
                    self.no_soul_parsing.add(cmd)


def version_tuple(v_str):
    return tuple(int(n) for n in v_str.split('.'))


class Driver(object):
    """
    The Mud 'driver'.
    Reads story file and config, initializes game state.
    Handles main game loop, player connections, and loading/saving of game state.
    """
    directions = {"north", "east", "south", "west", "northeast", "northwest", "southeast", "southwest", "up", "down"}

    def __init__(self):
        self.heartbeat_objects = set()
        self.unbound_exits = []
        self.deferreds = []  # heapq
        self.deferreds_lock = threading.Lock()
        self.notification_queue = util.queue.Queue()
        server_started = datetime.datetime.now()
        self.server_started = server_started.replace(microsecond=0)
        self.player = None
        self.config = None
        self.commands = Commands()
        self.server_loop_durations = collections.deque(maxlen=10)
        self.register_in_mud_context()
        cmds.register_all(self.commands)

    def register_in_mud_context(self):
        # Register the driver and some other stuff in the global thread context.
        # These are unique per thread (=per player).
        mud_context.driver = self
        mud_context.config = self.config
        mud_context.player = self.player

    def bind_exits(self):
        # convert textual exit strings to actual exit object bindings
        for exit in self.unbound_exits:
            exit._bind_target(self.zones)
        del self.unbound_exits

    def start(self, args):
        """Parse the command line arguments and start the driver accordingly."""
        parser = argparse.ArgumentParser(description="""
            Tale framework %s game driver. Use this to launch a game and specify some settings.
            Sometimes the game will provide its own startup script that invokes this automatically.
            If it doesn't, refer to the options to see how to launch it manually instead.
            """ % tale_version_str)
        parser.add_argument('-g', '--game', type=str, help='path to the game directory', required=True)
        parser.add_argument('-d', '--delay', type=int, help='screen output delay for IF mode (milliseconds, 0=no delay)', default=DEFAULT_SCREEN_DELAY)
        parser.add_argument('-m', '--mode', type=str, help='game mode, default=if', default="if", choices=["if", "mud"])
        parser.add_argument('-i', '--gui', help='gui interface', action='store_true')
        args = parser.parse_args(args)
        try:
            self._start(args)
        except Exception:
            if args.gui:
                import traceback
                tb = traceback.format_exc()
                from .io import tkinter_io
                tkinter_io.show_error_dialog("Exception during start", "An error occurred while starting up the game:\n\n" + tb)
            raise

    def _start(self, args):
        if 0 <= args.delay <= 100:
            output_line_delay = args.delay
        else:
            raise ValueError("invalid delay, valid range is 0-100")

        path_for_driver = os.path.abspath(os.path.dirname(inspect.getfile(Driver)))
        if path_for_driver == os.path.abspath("tale"):
            # The tale library is being loaded from the current directory, this is not supported.
            print("Tale is being asked to run directly from the distribution directory, this is not supported.")
            print("Install Tale properly, and/or use the start script from the story directory instead.")
            return
        # cd into the game directory, add it to the search path, and load its config and zones
        os.chdir(args.game)
        sys.path.insert(0, '.')
        story = __import__("story", level=0)
        self.story = story.Story()
        if args.mode not in self.story.config["supported_modes"]:
            raise ValueError("driver mode '%s' not supported by this story" % args.mode)
        self.config = util.ReadonlyAttributes(self.story.config)
        self.config.server_mode = args.mode   # if/mud driver mode ('if' = single player interactive fiction, 'mud'=multiplayer)
        self.register_in_mud_context()
        try:
            story_cmds = __import__("cmds", level=0)
        except (ImportError, ValueError):
            pass
        else:
            story_cmds.register_all(self.commands)
        self.commands.adjust_available_commands(self.config)
        tale_version = version_tuple(tale_version_str)
        tale_version_required = version_tuple(self.config.requires_tale)
        if tale_version < tale_version_required:
            raise RuntimeError("The game requires tale " + self.config.requires_tale + " but " + tale_version_str + " is installed.")
        self.game_clock = util.GameDateTime(self.config.epoch or self.server_started, self.config.gametime_to_realtime)
        self.moneyfmt = util.MoneyFormatter(self.config.money_type) if self.config.money_type else None
        self.vfs = vfs.VirtualFileSystem(story)
        self.story.init(self)
        import zones
        self.zones = zones
        self.config.startlocation_player = self.lookup_location(self.config.startlocation_player)
        self.config.startlocation_wizard = self.lookup_location(self.config.startlocation_wizard)
        if self.config.server_tick_method == "command":
            # If the server tick is synchronized with player commands, this factor needs to be 1,
            # because at every command entered the game time simply advances 1 x server_tick_time.
            self.config.gametime_to_realtime = 1
        assert self.config.server_tick_time > 0
        assert self.config.max_wait_hours >= 0
        self.config.lock()   # make the config read-only
        self.game_clock = util.GameDateTime(self.config.epoch or self.server_started, self.config.gametime_to_realtime)
        self.bind_exits()
        # story has been initialised, create and connect a player
        self.player = player.Player("<connecting>", "n", "elemental", "This player is still connecting.")
        if args.gui:
            from .io.tkinter_io import TkinterIo as IoAdapter
            io = IoAdapter(self.config)
        else:
            from .io.console_io import ConsoleIo as IoAdapter
            io = IoAdapter(self.config)
        io.output_line_delay = output_line_delay
        io.clear_screen()
        io.install_tab_completion(TabCompleter(self, self.player))
        self.player.io = io
        # the driver mainloop is running in a background thread, the io-loop/gui-event-loop runs in the main thread
        driver_thread = threading.Thread(name="driver", target=self.startup_main_loop)
        driver_thread.daemon = True
        driver_thread.start()
        io.mainloop(self.player)

    def startup_main_loop(self):
        # continues the startup process and kick off the driver's main loop
        self.register_in_mud_context()    # re-register because we may be running in a new background thread
        self._stop_mainloop = False
        try:
            self.print_game_intro(self.player)
            self.create_player(self.player)
            self.show_motd(self.player)
            self.player.look(short=False)
            self.player.write_output()
            while not self._stop_mainloop:
                try:
                    self.main_loop()
                    break
                except KeyboardInterrupt:
                    self.player.io.break_pressed()
                    continue
        except:
            self.player.io.critical_error()
            self._stop_mainloop = True
            raise

    def print_game_intro(self, player):
        # prints the intro screen of the game
        io = player.io
        try:
            banner = self.vfs.load_text("messages/banner.txt")
            # print game banner as supplied by the game
            io.output("\n<monospaced><bright>" + banner + "</></monospaced>\n")
        except IOError:
            # no banner provided by the game, print default game header
            io.output("")
            io.output("")
            io.output("<monospaced><bright>")
            msg = "'%s'" % self.config.name
            io.output(msg.center(DEFAULT_SCREEN_WIDTH))
            msg = "v%s" % self.config.version
            io.output(msg.center(DEFAULT_SCREEN_WIDTH))
            io.output("")
            msg = "written by %s" % self.config.author
            io.output(msg.center(DEFAULT_SCREEN_WIDTH))
            if self.config.author_address:
                io.output(self.config.author_address.center(DEFAULT_SCREEN_WIDTH))
            io.output("</></monospaced>")
            io.output("")

    def create_player(self, player):
        # lets the user create a new player, load a saved game, or initialize it directly from the story's configuration
        if self.config.server_mode == "mud" or not self.config.savegames_enabled:
            load_saved_game = False
        else:
            player.tell("\n")
            load_saved_game = util.input_confirm("Do you want to load a saved game ('<bright>n</>' will start a new game)?", player)
        player.tell("\n")
        if load_saved_game:
            io = player.io  # save the I/O
            player = self.load_saved_game()
            player.io = io  # reset the I/O
            player.tell("\n")
            if self.config.server_mode == "if":
                self.story.welcome_savegame(player)
            else:
                player.tell("Welcome back to %s, %s." % (self.config.name, player.title))
            player.tell("\n")
        else:
            if self.config.server_mode == "if" and self.config.player_name:
                # interactive fiction mode, create the player from the game's config
                player.init_names(self.config.player_name, None, None, None)
                player.init_race(self.config.player_race, self.config.player_gender)
            elif self.config.server_mode == "mud" or not self.config.player_name:
                # mud mode, or if mode without player config: create a character with the builder
                from .charbuilder import CharacterBuilder
                name_info = CharacterBuilder(player).build()
                name_info.apply_to(player)

            player.io.do_styles = player.screen_styles_enabled
            player.io.do_smartquotes = player.smartquotes_enabled
            player.tell("\n")
            # move the player to the starting location
            if "wizard" in player.privileges:
                player.move(self.config.startlocation_wizard)
            else:
                player.move(self.config.startlocation_player)
            player.tell("\n")
            if self.config.server_mode == "if":
                self.story.welcome(player)
            else:
                player.tell("Welcome to %s, %s." % (self.config.name, player.title), end=True)
            player.tell("\n")
        self.story.init_player(player)

    def show_motd(self, player):
        """Prints the Message-Of-The-Day file, if present. Does nothing in IF mode."""
        if self.config.server_mode != "if":
            motd, mtime = util.get_motd(self.vfs)
            if motd:
                player.tell("<bright>Message-of-the-day, last modified on %s:</>" % mtime, end=True)
                player.tell("\n")
                player.tell(motd, end=True, format=True)  # for now, the motd is displayed *with* formatting
                player.tell("\n")
                player.tell("\n")

    def stop_driver(self):
        """stop the driver mainloop"""
        self._stop_mainloop = True
        self.player.write_output()  # flush pending output at server shutdown.
        ctx = util.Context(driver=self)
        ctx.lock()
        self.player.destroy(ctx)

    def main_loop(self):
        """
        The game loop.
        Until the game is exited, it processes player input, and prints the resulting output.
        """
        has_input = True
        last_loop_time = last_server_tick = time.time()
        while not self._stop_mainloop:
            mud_context.player = self.player   # @todo hack... is always the same single player for now
            self.player.write_output()
            if self.player.story_complete and self.config.server_mode == "if":
                # congratulations ;-)
                self.story_complete_output()
                self.stop_driver()
                break
            if self.config.server_tick_method == "timer" and time.time() - last_server_tick >= self.config.server_tick_time:
                # NOTE: if the sleep time ever gets down to zero or below zero, the server load is too high
                last_server_tick = time.time()
                self.server_tick()
                loop_duration_with_server_tick = time.time() - last_loop_time
                self.server_loop_durations.append(loop_duration_with_server_tick)
            else:
                loop_duration = time.time() - last_loop_time

            if has_input:
                # print the input prompt
                self.player.io.write_input_prompt()

            # check for player input:
            if self.config.server_tick_method == "timer":
                has_input = self.player.input_is_available.wait(max(0.01, self.config.server_tick_time - loop_duration))
            elif self.config.server_tick_method == "command":
                self.player.input_is_available.wait()   # blocking wait until playered entered something
                has_input = True
                before = time.time()
                self.server_tick()
                self.server_loop_durations.append(time.time() - before)

            last_loop_time = time.time()
            if has_input:
                try:
                    for cmd in self.player.get_pending_input():   # @todo hmm, all at once or limit player to 1 cmd/tick?
                        if not cmd:
                            continue
                        try:
                            self.player.tell("\n")
                            self.process_player_input(cmd)
                            self.player.remember_parsed()
                        except soul.UnknownVerbException as x:
                            if x.verb in self.directions:
                                self.player.tell("You can't go in that direction.")
                            else:
                                self.player.tell("The verb '%s' is unrecognized." % x.verb)
                        except errors.ActionRefused as x:
                            self.player.remember_parsed()
                            self.player.tell(str(x))
                        except errors.ParseError as x:
                            self.player.tell(str(x))
                except KeyboardInterrupt:
                    self.player.io.break_pressed()
                    continue
                except EOFError:
                    continue
                except errors.StoryCompleted as ex:
                    if self.config.server_mode == "if":
                        # congratulations ;-)
                        self.player.story_completed()
                    else:
                        pass   # in mud mode, the game can't be 'completed' in this way
                except errors.SessionExit:
                    if self.config.server_mode == "if":
                        self.story.goodbye(self.player)
                    else:
                        self.player.tell("Goodbye, %s. Please come back again soon." % self.player.title, end=True)
                    self.stop_driver()
                    break
                except Exception:
                    import traceback
                    txt = "* internal error:\n" + traceback.format_exc()
                    self.player.tell(txt, format=False)
            # call any queued event notification handlers
            while True:
                try:
                    deferred = self.notification_queue.get_nowait()
                    deferred()
                except util.queue.Empty:
                    break

    def server_tick(self):
        """
        Do everything that the server needs to do every tick.
        1) game clock
        2) heartbeats
        3) deferreds
        4) write buffered output to the screen.
        """
        self.game_clock.add_realtime(datetime.timedelta(seconds=self.config.server_tick_time))
        ctx = {"driver": self, "clock": self.game_clock}
        for object in self.heartbeat_objects:
            object.heartbeat(ctx)
        if self.deferreds:
            with self.deferreds_lock:
                deferred = self.deferreds[0]
                if deferred.due <= self.game_clock.clock:
                    deferred = heapq.heappop(self.deferreds)
                else:
                    deferred = None
            if deferred:
                deferred(driver=self)
        self.player.write_output()

    def story_complete_output(self):
        self.player.tell("\n")
        self.story.completion(self.player)
        self.player.tell("\n")
        self.player.input("\nPress enter to continue. ")
        self.player.tell("\n")

    def process_player_input(self, cmd):
        if not cmd:
            return
        if cmd and cmd[0] in cmds.abbreviations and not cmd[0].isalpha():
            # insert a space to separate the first char such as ' or ?
            cmd = cmd[0] + " " + cmd[1:]
        # check for an abbreviation, replace it with the full verb if present
        _verb, _sep, _rest = cmd.partition(" ")
        if _verb in cmds.abbreviations:
            _verb = cmds.abbreviations[_verb]
            cmd = "".join([_verb, _sep, _rest])

        # We pass in all 'external verbs' (non-soul verbs) so it will do the
        # parsing for us even if it's a verb the soul doesn't recognise by itself.
        command_verbs = self.commands.get(self.player.privileges)
        custom_verbs = set(self.player.location.verbs)
        try:
            if _verb in self.commands.no_soul_parsing:
                # don't use the soul to parse it further
                raise soul.NonSoulVerb(soul.ParseResult(_verb, unparsed=_rest.strip()))
            else:
                # Parse the command by using the soul.
                all_verbs = set(command_verbs) | custom_verbs
                parsed = self.player.parse(cmd, external_verbs=all_verbs)
            # If parsing went without errors, it's a soul verb, handle it as a socialize action
            self.do_socialize(parsed)
        except soul.NonSoulVerb as x:
            parsed = x.parsed
            if parsed.qualifier:
                # for now, qualifiers are only supported on soul-verbs (emotes).
                raise errors.ParseError("That action doesn't support qualifiers.")
            # Execute non-soul verb. First try directions, then the rest.
            try:
                # Check if the verb is a custom verb and try to handle that.
                # If it remains unhandled, check if it is a normal verb, and handle that.
                # If it's not a normal verb, abort with "please be more specific".
                parse_error = "That doesn't make much sense."
                handled = False
                if parsed.verb in custom_verbs:
                    handled = self.player.location.handle_verb(parsed, self.player)
                    if handled:
                        self.after_player_action(self.player.location.notify_action, parsed, self.player)
                    else:
                        parse_error = "Please be more specific."
                if not handled:
                    if parsed.verb in self.player.location.exits:
                        self.go_through_exit(self.player, parsed.verb)
                    elif parsed.verb in command_verbs:
                        func = command_verbs[parsed.verb]
                        ctx = util.Context(driver=self, config=self.config, clock=self.game_clock)
                        ctx.lock()
                        func(self.player, parsed, ctx)
                        if func.enable_notify_action:
                            self.after_player_action(self.player.location.notify_action, parsed, self.player)
                    else:
                        raise errors.ParseError(parse_error)
            except errors.RetrySoulVerb as x:
                # cmd decided it can't deal with the parsed stuff and that it needs to be retried as soul emote.
                self.player.validate_socialize_targets(parsed)
                self.do_socialize(parsed)
            except errors.RetryParse as x:
                return self.process_player_input(x.command)   # try again but with new command string

    def get_current_verbs(self):
        """return a dict of all currently recognised verbs, and their help text"""
        normal_verbs = self.commands.get(self.player.privileges)
        verbs = {v: (f.__doc__ or "") for v, f in normal_verbs.items()}
        verbs.update(self.player.location.verbs)  # add the custom verbs
        return verbs

    def go_through_exit(self, player, direction):
        exit = player.location.exits[direction]
        exit.allow_passage(player)
        player.move(exit.target)
        player.look()

    def lookup_location(self, location_name):
        location = self.zones
        modulename = "zones"
        for name in location_name.split('.'):
            if hasattr(location, name):
                location = getattr(location, name)
            else:
                modulename = modulename + "." + name
                __import__(modulename)
                location = getattr(location, name)
        return location

    def do_socialize(self, parsed):
        who, player_message, room_message, target_message = self.player.socialize_parsed(parsed)
        self.player.tell(player_message)
        self.player.location.tell(room_message, self.player, who, target_message)
        self.after_player_action(self.player.location.notify_action, parsed, self.player)
        if parsed.verb in soul.AGGRESSIVE_VERBS:
            # usually monsters immediately attack,
            # other npcs may choose to attack or to ignore it
            # We need to check the qualifier, it might void the actual action :)
            if parsed.qualifier not in soul.NEGATING_QUALIFIERS:
                for living in who:
                    if getattr(living, "aggressive", False):
                        living.start_attack(self.player)

    def search_player(self, name):
        """Look through all the logged in players for one with the given name"""
        if self.player.name == name:
            return self.player
        return None

    def all_players(self):
        """return all players"""
        return [self.player]

    def do_wait(self, duration):
        # let time pass, duration is in game time (not real time).
        # We do let the game tick for the correct number of times,
        # however @todo: be able to detect if something happened during the wait
        if self.config.gametime_to_realtime == 0:
            # game is running with a 'frozen' clock
            # simply advance the clock, and perform a single server_tick
            self.game_clock.add_gametime(duration)
            self.server_tick()
            return True, None      # uneventful
        num_ticks = int(duration.seconds / self.config.gametime_to_realtime / self.config.server_tick_time)
        if num_ticks < 1:
            return False, "It's no use waiting such a short while."
        for _ in range(num_ticks):
            self.server_tick()
        return True, None     # wait was uneventful. (@todo return False if something happened)

    def do_save(self, player):
        if not self.config.savegames_enabled:
            return
        state = {
            "version": self.config.version,
            "player": self.player,
            "deferreds": self.deferreds,
            "clock": self.game_clock,
            "heartbeats": self.heartbeat_objects,
            "config": self.config
        }
        savedata = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
        self.vfs.write_to_storage(self.config.name.lower() + ".savegame", savedata)
        player.tell("Game saved.")
        if self.config.display_gametime:
            player.tell("Game time:", self.game_clock)
        player.tell("\n")

    def load_saved_game(self):
        try:
            savegame = self.vfs.load_from_storage(self.config.name.lower() + ".savegame")
            state = pickle.loads(savegame)
            del savegame
        except (IOError, pickle.PickleError) as x:
            print("There was a problem loading the saved game data:")
            print(type(x).__name__, x)
            raise SystemExit(10)
        else:
            if state["version"] != self.config.version:
                print("This saved game data was from a different version of the game and cannot be used.")
                print("(Current game version: %s  Saved game data version: %s)" % (self.config.version, state["version"]))
                raise SystemExit(10)
            self.player = state["player"]
            self.deferreds = state["deferreds"]
            self.game_clock = state["clock"]
            self.heartbeat_objects = state["heartbeats"]
            self.config = state["config"]
            self.player.tell("Game loaded.")
            if self.config.display_gametime:
                self.player.tell("Game time:", self.game_clock)
            self.player.tell("\n")
            return self.player

    def register_heartbeat(self, mudobj):
        self.heartbeat_objects.add(mudobj)

    def unregister_heartbeat(self, mudobj):
        self.heartbeat_objects.discard(mudobj)

    def register_exit(self, exit):
        if not exit.bound:
            self.unbound_exits.append(exit)

    def defer(self, due, owner, callable, *vargs, **kwargs):
        """
        Register a deferred callable (optionally with arguments).
        The owner object, the vargs and the kwargs all must be serializable.
        Note that the due time is datetime.datetime *in game time*
        (not real time!) when the deferred should trigger.
        Due can also be a number, meaning the number of real-time seconds after the current time.
        Also note that the deferred *always* gets a kwarg 'driver' set to the driver object
        (this makes it easy to register a new deferred on the driver without the need to
        access the global driver object)
        """
        if isinstance(due, datetime.datetime):
            assert due >= self.game_clock.clock
        else:
            due = float(due)
            assert due >= 0.0
            due = self.game_clock.plus_realtime(datetime.timedelta(seconds=due))
        # to be able to serialize this, we don't store the actual callable object.
        # instead we store its name.
        if not isinstance(callable, util.basestring_type):
            callable = callable.__name__
        # check that callable is in fact a function on the owner object
        func = getattr(owner, callable, None)
        if func:
            assert inspect.ismethod(func) or inspect.isfunction(func)
            deferred = Deferred(due, owner, callable, vargs, kwargs)
            # we skip the pickle check because it is extremely inefficient.....:
            # pickle.dumps(deferred, pickle.HIGHEST_PROTOCOL)  # make sure the data can be serialized
            with self.deferreds_lock:
                heapq.heappush(self.deferreds, deferred)
            return
        raise ValueError("unknown callable on owner object")

    def after_player_action(self, callable, *vargs, **kwargs):
        """
        Register a deferred callable (optionally with arguments) in the queue
        of events that will be executed immediately *after* the player's own actions
        have been completed.
        """
        deferred = Deferred(None, None, callable, vargs, kwargs)
        self.notification_queue.put(deferred)

    def remove_deferreds(self, owner):
        with self.deferreds_lock:
            self.deferreds = [d for d in self.deferreds if d.owner is not owner]
            heapq.heapify(self.deferreds)


if __name__ == "__main__":
    driver = Driver()
    driver.start(sys.argv[1:])
