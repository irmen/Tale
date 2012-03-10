# normal player commands
from __future__ import print_function
from .. import languagetools
from .. import soul
from .. import baseobjects
from .. import races
from ..errors import ParseError

all_commands = {}


def cmd(command, *aliases):
    """decorator to add the command to the global dictionary of commands"""
    def cmd2(func):
        if command in all_commands:
            raise ValueError("command defined more than once: "+command)
        all_commands[command] = func
        for alias in aliases:
            all_commands[alias] = func
        return func
    return cmd2


@cmd("inventory", "inv", "i")
def do_inventory(player, verb, arg, **ctx):
    print = player.tell
    if arg and "wizard" in player.privileges:
        # show another living's inventory
        living = player.location.search_living(arg)
        if not living:
            print("%s isn't here." % arg)
        else:
            if not living.inventory:
                print(living.name, "is carrying nothing.")
            else:
                print(living.name, "is carrying:")
                for item in living.inventory:
                    print("  " + item.title)
    else:
        if not player.inventory:
            print("You are carrying nothing.")
        else:
            print("You are carrying:")
            for item in player.inventory:
                print("  " + item.title)


@cmd("drop")
def do_drop(player, verb, arg, **ctx):
    print = player.tell
    if not arg:
        raise ParseError("Drop what?")
    item = player.search_item(arg, include_location=False)
    if not item:
        print("You don't have %s." % languagetools.a(arg))
    else:
        player.inventory.remove(item)
        player.location.add_item(item)
        print("You drop %s." % languagetools.a(item.title))
        player.location.tell("{player} drops {item}."
                                  .format(player=languagetools.capital(player.title), item=languagetools.a(item.title)),
                                  exclude_living=player)


@cmd("take")
def do_take(player, verb, arg, **ctx):
    print = player.tell
    if not arg:
        raise ParseError("Take what?")
    item = player.search_item(arg, include_inventory=False)
    if not item:
        print("There's no %s here." % arg)
    else:
        player.location.remove_item(item)
        player.inventory.add(item)
        print("You take %s." % languagetools.a(item.title))
        player.location.tell("{player} takes {item}."
                                  .format(player=languagetools.capital(player.title), item=languagetools.a(item.title)),
                                  exclude_living=player)


@cmd("help", "?")
def do_help(player, verb, topic, **ctx):
    print = player.tell
    if topic == "soul":
        print("* Soul verbs available:")
        lines = [""] * (len(soul.VERBS) // 5 + 1)
        index = 0
        for v in sorted(soul.VERBS):
            lines[index % len(lines)] += "  %-13s" % v
            index += 1
        for line in lines:
            print(line)
    else:
        print("* Available commands:", ", ".join(sorted(ctx["verbs"])))


@cmd("look", "l")
def do_look(player, verb, arg, **ctx):
    print = player.tell
    if arg:
        raise ParseError("Maybe you should examine that instead.")
    print(player.look())


@cmd("examine", "exa")
def do_examine(player, verb, arg, **ctx):
    print = player.tell
    if not arg:
        raise ParseError("Examine what?")
    player = player
    obj = player.search_name(arg, True)
    if obj:
        if "wizard" in player.privileges:
            print(repr(obj))
        if isinstance(obj, baseobjects.Living):
            print("This is %s." % obj.title)
            print(obj.description)
            race = races.races[obj.race]
            if obj.race == "human":
                # don't print as much info when dealing with mere humans
                msg = languagetools.capital("%s speaks %s." % (languagetools.SUBJECTIVE[obj.gender], race["language"]))
                print(msg)
            else:
                print("{subj}'s a {size} {btype} {race}, and speaks {lang}.".format(
                    subj=languagetools.capital(languagetools.SUBJECTIVE[obj.gender]),
                    size=races.sizes[race["size"]],
                    btype=races.bodytypes[race["bodytype"]],
                    race=obj.race,
                    lang=race["language"]
                ))
        else:
            if obj in player.inventory:
                print("You're carrying %s." % languagetools.a(obj.title))
            else:
                print("You see %s." % languagetools.a(obj.title))
            print(obj.description)
    else:
        # @todo: suggest name, like soul does?
        print("* %s isn't here." % arg)


@cmd("stats")
def do_stats(player, verb, arg, **ctx):
    print = player.tell
    if arg:
        target = player.location.search_living(arg)
        if not target:
            print("* %s isn't here." % arg)
            return
    else:
        target = player
    gender = languagetools.GENDERS[target.gender]
    living_type = target.__class__.__name__.lower()
    race = races.races[target.race]
    race_size = races.sizes[race["size"]]
    race_bodytype = races.bodytypes[race["bodytype"]]
    print("%s (%s) - %s %s %s" % (target.title, target.name, gender, target.race, living_type))
    print("%s %s, speaks %s, weighs ~%s kg." % (languagetools.capital(race_size), race_bodytype, race["language"], race["mass"]))
    print(", ".join("%s:%s" % (s[0], s[1]) for s in sorted(target.stats.items())))


@cmd("quit")
def do_quit(player, verb, arg, **ctx):
    # @todo: ask for confirmation (async)
    player.tell("Goodbye, %s." % player.title)
    return False
