"""
Mud driver (server).

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division
import collections
import datetime
import sys
import time
import os
import threading
import heapq
import mudlib.globals       # don't import anything else from mudlib, see delayed_imports()
try:
    import readline
except ImportError:
    pass
else:
    history = os.path.expanduser("~/.snakepit_history")
    readline.parse_and_bind("tab: complete")
    try:
        readline.read_history_file(history)
    except IOError:
        pass
    import atexit

    def save_history(historyfile):
        readline.write_history_file(historyfile)

    atexit.register(save_history, history)


if sys.version_info < (3, 0):
    input = raw_input


def delayed_imports():
    # we can't do these imports in global scope because first,
    # the global driver object in mudlib.globals.mud_context needs to be set.
    import mudlib.errors
    import mudlib.cmds
    import mudlib.rooms
    import mudlib.soul
    import mudlib.races
    import mudlib.player
    import mudlib.util


def create_player_from_info():
    while True:
        name = input("Name? ").strip()
        if name:
            break
    gender = input("Gender m/f/n? ").strip()[0]
    while True:
        print("Player races:", ", ".join(mudlib.races.player_races))
        race = input("Race? ").strip()
        if race in mudlib.races.player_races:
            break
        print("Unknown race, try again.")
    wizard = input("Wizard y/n? ").strip() == "y"
    description = "This is a random mud player."
    player = mudlib.player.Player(name, gender, race, description)
    if wizard:
        player.privileges.add("wizard")
        player.set_title("arch wizard %s", includes_name_param=True)
    return player


def create_default_wizard():
    player = mudlib.player.Player("irmen", "m", "human", "This wizard looks very important.")
    player.privileges.add("wizard")
    player.set_title("arch wizard %s", includes_name_param=True)
    return player


def create_default_player():
    player = mudlib.player.Player("irmen", "m", "human", "A regular person.")
    return player


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


class Driver(object):
    SERVER_TICK_TIME = 1.0    # in seconds
    GAMETIME_TO_REALTIME = 5    # meaning: game time is X times the speed of real time
    GAMETIME_EPOCH = datetime.datetime(2012, 4, 19, 14, 0, 0)

    def __init__(self):
        self.heartbeat_objects = set()
        self.unbound_exits = []
        self.deferreds = []  # heapq
        server_started = datetime.datetime.now()
        self.server_started = server_started.replace(microsecond=0)
        self.player = None
        self.commands = Commands()
        self.game_clock = self.GAMETIME_EPOCH
        self.server_loop_durations = collections.deque(maxlen=10)
        mudlib.globals.mud_context.driver = self
        delayed_imports()
        mudlib.cmds.register_all(self.commands)
        self.bind_exits()

    def bind_exits(self):
        for exit in self.unbound_exits:
            exit.bind(mudlib.rooms)
        del self.unbound_exits

    def start(self, args):
        # print GPL 3.0 banner
        print("\nSnakepit mud driver and mudlib. Copyright (C) 2012  Irmen de Jong.")
        print("This program comes with ABSOLUTELY NO WARRANTY. This is free software,")
        print("and you are welcome to redistribute it under the terms and conditions")
        print("of the GNU General Public License version 3. See the file LICENSE.txt")
        # print MUD banner and initiate player creation
        banner = mudlib.util.get_banner()
        if banner:
            print("\n" + banner + "\n\n")
        choice = input("Create default (w)izard, default (p)layer, (c)ustom player? ").strip()
        if choice == "w":
            player = create_default_wizard()
        elif choice == "p":
            player = create_default_player()
        else:
            player = create_player_from_info()
        self.player = player
        self.move_player_to_start_room()
        self.player.tell("\nWelcome, %s.\n" % self.player.title)
        motd, mtime = mudlib.util.get_motd()
        if motd:
            self.player.tell("Message-of-the-day, last modified on %s:" % mtime)
            self.player.tell(motd + "\n\n")
        self.player.tell(self.player.look())
        self.write_output()
        self.player_input_allowed = threading.Event()
        self.player_input_thread = PlayerInputThread(player, self.player_input_allowed)
        self.player_input_thread.setDaemon(True)
        self.player_input_thread.start()
        self.game_clock = self.GAMETIME_EPOCH
        self.main_loop()

    def move_player_to_start_room(self):
        if "wizard" in self.player.privileges:
            self.player.move(mudlib.rooms.STARTLOCATION_WIZARD)
        else:
            self.player.move(mudlib.rooms.STARTLOCATION_PLAYER)

    def main_loop(self):
        print = self.player.tell
        directions = {"north", "east", "south", "west", "northeast", "northwest", "southeast", "southwest", "up", "down"}
        last_loop_time = last_server_tick = time.time()
        mudlib.globals.mud_context.player = self.player
        while True:
            self.write_output()
            self.player_input_allowed.set()
            if time.time() - last_server_tick >= self.SERVER_TICK_TIME:
                # @todo if the sleep time ever gets down to zero or below zero, the server load is too high
                last_server_tick = time.time()
                self.server_tick()
                loop_duration_with_server_tick = time.time() - last_loop_time
                self.server_loop_durations.append(loop_duration_with_server_tick)
            else:
                loop_duration = time.time() - last_loop_time
            try:
                has_input = self.player.input_is_available.wait(max(0.01, self.SERVER_TICK_TIME - loop_duration))
            except KeyboardInterrupt:
                print("\n* break: Use <quit> if you want to quit.")
                continue
            last_loop_time = time.time()
            if has_input:
                try:
                    for cmd in self.player.get_pending_input():   # @todo hmm, all at once or limit player to 1 cmd/tick?
                        try:
                            self.process_player_input(cmd)
                        except mudlib.soul.UnknownVerbException as x:
                            if x.verb in directions:
                                print("You can't go in that direction.")
                            else:
                                print("The verb %s is unrecognized." % x.verb)
                        except (mudlib.errors.ParseError, mudlib.errors.ActionRefused) as x:
                            print(str(x))
                except KeyboardInterrupt:
                    print("\n* break: Use <quit> if you want to quit.")
                except EOFError:
                    continue
                except mudlib.errors.SessionExit:
                    print("Exiting...")
                    self.player_input_thread.join()
                    break
                except Exception:
                    import traceback
                    print("* internal error:")
                    print(traceback.format_exc())
        self.write_output()  # flush pending output at server shutdown.

    def server_tick(self):
        # Do everything that the server needs to do every tick.
        self.game_clock += datetime.timedelta(seconds=self.GAMETIME_TO_REALTIME * self.SERVER_TICK_TIME)
        # heartbeats
        ctx = {"driver": self, "game_clock": self.game_clock}
        for object in self.heartbeat_objects:
            object.heartbeat(ctx)
        # deferreds
        if self.deferreds:
            activation = self.deferreds[0][0]
            if activation <= self.game_clock:
                activation, deferred, vargs, kwargs = heapq.heappop(self.deferreds)
                deferred(*vargs, **kwargs)
        # buffered output
        self.write_output()

    def write_output(self):
        # print any buffered player output
        output = self.player.get_output_lines()
        if output:
            print("".join(output))
            sys.stdout.flush()

    def process_player_input(self, cmd):
        if not cmd:
            return
        if cmd and cmd[0] in mudlib.cmds.abbreviations and not cmd[0].isalpha():
            # insert a space to separate the first char such as ' or ?
            cmd = cmd[0] + " " + cmd[1:]
        # check for an abbreviation, replace it with the full verb if present
        _verb, _sep, _rest = cmd.partition(" ")
        if _verb in mudlib.cmds.abbreviations:
            _verb = mudlib.cmds.abbreviations[_verb]
            cmd = "".join([_verb, _sep, _rest])

        # Parse the command by using the soul.
        # We pass in all 'external verbs' (non-soul verbs) so it will do the
        # parsing for us even if it's a verb the soul doesn't recognise by itself.
        player_verbs = self.commands.get(self.player.privileges)
        try:
            parsed = self.player.parse(cmd, external_verbs=frozenset(player_verbs), room_exits=self.player.location.exits)
            # If parsing went without errors, it's a soul verb, handle it as a socialize action
            self.do_socialize(parsed)
            return
        except mudlib.soul.NonSoulVerb as x:
            parsed = x.parsed
            if parsed.qualifier:
                # for now, qualifiers are only supported on soul-verbs (emotes).
                raise mudlib.soul.ParseError("That action doesn't support qualifiers.")
            # Execute non-soul verb. First try directions, then the rest.
            try:
                if parsed.verb in self.player.location.exits:
                    self.go_through_exit(parsed.verb)
                    return True
                elif parsed.verb in player_verbs:
                    func = player_verbs[parsed.verb]
                    func(self.player, parsed, driver=self, verbs=player_verbs, game_clock=self.game_clock)
                    return
                else:
                    raise mudlib.soul.ParseError("That doesn't make much sense.")
            except mudlib.errors.RetrySoulVerb as x:
                # cmd decided it can't deal with the parsed stuff and that it needs to be retried as soul emote.
                self.do_socialize(parsed)

    def go_through_exit(self, direction):
        exit = self.player.location.exits[direction]
        exit.allow_passage(self.player)
        self.player.move(exit.target)
        self.player.tell(self.player.look())

    def do_socialize(self, parsed):
        who, player_message, room_message, target_message = self.player.socialize_parsed(parsed)
        self.player.tell(player_message)
        self.player.location.tell(room_message, self.player, who, target_message)
        if parsed.verb in mudlib.soul.AGGRESSIVE_VERBS:
            # usually monsters immediately attack,
            # other npcs may choose to attack or to ignore it
            # We need to check the qualifier, it might void the actual action :)
            if parsed.qualifier not in mudlib.soul.NEGATING_QUALIFIERS:
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
        num_tics = int(duration.seconds / self.GAMETIME_TO_REALTIME / self.SERVER_TICK_TIME)
        if num_tics < 1:
            return False, "It's no use waiting such a short while."
        for _ in range(num_tics):
            self.server_tick()
        return True, None     # wait was uneventful. (@todo return False if something happened)

    def register_heartbeat(self, mudobj):
        self.heartbeat_objects.add(mudobj)

    def unregister_heartbeat(self, mudobj):
        self.heartbeat_objects.discard(mudobj)

    def register_exit(self, exit):
        if not exit.bound:
            self.unbound_exits.append(exit)

    def deferred(self, activation, deferred, *vargs, **kwargs):
        """
        Register a deferred callable (optionally with arguments).
        Note that the activation is time datetime.datetime *in game time*
        (not real time!) when the deferred should trigger.
        """
        assert isinstance(activation, datetime.datetime)
        heapq.heappush(self.deferreds, (activation, deferred, vargs, kwargs))


class PlayerInputThread(threading.Thread):
    def __init__(self, player, input_allowed):
        super(PlayerInputThread, self).__init__()
        self.player = player
        self.input_allowed = input_allowed

    def run(self):
        while True:
            try:
                self.input_allowed.wait()
                sys.stdout.flush()
                cmd = input(">> ").lstrip()
                self.input_allowed.clear()
                self.player.input(cmd)
                if cmd == "quit":
                    break
            except KeyboardInterrupt:
                self.player.tell("\n* break: Use <quit> if you want to quit.")
            except EOFError:
                pass


if __name__ == "__main__":
    driver = Driver()
    driver.start(sys.argv[1:])
