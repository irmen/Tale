"""
Normal player commands.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division
from .. import languagetools
from .. import soul
from .. import races
from .. import util
from ..errors import ParseError, ActionRefused

all_commands = {}
abbreviations = {}   # will be injected


def cmd(command, *aliases):
    """decorator to add the command to the global dictionary of commands"""
    def cmd2(func):
        if command in all_commands:
            raise ValueError("command defined more than once: " + command)
        all_commands[command] = func
        for alias in aliases:
            all_commands[alias] = func
        return func
    return cmd2


@cmd("inventory")
def do_inventory(player, verb, arg, **ctx):
    print = player.tell
    if arg and "wizard" in player.privileges:
        # wizards may look at the inventory of everything else
        living = player.location.search_living(arg)
        if living:
            # show another living's inventory
            name = languagetools.capital(living.title)
            if not living.inventory:
                print(name, "is carrying nothing.")
            else:
                print(name, "is carrying:")
                for item in living.inventory:
                    print("  " + item.title)
            return
        item = player.search_item(arg)
        if item:
            # show item's inventory
            inventory = getattr(item, "inventory", None)
            if inventory:
                print("It contains:")
                for item in inventory:
                    print("  " + item.title)
            else:
                print("It's empty.")
        else:
            raise ActionRefused("Can't find %s." % arg)
    else:
        if not player.inventory:
            print("You are carrying nothing.")
        else:
            print("You are carrying:")
            for item in player.inventory:
                print("  " + item.title)


@cmd("locate")
def do_locate(player, verb, name, **ctx):
    print = player.tell
    if not name:
        raise ParseError("Locate what/who?")
    print("You look around to see if you can locate %s." % name)
    player.location.tell("%s looks around." % languagetools.capital(player.title), exclude_living=player)
    item, container = player.locate_item(name, include_inventory=True, include_location=True, include_containers_in_inventory=True)
    if item:
        if item.name.lower() != name.lower() and name.lower() in item.aliases:
            print("(by %s you probably mean %s)" % (name, item.name))
        util.print_object_location(player, item, container, False)
    living = player.location.search_living(name)
    if living and living.name.lower() != name.lower() and name.lower() in living.aliases:
        print("(by %s you probably mean %s)" % (name, living.name))
    if living and living is not player:
        print("%s is here next to you." % languagetools.capital(living.title))
    player = ctx["driver"].search_player(name)  # global player search
    if player:
        print("%s is playing, %s is currently in '%s'." % (languagetools.capital(player.title), player.subjective, player.location.name))
    else:
        if not item and not living:
            print("You can't seem to find that anywhere, and there's nobody here by that name.")


@cmd("drop")
def do_drop(player, verb, arg, **ctx):
    print = player.tell
    if not arg:
        raise ParseError("Drop what?")

    def drop_stuff(items, container):
        items = list(items)
        for item in items:
            if container is not player and container in player:
                print_item_removal(player, item, container)
            container.inventory.remove(item)
            player.location.enter(item)
        items_str = languagetools.join(languagetools.a(item.title) for item in items)
        print("You drop %s." % items_str)
        player.location.tell("{player} drops {items}."
                             .format(player=languagetools.capital(player.title), items=items_str),
                             exclude_living=player)
    if arg == "all":
        if not player.inventory:
            raise ActionRefused("You're not carrying anything.")
        else:
            # @todo: ask confirmation to drop everything
            drop_stuff(player.inventory, player)
    else:
        item, container = player.locate_item(arg, include_location=False)
        if not item:
            raise ActionRefused("You don't have %s." % languagetools.a(arg))
        else:
            util.print_object_location(player, item, container)
            drop_stuff([item], container)


@cmd("put")
def do_put(player, verb, args, **ctx):
    print = player.tell
    args = args.split()
    if len(args) < 2:
        raise ParseError("Put what where?")
    if args[1] == "in":
        where_name = args[2]
    else:
        where_name = args[1]
    if args[0] == "all":
        if not player.inventory:
            raise ActionRefused("You're not carrying anything.")
        # @todo: ask confirmation to put everything
        what = list(player.inventory)
    else:
        what = player.search_item(args[0], include_location=True)
        if not what:
            raise ActionRefused("You don't see %s." % languagetools.a(args[0]))
        what = [what]
    where = player.search_item(where_name)
    if where:
        if getattr(where, "public_inventory", False):
            room_items = []
            inventory_items = []
            for item in what:
                if item is where:
                    print("You can't put %s in itself." % item.title)
                    continue
                if item in player:
                    # simply use the item from the player's inventory
                    player.inventory.remove(item)
                    inventory_items.append(item)
                elif item in player.location:
                    # take the item from the room
                    player.location.leave(item)
                    room_items.append(item)
                where.accept(item, player)
                where.inventory.add(item)
            if inventory_items:
                items_msg = languagetools.join(languagetools.a(item.title) for item in inventory_items)
                player.location.tell("{player} puts {items} in the {where}.".format(
                    player=languagetools.capital(player.title),
                    items=items_msg, where=where.name), exclude_living=player)
                print("You put {items} in the {where}.".format(items=items_msg, where=where.name))
            if room_items:
                items_msg = languagetools.join(languagetools.a(item.title) for item in room_items)
                it_msg = "it" if len(inventory_items) < 2 else "them"
                player.location.tell("{player} takes {items}, and puts {it} in the {where}.".format(
                    player=languagetools.capital(player.title),
                    items=items_msg, it=it_msg, where=where.name), exclude_living=player)
                print("You take {items}, and put {it} in the {where}.".format(
                    items=items_msg, it=it_msg, where=where.name))
        else:
            raise ActionRefused("You can't put that in there.")
    else:
        living = player.location.search_living(where_name)
        if living:
            raise ActionRefused("You can't put stuff in %s, try giving it to %s?" % (living.name, living.objective))
        else:
            raise ActionRefused("There's no %s here." % where_name)


@cmd("take")
def do_take(player, verb, args, **ctx):
    """take thing|all , take thing|all [from] something"""
    print = player.tell
    args = args.split()
    if len(args) == 1:  # take thing|all
        what = args[0]
        where = None
    elif len(args) in (2, 3):  # take X [from] something
        what = args[0]
        where = args[1]
        if where == "from" and len(args) == 3:
            where = args[2]
    else:
        raise ParseError("Take what?")

    def take_stuff(items, container, is_location, where_str=None):
        if where_str:
            player_msg = "You take {items} from the %s." % where_str
            room_msg = "{player} takes {items} from the %s." % where_str
        else:
            player_msg = "You take {items}."
            room_msg = "{player} takes {items}."
        items = list(items)
        for item in items:
            if is_location:
                container.leave(item)
            else:
                container.inventory.remove(item)
            player.inventory.add(item)
        items_str = languagetools.join(languagetools.a(item.title) for item in items)
        print(player_msg.format(items=items_str))
        player.location.tell(room_msg.format(player=languagetools.capital(player.title), items=items_str), exclude_living=player)

    if what == "all":   # take ALL the things!
        if where:
            # take all stuff out of some container
            container = player.search_item(where)
            if container:
                if getattr(container, "public_inventory", False):
                    if container.inventory:
                        return take_stuff(container.inventory, container, False, where)
                    else:
                        raise ActionRefused("There's nothing in there.")
                else:
                    raise ActionRefused("You can't take things from there.")
            # no container, check if a living was targeted
            living = player.location.search_living(where)
            if living:
                if living is player:
                    raise ActionRefused("There's no reason to take things from yourself.")
                player.location.tell("%s tries to steal things from %s." % (languagetools.capital(player.title), living.title), exclude_living=player)
                if living.aggressive:
                    living.start_attack(player)  # stealing stuff is hostile!
                raise ActionRefused("You can't just steal stuff from %s!" % living.title)
            raise ActionRefused("There's no %s here." % where)
        if not player.location.items:
            raise ActionRefused("There's nothing here to take.")
        else:
            # take all stuff out of the room
            return take_stuff(player.location.items, player.location, True)
    else:  # just a single item
        if where:
            # take specific item out of some container
            container = player.search_item(where)
            if container:
                if getattr(container, "public_inventory", False):
                    for item in container.inventory:
                        if item.name == what:
                            return take_stuff([item], container, False, where)
                    raise ActionRefused("There's no %s in there." % what)
                else:
                    raise ActionRefused("You can't take things from there.")
            # no container, check if a living was targeted
            living = player.location.search_living(where)
            if living:
                if living is player:
                    raise ActionRefused("There's no reason to take things from yourself.")
                player.location.tell("%s tries to steal something from %s." % (languagetools.capital(player.title), living.title), exclude_living=player)
                if living.aggressive:
                    living.start_attack(player)  # stealing stuff is hostile!
                raise ActionRefused("You can't just steal stuff from %s!" % living.title)
            raise ActionRefused("There's no %s here." % where)
        # no specific source provided, search in room
        item = player.search_item(what, include_inventory=False)
        if item:
            return take_stuff([item], player.location, True)
        # no item, check if attempt to take living
        living = player.location.search_living(what)
        if living:
            living_race = races.races[living.race]
            player_race = races.races[player.race]
            if player_race["size"] - living_race["size"] >= 2:
                living.accept("take", None, player)  # @todo: do an agi/str/spd/luck check to see if we can pick it up
                print("Even though {subj}'s small enough, you can't carry {obj} with you.".format(subj=living.subjective, obj=living.objective))
            else:
                print("You can't carry {obj} with you, {subj}'s too large.".format(subj=living.subjective, obj=living.objective))
        else:
            print("There's no %s here." % what)


@cmd("give")
def do_give(player, verb, arg, **ctx):
    print = player.tell
    if not arg:
        raise ParseError("Give what to whom?")

    def give_stuff(items, target_name):
        target = player.location.search_living(target_name)
        if not target:
            raise ActionRefused("%s isn't here." % target_name)
        items = list(items)
        refused = []
        for item in items:
            try:
                target.accept("give", item, player)
                player.inventory.remove(item)
                target.inventory.add(item)
            except ActionRefused as x:
                refused.append((item, str(x)))
        for item, message in refused:
            print(message)
            items.remove(item)
        if items:
            items_str = languagetools.join(languagetools.a(item.title) for item in items)
            player_str = languagetools.capital(player.title)
            room_msg = "%s gave %s to %s." % (player_str, items_str, target.title)
            target_msg = "%s gave you %s." % (player_str, items_str)
            player.location.tell(room_msg, exclude_living=player, specific_targets=[target], specific_target_msg=target_msg)
            print("You gave %s %s." % (target.title, items_str))
        else:
            print("You didn't give %s anything." % target.title)

    # support "give living [the] thing" and "give [the] thing [to] living"
    args = [word for word in arg.split() if word not in ("the", "to")]
    if len(args) != 2:
        raise ParseError("Give what to whom?")
    item_name, target_name = args
    if item_name == "all":
        give_stuff(player.inventory, target_name)
    elif target_name == "all":
        give_stuff(player.inventory, item_name)
    else:
        item = player.search_item(item_name, include_location=False)
        if not item:
            target_name, item_name = args
            item = player.search_item(item_name, include_location=False)
            if not item:
                print("You don't have that.")
                return
        give_stuff([item], target_name)


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
        verbs = ctx["verbs"]
        verb_help = {}   # verb -> [list of abbrs]
        for verb in verbs:
            verb_help[verb] = []
        abbrevs = dict(abbreviations)
        for abbr, verb in abbreviations.items():
            if verb in verb_help:
                verb_help[verb].append(abbr)
                del abbrevs[abbr]
        cmds_help = []
        for verb, abbrs in verb_help.items():
            if abbrs:
                verb += "/" + "/".join(abbrs)
            cmds_help.append(verb)
        print("Available commands:")
        print(", ".join(cmds_help))
        print("Abbreviations:")
        print(", ".join(sorted("%s=%s" % (a, v) for a, v in abbrevs.items())))
        print("Pick up/put down are aliases for take/drop.")


@cmd("look")
def do_look(player, verb, arg, **ctx):
    print = player.tell
    if arg:
        # look <direction> is the only thing we support, the rest should be done with examine
        if arg in player.location.exits:
            print(player.location.exits[arg].description)
        elif arg in abbreviations and abbreviations[arg] in player.location.exits:
            print(player.location.exits[abbreviations[arg]].description)
        else:
            raise ParseError("Maybe you should examine that instead.")
    else:
        print(player.look())


@cmd("examine", "inspect")
def do_examine(player, verb, arg, **ctx):
    print = player.tell
    if not arg:
        raise ParseError("Examine what?")
    obj = player.location.search_living(arg)
    if obj:
        if "wizard" in player.privileges:
            print(repr(obj))
        print("This is %s." % obj.title)
        if obj.description:
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
        return
    obj = player.search_item(arg)
    if obj:
        if "wizard" in player.privileges:
            print(repr(obj))
        if obj in player:
            print("You're carrying %s." % languagetools.a(obj.title))
        else:
            print("You see %s." % languagetools.a(obj.title))
        if obj.description:
            print(obj.description)
        if getattr(obj, "public_inventory", False):
            if obj.inventory:
                print("It contains:", languagetools.join(item.title for item in obj.inventory))
            else:
                print("It's empty.")
        return
    if arg in player.location.exits:
        print("It seems you can go there:")
        print(player.location.exits[arg].description)
    elif arg in abbreviations and abbreviations[arg] in player.location.exits:
        print("It seems you can go there:")
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
            if name == "all":
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


def print_item_removal(player, item, container, print_parentheses=True):
    if print_parentheses:
        player.tell("(you take the %s from the %s)" % (item.name, container.name))
    else:
        player.tell("You take the %s from the %s." % (item.name, container.name))
    player.location.tell("{player} takes the {item} from the {container}.".format(
        player=languagetools.capital(player.title), item=item.name, container=container.name), exclude_living=player)
