"""
Mud driver (server).

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division
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
from . import globals
from . import errors
from . import util
from . import soul
from . import cmds
from . import resource
from . import player
from . import __version__ as tale_version_str
try:
    import readline
except ImportError:
    pass
else:
    history = os.path.expanduser("~/.tale_history")
    readline.parse_and_bind("tab: complete")
    try:
        readline.read_history_file(history)
    except IOError:
        pass
    import atexit

    def save_history(historyfile):
        readline.write_history_file(historyfile)

    atexit.register(save_history, history)

input = util.input


class StoryConfig(dict):
    """A dict-like object that supports accessing its members as attributes."""
    def __init__(self, *vargs, **kwargs):
        if vargs:
            assert len(vargs) == 1
            assert not kwargs
            source = vargs[0]
            assert isinstance(source, dict)
        else:
            source = kwargs
        dict.__init__(self, source)
        self.__dict__.update(source)
    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.__dict__[key] = value


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


class Commands(object):
    def __init__(self):
        self.commands_per_priv = {None: {}}

    def add(self, verb, func, privilege):
        for commands in self.commands_per_priv.values():
            if verb in commands:
                raise ValueError("command defined more than once: " + verb)
        self.commands_per_priv.setdefault(privilege, {})[verb] = func

    def get(self, privileges):
        result = self.commands_per_priv[None]  # always include the cmds for None
        for priv in privileges:
            if priv in self.commands_per_priv:
                result.update(self.commands_per_priv[priv])
        return result

    def adjust_available_commands(self, story_config, game_mode):
        if not story_config.max_score:
            # remove the 'score' command because scoring has been disabled
            for cmds in self.commands_per_priv.values():
                if "score" in cmds:
                    del cmds["score"]
        if game_mode == "if":
            # disable commands flagged with 'disabled_for_IF'
            for cmds in self.commands_per_priv.values():
                for cmd, func in list(cmds.items()):
                    if getattr(func, "disabled_for_IF", False):
                        del cmds[cmd]


CTRL_C_MESSAGE = "\n* break: Use <quit> if you want to quit."


def version_tuple(v_str):
    return tuple(int(n) for n in v_str.split('.'))


class Driver(object):
    directions = {"north", "east", "south", "west", "northeast", "northwest", "southeast", "southwest", "up", "down"}

    def __init__(self):
        self.heartbeat_objects = set()
        self.state = {}  # global game state variables
        self.unbound_exits = []
        self.deferreds = []  # heapq
        server_started = datetime.datetime.now()
        self.server_started = server_started.replace(microsecond=0)
        self.player = None
        self.mode = "if"  # if/mud driver mode
        self.commands = Commands()
        self.output_line_delay = 60   # milliseconds
        self.server_loop_durations = collections.deque(maxlen=10)
        globals.mud_context.driver = self
        globals.mud_context.state = self.state
        globals.mud_context.config = None
        cmds.register_all(self.commands)

    def bind_exits(self):
        for exit in self.unbound_exits:
            exit.bind(self.zones)
        self.unbound_exits = []

    def start(self, args):
        # parse args
        parser = argparse.ArgumentParser(description='Parse driver arguments.')
        parser.add_argument('-g', '--game', type=str, help='path to the game directory', required=True)
        parser.add_argument('-t', '--transcript', type=str, help='transcript filename')
        parser.add_argument('-d', '--delay', type=int, help='screen output delay for IF mode (milliseconds, 0=no delay)', default=60)
        parser.add_argument('-m', '--mode', type=str, help='game mode, default=if', default="if", choices=["if", "mud"])
        args = parser.parse_args()
        self.mode = args.mode
        if 0 <= args.delay <= 100:
            self.output_line_delay = args.delay
        else:
            raise ValueError("invalid delay, valid range is 0-100")

        # cd into the game directory and load its config and zones
        os.chdir(args.game)
        import story
        self.story = story.Story()
        self.config = StoryConfig(self.story.config)
        globals.mud_context.config = self.config
        self.commands.adjust_available_commands(self.config, self.mode)
        tale_version = version_tuple(tale_version_str)
        tale_version_required = version_tuple(self.config.requires_tale)
        if tale_version < tale_version_required:
            raise RuntimeError("The game requires tale " + self.config.requires_tale + " but " + tale_version_str + " is installed.")
        self.game_clock = util.GameDateTime(self.config.epoch or self.server_started, self.config.gametime_to_realtime)
        self.game_resource = resource.ResourceLoader(story)
        self.story.init(self)
        import zones
        self.zones = zones
        self.config.startlocation_player = self.lookup_location(self.config.startlocation_player)
        self.config.startlocation_wizard = self.lookup_location(self.config.startlocation_wizard)
        if self.config.server_tick_method == "command":
            # If the server tick is synchronized with player commands, this factor needs to be 1,
            # because at every command entered the game time simply advances 1 x server_tick_time.
            self.config.gametime_to_realtime = 1
        self.game_clock = util.GameDateTime(self.config.epoch or self.server_started, self.config.gametime_to_realtime)
        self.bind_exits()

        try:
            banner = self.game_resource.load_text("messages/banner.txt")
            # print game banner as supplied by the game
            print("\n" + banner + "\n")
        except IOError:
            # no banner provided by the game, print default game header
            print()
            print()
            msg = "'%s'" % self.config.name
            print(msg.center(player.DEFAULT_SCREEN_WIDTH))
            msg = "v%s" % self.config.version
            print(msg.center(player.DEFAULT_SCREEN_WIDTH))
            print()
            msg = "written by %s" % self.config.author
            print(msg.center(player.DEFAULT_SCREEN_WIDTH))
            if self.config.author_address:
                print(self.config.author_address.center(player.DEFAULT_SCREEN_WIDTH))
            print()

        choice = self.input("\nDo you want to load a saved game ('n' will start a new game)? ")
        print("")
        if choice == "y":
            self.load_saved_game()
            if args.transcript:
                self.player.activate_transcript(args.transcript)
            self.player.tell("\n")
            if self.mode == "if":
                self.story.welcome_savegame(self.player)
            else:
                self.player.tell("Welcome back to %s, %s." % (self.config.name, self.player.title))
            self.player.tell("\n")
        else:
            if self.mode == "if" and self.config.player_name:
                # interactive fiction mode, create the player from the game's config
                self.player = player.Player(self.config.player_name, self.config.player_gender, self.config.player_race)
            elif self.mode == "mud" or not self.config.player_name:
                # mud mode, or if mode without player config: create a character with the builder
                from .charbuilder import CharacterBuilder
                builder = CharacterBuilder(self)
                self.player = builder.build()
            if args.transcript:
                self.player.activate_transcript(args.transcript)
            # move the player to the starting location
            if "wizard" in self.player.privileges:
                self.player.move(self.config.startlocation_wizard)
            else:
                self.player.move(self.config.startlocation_player)
            self.player.tell("\n")
            if self.mode == "if":
                self.story.welcome(self.player)
            else:
                self.player.tell("Welcome to %s, %s." % (self.config.name, self.player.title), end=True)
            self.player.tell("\n")
        self.show_motd()
        self.player.look(short=False)
        self.write_output()
        self.player_input_allowed = threading.Event()
        self.start_player_input()
        self.main_loop()

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

    def show_motd(self):
        if self.mode != "if":
            motd, mtime = util.get_motd(self.game_resource)
            if motd:
                self.player.tell("Message-of-the-day, last modified on %s:" % mtime, end=True)
                self.player.tell("\n")
                self.player.tell(motd, end=True, format=True)  # for now, the motd is displayed *with* formatting
                self.player.tell("\n")
                self.player.tell("\n")

    def start_player_input(self):
        if self.config.server_tick_method == "timer":
            self.player_input_thread = PlayerInputThread(self.player, self.player_input_allowed)
            self.player_input_thread.setDaemon(True)
            self.player_input_thread.start()
        elif self.config.server_tick_method == "command":
            pass  # player input is done in the same thread as the game loop
        else:
            raise ValueError("invalid server_tick_method: " + self.config.server_tick_method)

    def main_loop(self):
        last_loop_time = last_server_tick = time.time()
        while True:
            globals.mud_context.player = self.player
            self.write_output()
            if self.player.story_complete and self.mode == "if":
                # congratulations ;-)
                self.story_complete_output(self.player.story_complete_callback)
                break
            self.player_input_allowed.set()
            if self.config.server_tick_method == "timer" and time.time() - last_server_tick >= self.config.server_tick_time:
                # NOTE: if the sleep time ever gets down to zero or below zero, the server load is too high
                last_server_tick = time.time()
                self.server_tick()
                loop_duration_with_server_tick = time.time() - last_loop_time
                self.server_loop_durations.append(loop_duration_with_server_tick)
            else:
                loop_duration = time.time() - last_loop_time

            if self.config.server_tick_method == "timer":
                try:
                    has_input = self.player.input_is_available.wait(max(0.01, self.config.server_tick_time - loop_duration))
                except KeyboardInterrupt:
                    self.player.tell(CTRL_C_MESSAGE)
                    continue
            elif self.config.server_tick_method == "command":
                PlayerInputThread.input_line(self.player, self.player_input_allowed, self.input)
                has_input = self.player.input_is_available.is_set()  # don't block
                before = time.time()
                self.server_tick()
                self.server_loop_durations.append(time.time() - before)

            last_loop_time = time.time()
            if has_input:
                try:
                    for cmd in self.player.get_pending_input():   # @todo hmm, all at once or limit player to 1 cmd/tick?
                        try:
                            self.process_player_input(cmd)
                            self.player.tell("\n")  # paragraph separation
                        except soul.UnknownVerbException as x:
                            if x.verb in self.directions:
                                self.player.tell("You can't go in that direction.")
                            else:
                                self.player.tell("The verb '%s' is unrecognized." % x.verb)
                        except (errors.ParseError, errors.ActionRefused) as x:
                            self.player.tell(str(x))
                except KeyboardInterrupt:
                    self.player.tell(CTRL_C_MESSAGE)
                except EOFError:
                    continue
                except errors.StoryCompleted as ex:
                    if self.mode == "if":
                        # congratulations ;-)
                        self.player.story_completed(ex.callback)
                    else:
                        pass   # in mud mode, the game can't be completed
                except errors.SessionExit:
                    choice = self.input("\nAre you sure you want to quit? ")
                    self.player.tell("\n")
                    if choice not in ("y", "yes"):
                        self.player.tell("Good, thanks for staying.")
                        self.start_player_input()
                        continue
                    while True:
                        choice = self.input("\nWould you like to save your progress? ")
                        self.player.tell("\n")
                        if choice in ("y", "yes"):
                            self.do_save(self.player)
                            break
                        elif choice in ("n", "no"):
                            break
                    if self.mode == "if":
                        self.story.goodbye(self.player)
                    else:
                        self.player.tell("Goodbye, %s. Please come back again soon." % self.player.title, end=True)
                    if self.config.server_tick_method == "timer":
                        self.player_input_thread.join()
                    break
                except Exception:
                    import traceback
                    txt = "* internal error:\n" + traceback.format_exc()
                    self.player.tell(txt, format=False)
        self.player.destroy({"driver": self})
        self.write_output()  # flush pending output at server shutdown.

    def server_tick(self):
        # Do everything that the server needs to do every tick.
        # First, adjust the game clock.
        self.game_clock.add_realtime(datetime.timedelta(seconds=self.config.server_tick_time))
        # Heartbeats.
        ctx = {"driver": self, "clock": self.game_clock, "state": self.state}
        for object in self.heartbeat_objects:
            object.heartbeat(ctx)
        # deferreds
        if self.deferreds:
            deferred = self.deferreds[0]
            if deferred.due <= self.game_clock.clock:
                deferred = heapq.heappop(self.deferreds)
                kwargs = deferred.kwargs
                kwargs["driver"] = self  # always add a 'driver' keyword argument for convenience
                # deferred callable is stored as a name, so we need to obtain the actual function:
                callable = getattr(deferred.owner, deferred.callable, None)
                if callable:
                    callable(*deferred.vargs, **kwargs)
        # buffered output
        self.write_output()

    def story_complete_output(self, callback):
        if callback:
            callback(self.player, self.config, self)
        else:
            self.player.tell("\n")
            self.story.completion(self.player)
            self.player.tell("\n")
            if self.config.max_score:
                self.player.tell("Your final score is %d out of a possible %d. (in %d turns)" %
                                 (self.player.score, self.config.max_score, self.player.turns), end=True)
            self.input("\nPress enter to continue. ")
            self.player.tell("\n")

    def write_output(self):
        """print any buffered player output to the screen"""
        if not self.player:
            return
        output = self.player.get_wrapped_output_lines()
        if output:
            if self.mode == "if" and 0 < self.output_line_delay < 1000:
                for line in output.splitlines():
                    print(line)
                    sys.stdout.flush()
                    time.sleep(self.output_line_delay / 1000)
            else:
                print(output)
                sys.stdout.flush()

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

        self.player.tell("\n")
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
                        self.player.location.notify_action(parsed, self.player)
                    else:
                        parse_error = "Please be more specific."
                if not handled:
                    if parsed.verb in self.player.location.exits:
                        self.go_through_exit(self.player, parsed.verb)
                    elif parsed.verb in command_verbs:
                        func = command_verbs[parsed.verb]
                        func(self.player, parsed, driver=self, verbs=command_verbs, config=self.config,
                                                  clock=self.game_clock, state=self.state)
                        if func.enable_notify_action:
                            self.player.location.notify_action(parsed, self.player)
                    else:
                        raise errors.ParseError(parse_error)
            except errors.RetrySoulVerb as x:
                # cmd decided it can't deal with the parsed stuff and that it needs to be retried as soul emote.
                self.player.validate_socialize_targets(parsed)
                self.do_socialize(parsed)

    def go_through_exit(self, player, direction):
        exit = player.location.exits[direction]
        exit.allow_passage(player)
        player.move(exit.target)
        player.look()

    def do_socialize(self, parsed):
        who, player_message, room_message, target_message = self.player.socialize_parsed(parsed)
        self.player.tell(player_message)
        self.player.location.tell(room_message, self.player, who, target_message)
        self.player.location.notify_action(parsed, self.player)
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
        num_tics = int(duration.seconds / self.config.gametime_to_realtime / self.config.server_tick_time)
        if num_tics < 1:
            return False, "It's no use waiting such a short while."
        for _ in range(num_tics):
            self.server_tick()
        return True, None     # wait was uneventful. (@todo return False if something happened)

    def do_save(self, player):
        state = {
            "version": self.config.version,
            "gamestate": self.state,
            "player": self.player,
            "deferreds": self.deferreds,
            "clock": self.game_clock,
            "heartbeats": self.heartbeat_objects,
            "config": self.config
        }
        with open(self.config.name.lower() + ".savegame", "wb") as out:
            pickle.dump(state, out, protocol=pickle.HIGHEST_PROTOCOL)
        player.tell("Game saved.")
        if self.config.display_gametime:
            player.tell("Game time:", self.game_clock)
        player.tell("\n")

    def load_saved_game(self):
        try:
            with open(self.config.name.lower() + ".savegame", "rb") as savegame:
                state = pickle.load(savegame)
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
        Note that the due time is time datetime.datetime *in game time*
        (not real time!) when the deferred should trigger.
        Also note that the deferred *always* gets a kwarg 'driver' set to the driver object
        (this makes it easy to register a new deferred on the driver without the need to
        access the global driver object)
        """
        assert isinstance(due, datetime.datetime)
        assert due >= self.game_clock.clock
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
            heapq.heappush(self.deferreds, deferred)
            return
        raise ValueError("unknown callable on owner object")

    def remove_deferreds(self, owner):
        self.deferreds = [d for d in self.deferreds if d.owner is not owner]
        heapq.heapify(self.deferreds)

    def input(self, prompt=None):
        """Writes any pending output and prompts for input. Returns stripped result."""
        self.write_output()
        return input(prompt).strip()


class PlayerInputThread(threading.Thread):
    def __init__(self, player, input_allowed):
        super(PlayerInputThread, self).__init__()
        self.player = player
        self.input_allowed = input_allowed

    def run(self):
        while PlayerInputThread.input_line(self.player, self.input_allowed, input):
            pass

    @classmethod
    def input_line(cls, player, input_allowed, input_function):
        """
        Input a line of text by the player.
        It's a classmethod because it's also used by the 'command' driven server loop.
        """
        try:
            input_allowed.wait()
            sys.stdout.flush()
            cmd = input_function("\n>> ").lstrip()
            input_allowed.clear()
            player.input_line(cmd)
            if cmd == "quit":
                return False
        except KeyboardInterrupt:
            player.tell(CTRL_C_MESSAGE)
        except EOFError:
            pass
        return True


if __name__ == "__main__":
    driver = Driver()
    driver.start(sys.argv[1:])
