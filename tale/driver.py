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
from . import races
from . import soul
from . import player
from . import cmds
from . import rooms
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


@total_ordering
class Deferred(object):
    __slots__ = ("due", "owner", "callable", "vargs", "kwargs")

    def __init__(self, due, owner, callable, vargs, kwargs):
        self.due = due
        self.owner = owner
        self.callable = callable
        self.vargs = vargs
        self.kwargs = kwargs

    def __eq__(self, other):
        return self.due == other.due

    def __lt__(self, other):
        return self.due < other.due   # deferreds must be sortable


def create_player_from_info():
    while True:
        name = input("Name? ").strip()
        if name:
            break
    gender = input("Gender m/f/n? ").strip()[0]
    while True:
        print("Player races:", ", ".join(races.player_races))
        race = input("Race? ").strip()
        if race in races.player_races:
            break
        print("Unknown race, try again.")
    wizard = input("Wizard y/n? ").strip() == "y"
    description = "This is a random mud player."
    p = player.Player(name, gender, race, description)
    if wizard:
        p.privileges.add("wizard")
        p.set_title("arch wizard %s", includes_name_param=True)
    return p


def create_default_wizard():
    p = player.Player("irmen", "m", "human", "This wizard looks very important.")
    p.privileges.add("wizard")
    p.set_title("arch wizard %s", includes_name_param=True)
    return p


def create_default_player():
    return player.Player("irmen", "m", "human", "A regular person.")


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


CTRL_C_MESSAGE = "\n* break: Use <quit> if you want to quit."


def version_tuple(v_str):
    return tuple(int(n) for n in v_str.split('.'))


class Driver(object):
    directions = {"north", "east", "south", "west", "northeast", "northwest", "southeast", "southwest", "up", "down"}

    def __init__(self):
        tale_version = version_tuple(tale_version_str)
        tale_version_required = version_tuple(globals.REQUIRES_TALE_VERSION)
        if tale_version < tale_version_required:
            raise RuntimeError("The game requires tale " + globals.REQUIRES_TALE_VERSION + " but installed is " + tale_version_str)
        self.heartbeat_objects = set()
        self.state = {}  # global game state variables
        self.unbound_exits = []
        self.deferreds = []  # heapq
        server_started = datetime.datetime.now()
        self.server_started = server_started.replace(microsecond=0)
        self.player = None
        self.commands = Commands()
        self.game_clock = globals.GAMETIME_EPOCH or self.server_started
        if globals.SERVER_TICK_METHOD == "command":
            globals.GAMETIME_TO_REALTIME = 1.0
        self.server_loop_durations = collections.deque(maxlen=10)
        globals.mud_context.driver = self
        globals.mud_context.state = self.state
        rooms.init(self)
        cmds.register_all(self.commands)
        self.bind_exits()

    def bind_exits(self):
        for exit in self.unbound_exits:
            exit.bind(rooms)
        del self.unbound_exits

    def start(self, args):
        # parse args
        parser = argparse.ArgumentParser(description='Parse driver arguments.')
        parser.add_argument('--transcript', type=str, help='transcript filename')
        args = parser.parse_args()

        # print GPL 3.0 banner
        print("\n'Tale' mud driver, mudlib and interactive fiction framework.")
        print("Copyright (C) 2012  Irmen de Jong.")
        print("This program comes with ABSOLUTELY NO WARRANTY. This is free software,")
        print("and you are welcome to redistribute it under the terms and conditions")
        print("of the GNU General Public License version 3. See the file LICENSE.txt")

        # print MUD banner and initiate player creation
        banner = util.get_banner()
        if banner:
            print("\n" + banner + "\n\n")
        print("This is '%s' version %s.\nYou're using Tale version %s." % (globals.GAME_TITLE, globals.GAME_VERSION, tale_version_str))
        choice = input("\nDo you want to load a saved game ('n' will start a new game)? ").strip()
        if choice == "y":
            print("")
            self.load_saved_game()
            if args.transcript:
                self.player.activate_transcript(args.transcript)
        else:
            choice = input("Create default (w)izard, default (p)layer, (c)ustom player? ").strip()
            if choice == "w":
                player = create_default_wizard()
            elif choice == "p":
                player = create_default_player()
            else:
                player = create_player_from_info()
            if args.transcript:
                player.activate_transcript(args.transcript)
            self.game_clock = globals.GAMETIME_EPOCH or self.server_started
            self.player = player
            self.move_player_to_start_room()
        self.player.tell("\n")
        self.player.tell("\n")
        self.player.tell("Welcome to %s, %s." % (globals.GAME_TITLE, self.player.title), end=True)
        self.player.tell("\n")
        self.show_motd()
        self.player.look(short=False)
        self.write_output()
        self.player_input_allowed = threading.Event()
        self.start_player_input()
        self.main_loop()

    def show_motd(self):
        motd, mtime = util.get_motd()
        if motd:
            self.player.tell("Message-of-the-day, last modified on %s:" % mtime, end=True)
            self.player.tell("\n")
            self.player.tell(motd, end=True, format=True)  # for now, the motd is displayed with formatting
            self.player.tell("\n")
            self.player.tell("\n")

    def start_player_input(self):
        if globals.SERVER_TICK_METHOD == "timer":
            self.player_input_thread = PlayerInputThread(self.player, self.player_input_allowed)
            self.player_input_thread.setDaemon(True)
            self.player_input_thread.start()
        elif globals.SERVER_TICK_METHOD == "command":
            self.player_input = PlayerInput(self.player, self.player_input_allowed)
        else:
            raise ValueError("invalid SERVER_TICK_METHOD: " + globals.SERVER_TICK_METHOD)

    def move_player_to_start_room(self):
        if "wizard" in self.player.privileges:
            self.player.move(rooms.STARTLOCATION_WIZARD)
        else:
            self.player.move(rooms.STARTLOCATION_PLAYER)

    def main_loop(self):
        last_loop_time = last_server_tick = time.time()
        while True:
            globals.mud_context.player = self.player
            self.write_output()
            if self.player.story_complete:
                # congratulations ;-)
                self.story_complete_output(self.player.story_complete_callback)
                break
            self.player_input_allowed.set()
            if globals.SERVER_TICK_METHOD == "timer" and time.time() - last_server_tick >= globals.SERVER_TICK_TIME:
                # @todo if the sleep time ever gets down to zero or below zero, the server load is too high
                last_server_tick = time.time()
                self.server_tick()
                loop_duration_with_server_tick = time.time() - last_loop_time
                self.server_loop_durations.append(loop_duration_with_server_tick)
            else:
                loop_duration = time.time() - last_loop_time

            if globals.SERVER_TICK_METHOD == "timer":
                try:
                    has_input = self.player.input_is_available.wait(max(0.01, globals.SERVER_TICK_TIME - loop_duration))
                except KeyboardInterrupt:
                    self.player.tell(CTRL_C_MESSAGE)
                    continue
            elif globals.SERVER_TICK_METHOD == "command":
                self.player_input.input_line()
                has_input = self.player.input_is_available.wait()
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
                    # congratulations ;-)
                    self.player.story_completed(ex.callback)
                except errors.SessionExit:
                    choice = input("\nAre you sure you want to quit? ").strip()
                    if choice not in ("y", "yes"):
                        self.player.tell("Good, thanks for staying.")
                        self.start_player_input()
                        continue
                    while True:
                        choice = input("\nWould you like to save your progress? ").strip()
                        if choice in ("y", "yes"):
                            self.do_save(self.player)
                            break
                        elif choice in ("n", "no"):
                            break
                    self.player.tell("Goodbye, %s. Please come back again soon." % self.player.title, end=True)
                    if globals.SERVER_TICK_METHOD == "timer":
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
        if globals.SERVER_TICK_METHOD == "timer":
            self.game_clock += datetime.timedelta(seconds=globals.GAMETIME_TO_REALTIME * globals.SERVER_TICK_TIME)
        elif globals.SERVER_TICK_METHOD == "command":
            self.game_clock += datetime.timedelta(seconds=globals.SERVER_TICK_TIME)
        # heartbeats
        ctx = {"driver": self, "game_clock": self.game_clock, "state": self.state}
        for object in self.heartbeat_objects:
            object.heartbeat(ctx)
        # deferreds
        if self.deferreds:
            deferred = self.deferreds[0]
            if deferred.due <= self.game_clock:
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
            callback(self.player, self)
        else:
            self.player.tell("\n")
            self.player.tell("Congratulations, you've finished the game.", end=True)
            if globals.MAX_SCORE:
                self.player.tell("Your final score is %d out of a possible %d. (in %d turns)" %
                                 (self.player.score, globals.MAX_SCORE, self.player.turns), end=True)

    def write_output(self):
        """print any buffered player output to the screen"""
        output = self.player.get_wrapped_output_lines()
        if output:
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
        custom_verbs = set(self.player.location.verbs) | set(self.player.verbs)
        all_verbs = set(command_verbs) | custom_verbs
        try:
            parsed = self.player.parse(cmd, external_verbs=all_verbs)
            # If parsing went without errors, it's a soul verb, handle it as a socialize action
            self.do_socialize(parsed)
            return
        except soul.NonSoulVerb as x:
            parsed = x.parsed
            if parsed.qualifier:
                # for now, qualifiers are only supported on soul-verbs (emotes).
                raise errors.ParseError("That action doesn't support qualifiers.")
            # Execute non-soul verb. First try directions, then the rest.
            try:
                if parsed.verb in self.player.location.exits:
                    self.go_through_exit(self.player, parsed.verb)
                    return True
                elif parsed.verb in command_verbs:
                    func = command_verbs[parsed.verb]
                    func(self.player, parsed, driver=self, verbs=command_verbs, game_clock=self.game_clock, state=self.state)
                    return
                elif parsed.verb in custom_verbs:
                    print(parsed) # XXX
                    print("@TODO: CUSTOM VERB (LOCATION or PLAYER):", parsed.verb)  # @ todo
                else:
                    raise errors.ParseError("That doesn't make much sense.")
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
        num_tics = int(duration.seconds / globals.GAMETIME_TO_REALTIME / globals.SERVER_TICK_TIME)
        if num_tics < 1:
            return False, "It's no use waiting such a short while."
        for _ in range(num_tics):
            self.server_tick()
        return True, None     # wait was uneventful. (@todo return False if something happened)

    def do_save(self, player):
        state = {
            "version": globals.GAME_VERSION,
            "gamestate": self.state,
            "player": self.player,
            "deferreds": self.deferreds,
            "game_clock": self.game_clock,
            "heartbeats": self.heartbeat_objects,
            "start_player": rooms.STARTLOCATION_PLAYER,
            "start_wizard": rooms.STARTLOCATION_WIZARD
        }
        with open(globals.GAME_TITLE.lower() + ".savegame", "wb") as out:
            pickle.dump(state, out, protocol=pickle.HIGHEST_PROTOCOL)
        player.tell("Game saved.")
        if globals.DISPLAY_GAMETIME:
            player.tell("Game time:", self.game_clock)
        player.tell("\n")

    def load_saved_game(self):
        try:
            with open(globals.GAME_TITLE.lower() + ".savegame", "rb") as savegame:
                state = pickle.load(savegame)
        except (IOError, pickle.PickleError) as x:
            print("There was a problem loading the saved game data:")
            print(type(x).__name__, x)
            raise SystemExit(10)
        else:
            if state["version"] != globals.GAME_VERSION:
                print("This saved game data was from a different version of the game and cannot be used.")
                print("(Current game version: %s  Saved game data version: %s)" % (globals.GAME_VERSION, state["version"]))
                raise SystemExit(10)
            self.player = state["player"]
            self.state = state["gamestate"]
            self.deferreds = state["deferreds"]
            self.game_clock = state["game_clock"]
            self.heartbeat_objects = state["heartbeats"]
            rooms.STARTLOCATION_PLAYER = state["start_player"]
            rooms.STARTLOCATION_WIZARD = state["start_wizard"]
            self.player.tell("Game loaded.")
            if globals.DISPLAY_GAMETIME:
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
        assert due >= self.game_clock
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


class PlayerInputThread(threading.Thread):
    def __init__(self, player, input_allowed):
        super(PlayerInputThread, self).__init__()
        self.player_input = PlayerInput(player, input_allowed)

    def run(self):
        while self.player_input.input_line():
            pass


class PlayerInput(object):
    def __init__(self, player, input_allowed):
        self.player = player
        self.input_allowed = input_allowed

    def input_line(self):
        try:
            self.input_allowed.wait()
            sys.stdout.flush()
            cmd = input("\n>> ").lstrip()
            self.input_allowed.clear()
            self.player.input(cmd)
            if cmd == "quit":
                return False
        except KeyboardInterrupt:
            self.player.tell(CTRL_C_MESSAGE)
        except EOFError:
            pass
        return True


if __name__ == "__main__":
    driver = Driver()
    driver.start(sys.argv[1:])
