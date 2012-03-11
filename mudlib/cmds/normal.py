"""
Normal player commands.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function
from .. import languagetools
from .. import soul
from .. import baseobjects
from .. import races
from ..errors import ParseError, ActionRefused

all_commands = {}
abbreviations = {}   # will be injected


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


@cmd("inventory", "inv")
def do_inventory(player, verb, arg, **ctx):
    print = player.tell
    if arg and "wizard" in player.privileges:
        # show another living's inventory
        living = player.location.search_living(arg)
        if not living:
            raise ActionRefused("%s isn't here." % arg)
        else:
            name = languagetools.capital(living.title)
            if not living.inventory:
                print(name, "is carrying nothing.")
            else:
                print(name, "is carrying:")
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


@cmd("give")
def do_give(player, verb, arg, **ctx):
    print = player.tell
    if not arg:
        raise ParseError("Give what to whom?")
    # support "give living [the] thing" and "give [the] thing [to] living"
    args = [word for word in arg.split() if word not in ("the", "to")]
    if len(args)!=2:
        raise ParseError("Give what to whom?")
    item_name, target_name = args
    item = player.search_item(item_name, include_location=False)
    if not item:
        target_name, item_name = args
        item = player.search_item(item_name, include_location=False)
        if not item:
            print("You don't have that.")
            return
    living = player.location.search_living(target_name)
    if not living:
        raise ActionRefused("%s isn't here." % target_name)
    living.accept("give", item, player)
    player.inventory.remove(item)
    living.inventory.add(item)
    item_str = languagetools.a(item.title)
    player_str = languagetools.capital(player.title)
    room_msg = "%s gave %s to %s." % (player_str, item_str, living.title)
    target_msg = "%s gave you %s." % (player_str, item_str)
    player.location.tell(room_msg, exclude_living=player, specific_targets=[living], specific_target_msg=target_msg)
    player.tell("You gave %s %s." % (living.title, item_str))


@cmd("help")
def do_help(player, verb, topic, **ctx):
    print = player.tell
    if topic == "soul":
        print("Soul verbs available:")
        lines = [""] * (len(soul.VERBS) // 5 + 1)
        index = 0
        for v in sorted(soul.VERBS):
            lines[index % len(lines)] += "  %-13s" % v
            index += 1
        for line in lines:
            print(line)
    else:
        print("Available commands:", ", ".join(sorted(ctx["verbs"])))
        print("Abbreviations:", ", ".join(sorted("%s=%s" % (a, v) for a, v in abbreviations.items())))


@cmd("look")
def do_look(player, verb, arg, **ctx):
    print = player.tell
    if arg:
        if arg in player.location.exits:
            print(player.location.exits[arg].description)
        elif arg in abbreviations and abbreviations[arg] in player.location.exits:
            print(player.location.exits[abbreviations[arg]].description)
        else:
            raise ParseError("Maybe you should examine that instead.")
    else:
        print(player.look())


@cmd("examine", "exa")
def do_examine(player, verb, arg, **ctx):
    print = player.tell
    if not arg:
        raise ParseError("Examine what?")
    player = player
    obj = player.search_name(arg)
    if obj:
        if "wizard" in player.privileges:
            print(repr(obj))
        if isinstance(obj, baseobjects.Living):
            print("This is %s." % obj.title)
            print(obj.description)
            race = races.races[obj.race]
            if obj.race == "human":
                # don't print as much info when dealing with mere humans
                msg = languagetools.capital("%s speaks %s." % (obj.subjective, race["language"]))
                print(msg)
            else:
                print("{subj}'s a {size} {btype} {race}, and speaks {lang}.".format(
                    subj=languagetools.capital(obj.subjective),
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
    elif arg in player.location.exits:
        print(player.location.exits[arg].description)
    elif arg in abbreviations and abbreviations[arg] in player.location.exits:
        print(player.location.exits[abbreviations[arg]].description)
    else:
        raise ActionRefused("%s isn't here." % arg)


@cmd("stats")
def do_stats(player, verb, arg, **ctx):
    print = player.tell
    if arg:
        target = player.location.search_living(arg)
        if not target:
            raise ActionRefused("%s isn't here." % arg)
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


@cmd("tell")
def do_tell(player, verb, args, **ctx):
    print = player.tell
    name, _, msg = args.partition(" ")
    msg = msg.strip()
    if not name or not msg:
        raise ActionRefused("Tell whom what?")
    # first look for a living with the name
    living = player.location.search_living(name)
    if not living:
        # ask the driver if there's a player with that name (globally)
        living = ctx["driver"].search_player(name)
        if not living:
            if name=="all":
                raise ActionRefused("You can't tell something to everyone, only to individuals.")
            raise ActionRefused("%s isn't here." % name)
    if living is player:
        player.tell("You're talking to yourself...")
    else:
        living.tell("%s tells you: %s" % (player.name, msg))
        player.tell("You told %s." % name)


@cmd("quit")
def do_quit(player, verb, arg, **ctx):
    # @todo: ask for confirmation (async)
    player.tell("Goodbye, %s." % player.title)
    return False
