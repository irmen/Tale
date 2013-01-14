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
import threading
import heapq
import inspect
import argparse
import pickle
from . import globalcontext
from . import errors
from . import util
from . import soul
from . import cmds
from . import player
from . import __version__ as tale_version_str
from .io import vfs


@total_ordering
class Deferred(object):
    __slots__ = ("due", "owner", "callable", "vargs", "kwargs")

    def __init__(self, due, owner, callable, vargs, kwargs):
        self.due = due   # in game time
        self.owner = owner
        self.callable = callable
        self.vargs = vargs
        self.kwargs = kwargs

    def __eq__(self, other):
        return self.due == other.due

    def __lt__(self, other):
        return self.due < other.due   # deferreds must be sortable

    def due_secs(self, game_clock, realtime=False):
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
        for cmds in self.commands_per_priv.values():
            for cmd, func in list(cmds.items()):
                disabled_mode = getattr(func, "disabled_in_mode", None)
                if story_config.server_mode == disabled_mode:
                    del cmds[cmd]
                elif getattr(func, "overrides_soul", False):
                    del soul.VERBS[cmd]


def version_tuple(v_str):
    return tuple(int(n) for n in v_str.split('.'))


class Driver(object):
    directions = {"north", "east", "south", "west", "northeast", "northwest", "southeast", "southwest", "up", "down"}

    def __init__(self):
        self.heartbeat_objects = set()
        self.state = {}  # global game state variables
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
        self.register_global_context()
        cmds.register_all(self.commands)
        monkeypatch_blinker()

    def register_global_context(self):
        """register the driver and some other stuff in the global thread context"""
        ctx = globalcontext.mud_context
        ctx.driver = self
        ctx.state = self.state
        ctx.config = self.config
        ctx.player = self.player

    def bind_exits(self):
        for exit in self.unbound_exits:
            exit._bind_target(self.zones)
        del self.unbound_exits

    def start(self, args):
        # parse args
        parser = argparse.ArgumentParser(description="""
            Tale framework %s game driver. Use this to launch a game and specify some settings.
            Sometimes the game will provide its own startup script that invokes this automatically.
            If it doesn't, refer to the options to see how to launch it manually instead.
            """ % tale_version_str)
        parser.add_argument('-g', '--game', type=str, help='path to the game directory', required=True)
        parser.add_argument('-d', '--delay', type=int, help='screen output delay for IF mode (milliseconds, 0=no delay)', default=player.DEFAULT_SCREEN_DELAY)
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
        self.config = util.AttrDict(self.story.config)
        self.config.server_mode = args.mode   # if/mud driver mode ('if' = single player interactive fiction, 'mud'=multiplayer)
        enable_readline(self.config)
        self.register_global_context()
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
        self.game_clock = util.GameDateTime(self.config.epoch or self.server_started, self.config.gametime_to_realtime)
        self.bind_exits()
        # story has been initialised, create and connect a player
        self.async_player_input = None
        self.player = player.Player("<connecting>", "n", "elemental", "This player is still connecting.")
        if args.gui:
            from .io.tkinter_io import TkinterIo as IoAdapter
        else:
            from .io.console_io import ConsoleIo as IoAdapter
        self.player.io = IoAdapter(self.config)
        self.player.io.output_line_delay = output_line_delay
        self.player.io.clear_screen()
        driver_thread, io_mainloop = self.player.io.mainloop_threads(self.startup_main_loop)
        self._io_thread_may_start = threading.Event()
        if driver_thread is None:
            assert io_mainloop is None
            # the driver mainloop is running in the main thread
            self.startup_main_loop()
        else:
            # the driver mainloop is running in a background thread, the io-loop should run in the main thread
            driver_thread.start()
            self._io_thread_may_start.wait()
            del self._io_thread_may_start
            time.sleep(0.1)
            while not self._stop_mainloop:
                try:
                    io_mainloop()
                    break
                except KeyboardInterrupt:
                    self.player.io.break_pressed(self.player)
                    continue
            driver_thread.join()

    def startup_main_loop(self):
        # continues the startup process and kick of the driver's main loop
        self.register_global_context()    # re-register because we may be running in a new background thread
        self._io_thread_may_start.set()
        self._stop_mainloop = False
        try:
            self.start_print_game_intro()
            self.start_create_player()
            self.start_show_motd()
            self.player.look(short=False)
            self.player.write_output()
            self.start_player_input()
            while not self._stop_mainloop:
                try:
                    self.main_loop()
                    break
                except KeyboardInterrupt:
                    self.player.io.break_pressed(self.player)
                    continue
        except:
            self.player.io.critical_error()
            self._stop_mainloop = True
            raise

    def start_print_game_intro(self):
        io = self.player.io
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
            io.output(msg.center(player.DEFAULT_SCREEN_WIDTH))
            msg = "v%s" % self.config.version
            io.output(msg.center(player.DEFAULT_SCREEN_WIDTH))
            io.output("")
            msg = "written by %s" % self.config.author
            io.output(msg.center(player.DEFAULT_SCREEN_WIDTH))
            if self.config.author_address:
                io.output(self.config.author_address.center(player.DEFAULT_SCREEN_WIDTH))
            io.output("</></monospaced>")
            io.output("")

    def start_create_player(self):
        io = self.player.io
        if self.config.server_mode == "mud" or not self.config.savegames_enabled:
            load_saved_game = False
        else:
            io.output("")
            load_saved_game = util.input_confirm("Do you want to load a saved game ('<bright>n</>' will start a new game)?", self.player)
        io.output("")
        if load_saved_game:
            self.load_saved_game()
            self.player.io = io  # set the I/O adapter for this player
            del io
            self.player.tell("\n")
            if self.config.server_mode == "if":
                self.story.welcome_savegame(self.player)
            else:
                self.player.tell("Welcome back to %s, %s." % (self.config.name, self.player.title))
            self.player.tell("\n")
        else:
            if self.config.server_mode == "if" and self.config.player_name:
                # interactive fiction mode, create the player from the game's config
                self.player.init_names(self.config.player_name, None, None, None)
                self.player.init_race(self.config.player_race, self.config.player_gender)
            elif self.config.server_mode == "mud" or not self.config.player_name:
                # mud mode, or if mode without player config: create a character with the builder
                from .charbuilder import CharacterBuilder
                name_info = CharacterBuilder(self.player).build()
                name_info.apply_to(self.player)

            self.player.io = io  # set the I/O adapter for this player
            self.player.io.do_styles = self.player.screen_styles_enabled
            self.player.io.do_smartquotes = self.player.smartquotes_enabled
            del io
            self.player.tell("\n")
            # move the player to the starting location
            if "wizard" in self.player.privileges:
                self.player.move(self.config.startlocation_wizard)
            else:
                self.player.move(self.config.startlocation_player)
            self.player.tell("\n")
            if self.config.server_mode == "if":
                self.story.welcome(self.player)
            else:
                self.player.tell("Welcome to %s, %s." % (self.config.name, self.player.title), end=True)
            self.player.tell("\n")
        self.story.init_player(self.player)

    def start_show_motd(self):
        if self.config.server_mode != "if":
            motd, mtime = util.get_motd(self.vfs)
            if motd:
                self.player.tell("<bright>Message-of-the-day, last modified on %s:</>" % mtime, end=True)
                self.player.tell("\n")
                self.player.tell(motd, end=True, format=True)  # for now, the motd is displayed *with* formatting
                self.player.tell("\n")
                self.player.tell("\n")

    def start_player_input(self):
        """(re)start the async player input processing task"""
        if self.config.server_tick_method == "timer":
            self.async_player_input = self.player.io.get_async_input(self.player)
        elif self.config.server_tick_method == "command":
            self.async_player_input = None  # player input is done in the same thread as the game loop
        else:
            raise ValueError("invalid server_tick_method: " + self.config.server_tick_method)

    def stop_driver(self):
        """stop the async player input processing task, and the driver mainloop"""
        self._stop_mainloop = True
        if self.async_player_input is not None:
            self.async_player_input.stop()

    def main_loop(self):
        last_loop_time = last_server_tick = time.time()
        while not self._stop_mainloop:
            globalcontext.mud_context.player = self.player   # @todo hack... is always the same single player for now
            self.player.write_output()
            if self.player.story_complete and self.config.server_mode == "if":
                # congratulations ;-)
                self.story_complete_output(self.player.story_complete_callback)
                self.stop_driver()
                self.player.io.destroy()
                break
            if self.async_player_input:
                self.async_player_input.enable()  # enable player input
            if self.config.server_tick_method == "timer" and time.time() - last_server_tick >= self.config.server_tick_time:
                # NOTE: if the sleep time ever gets down to zero or below zero, the server load is too high
                last_server_tick = time.time()
                self.server_tick()
                loop_duration_with_server_tick = time.time() - last_loop_time
                self.server_loop_durations.append(loop_duration_with_server_tick)
            else:
                loop_duration = time.time() - last_loop_time

            if self.config.server_tick_method == "timer":
                has_input = self.player.input_is_available.wait(max(0.01, self.config.server_tick_time - loop_duration))
            elif self.config.server_tick_method == "command":
                self.player.io.input_line(self.player)
                has_input = self.player.input_is_available.is_set()
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
                    self.player.io.break_pressed(self.player)
                    continue
                except EOFError:
                    continue
                except errors.StoryCompleted as ex:
                    if self.config.server_mode == "if":
                        # congratulations ;-)
                        self.player.story_completed(ex.callback)
                    else:
                        pass   # in mud mode, the game can't be completed
                except errors.SessionExit:
                    if self.config.server_mode == "if":
                        self.story.goodbye(self.player)
                    else:
                        self.player.tell("Goodbye, %s. Please come back again soon." % self.player.title, end=True)
                    self.stop_driver()
                    self.player.io.destroy()
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
        self.player.write_output()  # flush pending output at server shutdown.
        ctx = util.Context(driver=self)
        self.player.destroy(ctx)

    def server_tick(self):
        # Do everything that the server needs to do every tick.
        # 1) game clock
        # 2) heartbeats
        # 3) deferreds
        # 4) write buffered output to the screen.
        self.game_clock.add_realtime(datetime.timedelta(seconds=self.config.server_tick_time))
        ctx = {"driver": self, "clock": self.game_clock, "state": self.state}
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

    def story_complete_output(self, callback):
        if callback:
            callback(self.player, self.config, self)
        else:
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

        # Parse the command by using the soul.
        # We pass in all 'external verbs' (non-soul verbs) so it will do the
        # parsing for us even if it's a verb the soul doesn't recognise by itself.
        command_verbs = self.commands.get(self.player.privileges)
        custom_verbs = set(self.player.location.verbs)
        all_verbs = set(command_verbs) | custom_verbs
        try:
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
                        ctx = util.Context(driver=self, config=self.config, clock=self.game_clock, state=self.state)
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
            "gamestate": self.state,
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
            self.state = state["gamestate"]
            self.deferreds = state["deferreds"]
            self.game_clock = state["clock"]
            self.heartbeat_objects = state["heartbeats"]
            self.config = state["config"]
            self.player.tell("Game loaded.")
            if self.config.display_gametime:
                self.player.tell("Game time:", self.game_clock)
            self.player.tell("\n")

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


def enable_readline(config):
    # enable readline except in certain situation on Pypy,
    # it causes a crash when using the threaded input mode on Pypy (1.9).
    if hasattr(sys, "pypy_version_info") and config.server_tick_method == "timer":
        return
    try:
        import readline
    except ImportError:
        return
    readline.parse_and_bind("tab: complete")


def monkeypatch_blinker():
    """
    On Pypy: monkeypatch blinker to use a namespace based on dict instead of weakvaluedict
    See blinker issue: https://bitbucket.org/jek/blinker/issue/7
    """
    if hasattr(sys, "pypy_version_info"):
        import blinker
        if getattr(blinker.signal.im_class, "_tale_monkeypatch", False):
            return  # already patched

        class MonkeyPatchedNamespace(dict, blinker.Namespace):
            _tale_monkeypatch = True

        blinker.signal = MonkeyPatchedNamespace().signal


if __name__ == "__main__":
    driver = Driver()
    driver.start(sys.argv[1:])
