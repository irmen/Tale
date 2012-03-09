from __future__ import print_function
import sys
import mudlib.rooms
import mudlib.player
import mudlib.races
import mudlib.soul
import mudlib.util
import mudlib.baseobjects
import mudlib.errors
import mudlib.cmds

def create_player_from_info():
    while True:
        name = raw_input("Name? ").strip()
        if name:
            break
    gender = raw_input("Gender m/f/n? ").strip()[0]
    while True:
        print("Player races:", ", ".join(mudlib.races.player_races))
        race = raw_input("Race? ").strip()
        if race in mudlib.races.player_races:
            break
        print("Unknown race, try again.")
    wizard = raw_input("Wizard y/n? ").strip() == "y"
    description = "some random mud player"
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


class Driver(object):
    def __init__(self):
        self.player = None
        self.commands_processor = {}
        mudlib.cmds.register_all(self.commands_processor)

    def start(self, args):
        # print GPL 3.0 banner
        print("\nSnakepit mud driver and mudlib. Copyright (C) 2012  Irmen de Jong.")
        print("This program comes with ABSOLUTELY NO WARRANTY. This is free software,")
        print("and you are welcome to redistribute it under the terms and conditions")
        print("of the GNU General Public License version 3. See the file LICENSE.txt")
        # print MUD banner and initiate player creation
        print("\n" + mudlib.MUD_BANNER + "\n")
        choice = raw_input("Create default (w)izard, default (p)layer, (c)ustom player? ").strip()
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
        while keep_going:
            mudlib.mud_context.driver = self
            mudlib.mud_context.player = self.player
            self.write_output()
            try:
                keep_going = self.ask_player_input()
            except mudlib.soul.UnknownVerbException, x:
                print("* The verb %s is unrecognised." % x.verb)
            except mudlib.errors.ParseException, x:
                print("* %s" % str(x))
            except Exception:
                import traceback
                print("* Error:")
                print(traceback.format_exc())
        self.write_output()

    def write_output(self):
        # print any buffered player output
        output = self.player.get_output_lines()
        print("".join(output))

    def ask_player_input(self):
        cmd = raw_input(">> ").strip()
        verb, _, rest = cmd.partition(" ")
        # pre-process input special cases
        if verb.startswith("'"):
            self.do_socialize("say " + cmd[1:])
            return True
        elif verb in self.commands_processor:
            func, privilege = self.commands_processor[verb]
            # @todo check privilege
            result = func(self.player, verb, rest, driver=self)
            return result != False
        else:
            self.do_socialize(cmd)
            return True

    def do_socialize(self, cmd):
        player = self.player
        verb, (who, player_message, room_message, target_message) = player.socialize(cmd)
        player.tell(player_message)
        player.location.tell(room_message, player, who, target_message)


if __name__ == "__main__":
    driver = Driver()
    driver.start(sys.argv[1:])
