"""
Mud driver (server).

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division
import sys
import mudlib.rooms
import mudlib.player
import mudlib.races
import mudlib.soul
import mudlib.util
import mudlib.base
import mudlib.errors
import mudlib.cmds


if sys.version_info < (3, 0):
    input = raw_input


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
        self.commands_per_priv.setdefault(privilege, {})[verb] = func

    def get(self, privileges):
        result = self.commands_per_priv[None]  # always include the cmds for None
        for priv in privileges:
            if priv in self.commands_per_priv:
                result.update(self.commands_per_priv[priv])
        return result


class Driver(object):
    def __init__(self):
        self.player = None
        self.commands = Commands()
        mudlib.cmds.register_all(self.commands)

    def start(self, args):
        # print GPL 3.0 banner
        print("\nSnakepit mud driver and mudlib. Copyright (C) 2012  Irmen de Jong.")
        print("This program comes with ABSOLUTELY NO WARRANTY. This is free software,")
        print("and you are welcome to redistribute it under the terms and conditions")
        print("of the GNU General Public License version 3. See the file LICENSE.txt")
        # print MUD banner and initiate player creation
        print("\n" + mudlib.MUD_BANNER + "\n")
        choice = input("Create default (w)izard, default (p)layer, (c)ustom player? ").strip()
        if choice == "w":
            player = create_default_wizard()
        elif choice == "p":
            player = create_default_player()
        else:
            player = create_player_from_info()
        self.player = player
        self.move_player_to_start_room()
        self.player.tell("\nWelcome to %s, %s.\n\n" % (mudlib.MUD_NAME, self.player.title))
        self.player.tell(self.player.look())
        self.main_loop()

    def move_player_to_start_room(self):
        if "wizard" in self.player.privileges:
            self.player.move(mudlib.rooms.STARTLOCATION_WIZARD)
        else:
            self.player.move(mudlib.rooms.STARTLOCATION_PLAYER)

    def main_loop(self):
        print = self.player.tell
        keep_going = True
        directions = {"north", "east", "south", "west", "northeast", "northwest", "southeast", "southwest", "up", "down"}
        while True:
            mudlib.mud_context.driver = self
            mudlib.mud_context.player = self.player
            self.write_output()
            try:
                self.ask_player_input()
            except mudlib.soul.UnknownVerbException as x:
                if x.verb in directions:
                    print("You can't go in that direction.")
                else:
                    print("The verb %s is unrecognized." % x.verb)
            except (mudlib.errors.ParseError, mudlib.errors.ActionRefused) as x:
                print(str(x))
            except mudlib.errors.SessionExit:
                break
            except Exception:
                import traceback
                print("* internal error:")
                print(traceback.format_exc())
        self.write_output()

    def write_output(self):
        # print any buffered player output
        output = self.player.get_output_lines()
        print("".join(output))

    def ask_player_input(self):
        cmd = input(">> ").lstrip()
        if not cmd:
            return True
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
        external_verbs = frozenset(player_verbs) | frozenset(self.player.location.exits)
        try:
            parsed = self.player.parse(cmd, external_verbs)
            # If parsing went without errors, it's a soul verb, handle it as a socialize action
            self.do_socialize(parsed)
            return
        except mudlib.soul.NonSoulVerb as x:
            print("NONSOULVERB!", x.parsed)  # XXX
            parsed = x.parsed
            # Execute non-soul verb. First try directions, then the rest
            if parsed.verb in self.player.location.exits:
                self.do_move(parsed.verb)
                return True
            elif parsed.verb in player_verbs:
                func = player_verbs[parsed.verb]
                func(self.player, parsed, driver=self, verbs=player_verbs)
                return
            else:
                raise mudlib.soul.ParseError("failed to parse the command line correctly")

    def do_move(self, direction):
        exit = self.player.location.exits[direction]
        if not exit.bound:
            # resolve the location and replace with bound Exit
            target_module, target_object = exit.target.rsplit(".", 1)
            module = mudlib.rooms
            for name in target_module.split("."):
                module = getattr(module, name)
            target = getattr(module, target_object)
            exit.bind(target)
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


if __name__ == "__main__":
    driver = Driver()
    driver.start(sys.argv[1:])
