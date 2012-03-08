from __future__ import print_function
import sys
import types
import copy
import mudlib.rooms
import mudlib.player
import mudlib.races
import mudlib.soul
import mudlib.util
import mudlib.baseobjects
import mudlib.languagetools as lang

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
        keepgoing = True
        while keepgoing:
            mudlib.mud_context.driver = self
            mudlib.mud_context.player = self.player
            self.write_output()
            try:
                keepgoing = self.ask_player_input()
            except mudlib.soul.UnknownVerbException, x:
                print("* The verb %s is unrecognised." % x.verb)
            except mudlib.soul.ParseException, x:
                print("* %s" % x.message)

    def write_output(self):
        # print any buffered player output
        output = self.player.get_output_lines()
        print("".join(output))

    def ask_player_input(self):
        cmd = raw_input(">> ").strip()
        verb, _, rest = cmd.partition(" ")
        # preprocess input special cases
        if verb.startswith("'"):
            self.do_command("say " + cmd[1:])
        elif verb.startswith("?"):
            self.do_help(cmd[1:].strip())
        elif verb == "help":
            self.do_help(rest)
        elif verb in ("l", "look"):
            self.do_look(rest)
        elif verb in ("exa", "examine"):
            self.do_examine(rest)
        elif verb == "stats":
            self.do_stats(rest)
        elif verb in ("i", "inv", "inventory"):
            self.do_inventory()
        elif verb == "quit":
            return False
        elif verb == "ls" and "wizard" in self.player.privileges:
            self.do_ls(rest)
        elif verb == "clone" and "wizard" in self.player.privileges:
            self.do_clone(rest)
        else:
            self.do_command(cmd)
        return True

    def do_command(self, cmd):
        player = self.player
        verb, (who, player_message, room_message, target_message) = player.socialize(cmd)
        player.tell(player_message)
        player.location.tell(room_message, player, who, target_message)

    def do_inventory(self):
        print = self.player.tell
        if not self.player.inventory:
            print("You are carrying nothing.")
        else:
            print("You are carrying:")
            for item in self.player.inventory:
                print("  " + item.title)

    def do_ls(self, path):
        print = self.player.tell
        if not path.startswith("."):
            path = "." + path
        try:
            module = __import__("mudlib" + path)
            for name in path.split("."):
                if name:
                    module = getattr(module, name)
        except (ImportError, ValueError):
            print("* ls: here is no module named " + path)
            return
        print("<%s>" % path)
        modules = [x[0] for x in vars(module).items() if type(x[1]) is types.ModuleType]
        classes = [x[0] for x in vars(module).items() if type(x[1]) is type and issubclass(x[1], mudlib.baseobjects.MudObject)]
        items = [x[0] for x in vars(module).items() if isinstance(x[1], mudlib.baseobjects.Item)]
        if modules:
            print("Modules: " + ", ".join(modules))
        if classes:
            print("Classes: " + ", ".join(classes))
        if items:
            print("Items: " + ", ".join(items))

    def do_clone(self, path):
        print = self.player.tell
        if not path.startswith("."):
            path = "." + path
        path, objectname = path.rsplit(".", 1)
        if not objectname:
            print("* clone: invalid object path")
            return
        try:
            module = __import__("mudlib" + path)
        except (ImportError, ValueError):
            print("* clone: there is no module named " + path)
            return
        if len(path) > 1:
            for name in path.split(".")[1:]:
                module = getattr(module, name)
        object = getattr(module, objectname, None)
        if object is None or not isinstance(object, mudlib.baseobjects.Item):
            print("* clone: object not found")
            return
        item = copy.deepcopy(object)
        self.player.inventory.add(item)
        print("* cloned: " + repr(item))
        self.player.location.tell("{player} conjures up {item}, and quickly pockets it."
            .format(player = lang.capital(self.player.title), item = lang.a(item.title)),
            exclude_living = self.player)

    def do_help(self, topic):
        print = self.player.tell
        if topic == "soul":
            print("* Soul verbs available:")
            lines = [""] * (len(mudlib.soul.VERBS)//5+1)
            index = 0
            for v in sorted(mudlib.soul.VERBS):
                lines[index % len(lines)] += "  %-13s" % v
                index += 1
            for line in lines:
                print(line)
        else:
            print("* Builtin commands: l/look, exa/examine, stats, quit.")
            print("* Help: ?/help with optional topic ('soul' for soul verb list).")
            print("* No further help available yet.")

    def do_look(self, arg):
        print = self.player.tell
        if arg:
            raise mudlib.soul.ParseException("Maybe you should examine that instead.")
        print(self.player.look())

    def do_examine(self, arg):
        print = self.player.tell
        if not arg:
            raise mudlib.soul.ParseException("Examine what?")
        player = self.player
        living = self.player.location.search_living(arg)
        if living:
            if "wizard" in self.player.privileges:
                print(mudlib.util.wizard_obj_info(living))
            print("This is %s.\n%s" % (living.title, lang.fullstop(living.description)))
            race = mudlib.races.races[living.race]
            if living.race == "human":
                # don't print as much info when dealing with mere humans
                msg = lang.capital("%s speaks %s." % (lang.SUBJECTIVE[living.gender], race["language"]))
                print(msg)
            else:
                print("{subj}'s a {size} {btype} {race}, and speaks {lang}.".format(
                    subj=lang.capital(lang.SUBJECTIVE[living.gender]),
                    size=mudlib.races.sizes[race["size"]],
                    btype=mudlib.races.bodytypes[race["bodytype"]],
                    race=living.race,
                    lang=race["language"]
                    ))
        else:
            # @todo: suggest name, like soul does?
            print("* %s isn't here." % arg)

    def do_stats(self, arg):
        print = self.player.tell
        if arg:
            target = self.player.location.search_living(arg)
            if not target:
                print("* %s isn't here." % arg)
                return
        else:
            target = self.player
        gender = lang.GENDERS[target.gender]
        living_type = target.__class__.__name__.lower()
        race = mudlib.races.races[target.race]
        race_size = mudlib.races.sizes[race["size"]]
        race_bodytype = mudlib.races.bodytypes[race["bodytype"]]
        print("%s (%s) - %s %s %s" % (target.title, target.name, gender, target.race, living_type))
        print("%s %s, speaks %s, weighs ~%s kg." % (lang.capital(race_size), race_bodytype, race["language"], race["mass"]))
        print(", ".join("%s:%s" % (s[0], s[1]) for s in sorted(target.stats.items())))


if __name__ == "__main__":
    driver = Driver()
    driver.start(sys.argv[1:])
