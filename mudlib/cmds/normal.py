"""
Normal player commands.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division
import inspect
import datetime
import random
from .. import lang
from .. import soul
from .. import races
from .. import util
from .. import base
from ..errors import ParseError, ActionRefused, SessionExit, RetrySoulVerb

all_commands = {}
abbreviations = {}   # will be injected


def cmd(command, *aliases):
    """decorator to add the command to the global dictionary of commands"""
    def cmd2(func):
        if command in all_commands:
            raise ValueError("command defined more than once: " + command)
        argspec = inspect.getargspec(func)
        if argspec.args == ["player", "parsed"] and argspec.varargs is None and argspec.keywords == "ctx" and argspec.defaults is None:
            all_commands[command] = func
            for alias in aliases:
                if alias in all_commands:
                    raise ValueError("command defined more than once: " + alias)
                all_commands[alias] = func
            return func
        else:
            raise SyntaxError("invalid cmd function signature for: " + func.__name__)
    return cmd2


@cmd("inventory")
def do_inventory(player, parsed, **ctx):
    """Show the items you are carrying."""
    print = player.tell
    if parsed.who and "wizard" in player.privileges:
        # wizards may look at the inventory of everything else
        other = parsed.who.pop()
        if isinstance(other, base.Living):
            # show another living's inventory
            name = lang.capital(other.title)
            inventory = other.inventory()
            if inventory:
                print(name, "is carrying:")
                for item in inventory:
                    print("  " + item.title)
            else:
                print(name, "is carrying nothing.")
            print("Money in possession: %s." % util.money_display(other.money))
            return
        elif isinstance(other, base.Item):
            # show item's inventory
            inventory = other.inventory()
            if inventory:
                print("It contains:")
                for item in inventory:
                    print("  " + item.title)
            else:
                print("It's empty.")
        else:
            raise ActionRefused("Can't find %s." % other.name)
    else:
        inventory = player.inventory()
        if inventory:
            print("You are carrying:")
            for item in inventory:
                print("  " + item.title)
        else:
            print("You are carrying nothing.")
        print("Money in possession: %s." % util.money_display(player.money, zero_msg="you are broke"))


@cmd("locate", "search")
def do_locate(player, parsed, **ctx):
    """Try to locate a specific item, creature or player."""
    print = player.tell
    if not parsed.args:
        raise ParseError("Locate what/who?")
    if len(parsed.args) > 1 or len(parsed.who) > 1:
        raise ParseError("Can only search for one thing at a time.")
    name = parsed.args[0]
    print("You look around to see if you can locate %s." % name)
    player.tell_others("{Title} looks around.")
    if parsed.who:
        thing = parsed.who.pop()
        if thing is player:
            print("You are here, in %s." % player.location.name)
            return
        if thing.name.lower() != name.lower() and name.lower() in thing.aliases:
            print("(by %s you probably mean %s)" % (name, thing.name))
        if thing in player.location:
            if isinstance(thing, base.Living):
                print("%s is here next to you." % lang.capital(thing.title))
            else:
                util.print_object_location(player, thing, player.location, False)
        elif thing in player:
            util.print_object_location(player, thing, player, False)
        else:
            print("You can't find that.")
    else:
        # The default parser checks inventory and location, but it didn't find anything.
        # Check inside containers in the player's inventory instead.
        item, container = player.locate_item(name, include_inventory=False, include_location=False, include_containers_in_inventory=True)
        if item:
            if item.name.lower() != name.lower() and name.lower() in item.aliases:
                print("(by %s you probably mean %s)" % (name, item.name))
            util.print_object_location(player, item, container, False)
        else:
            otherplayer = ctx["driver"].search_player(name)  # global player search
            if otherplayer:
                player.tell("%s is playing, %s is currently in '%s'." % (lang.capital(otherplayer.title), otherplayer.subjective, otherplayer.location.name))
            else:
                print("You can't find that.")


@cmd("drop")
def do_drop(player, parsed, **ctx):
    """Drop an item (or all items) you are carrying."""
    print = player.tell
    if not parsed.args:
        raise ParseError("Drop what?")

    def drop_stuff(items, container):
        items = list(items)
        refused = []
        for item in items:
            try:
                item.move(container, player.location, player)
                if container is not player and container in player:
                    print_item_removal(player, item, container)
            except ActionRefused as x:
                refused.append((item, str(x)))
        for item, message in refused:
            items.remove(item)
            print(message)
        if items:
            items_str = lang.join(lang.a(item.title) for item in items)
            print("You drop %s." % items_str)
            player.tell_others("{Title} drops %s." % items_str)
        else:
            print("You didn't drop anything.")

    arg = parsed.args[0]
    if arg == "all":
        if player.inventory_size() == 0:
            raise ActionRefused("You're not carrying anything.")
        else:
            # @todo: ask confirmation to drop everything
            drop_stuff(player.inventory(), player)
    else:
        # drop a single item from the inventory (or a container in the inventory)
        if parsed.who:
            item = parsed.who.pop()
            if item in player:
                drop_stuff([item], player)
            else:
                raise ActionRefused("You can't drop that.")
        else:
            item, container = player.locate_item(arg, include_location=False)
            if item:
                if container is not player:
                    util.print_object_location(player, item, container)
                drop_stuff([item], container)
            else:
                raise ActionRefused("You don't have %s." % lang.a(arg))


@cmd("empty")
def do_empty(player, parsed, **ctx):
    """Remove the contents from an object."""
    print = player.tell
    if len(parsed.args) != 1:
        raise ParseError("Empty what?")
    if len(parsed.who) > 1:
        raise ParseError("Please be more specific, only empty one thing at a time.")
    container = parsed.who.pop()
    if not isinstance(container, base.Container):
        raise ActionRefused("You can't take anything from %s." % container.title)
    if container in player.location:
        # move the contents to the room
        target = player.location
        action = "dropped"
    elif container in player:
        # move the contents to the player's inventory
        target = player
        action = "took"
    else:
        raise ParseError("You can't seem to empty that.")
    items_moved = []
    for item in container.inventory():
        try:
            item.allow_move(player)
        except ActionRefused as x:
            print(str(x))
        else:
            item.move(container, target, player)
            items_moved.append(item.title)
    if items_moved:
        itemnames = lang.join(items_moved)
        print("You %s: %s." % (action, itemnames))
        player.tell_others("{Title} %s: %s." % (action, itemnames))
    else:
        print("You %s nothing." % action)


@cmd("put", "place")
def do_put(player, parsed, **ctx):
    """Put an item (or all items) into something else.
If you're not carrying the item, you will first pick it up."""
    print = player.tell
    if len(parsed.args) < 2:
        raise ParseError("Put what where?")
    if parsed.args[0] == "all":
        if player.inventory_size() == 0:
            raise ActionRefused("You're not carrying anything.")
        if len(parsed.args) != 2:
            raise ParseError("Put what where?")
        # @todo: ask confirmation to put everything
        what = list(player.inventory())
        where = parsed.who_order[-1]   # last object is where to put the stuff
    elif parsed.unrecognized:
        raise ActionRefused("You don't see %s." % lang.join(parsed.unrecognized))
    else:
        what = parsed.who_order[:-1]
        where = parsed.who_order[-1]
    if isinstance(where, base.Living):
        raise ActionRefused("You can't put stuff in %s, try giving it to %s?" % (where.name, where.objective))
    inventory_items = []
    refused = []
    word_before = parsed.who_info[where].previous_word or "in"
    if word_before != "in" and word_before != "into":
        raise ActionRefused("You can't do that.")  # only supports put X in Y
    for item in what:
        if item is where:
            print("You can't put %s %s itself." % (item.title, word_before))
            continue
        try:
            if item in player:
                # simply use the item from the player's inventory
                item.move(player, where, player)
                inventory_items.append(item)
            elif item in player.location:
                # first take the item from the room, then move it to the target location
                item.move(player.location, player, player)
                print("You take %s." % item.title)
                player.tell_others("{Title} takes %s." % item.title)
                item.move(player, where, player)
                print("You put it in the %s." % where.name)
                player.tell_others("{Title} puts it in the %s." % where.name)
        except ActionRefused as x:
            refused.append((item, str(x)))
    for item, message in refused:
        print(message)
    if inventory_items:
        items_msg = lang.join(lang.a(item.title) for item in inventory_items)
        player.tell_others("{Title} puts %s in the %s." % (items_msg, where.name))
        print("You put {items} in the {where}.".format(items=items_msg, where=where.name))


@cmd("take", "get", "steal", "rob")
def do_take(player, parsed, **ctx):
    """Take something (or all things) from something or someone else.
Stealing and robbing is frowned upon, to say the least."""
    print = player.tell
    if len(parsed.args) == 0:
        raise ParseError("Take what?")
    if len(parsed.args) == 1:  # take thing|all
        what_names = parsed.args
        where = None
    else:
        if parsed.who:
            last_obj = parsed.who_order[-1]
            if parsed.who_info[last_obj].previous_word == "from":
                # take x[,y and z] from something
                what_names = parsed.args[:-1]
                where = last_obj
            else:
                # take x[,y and z]
                what_names = parsed.args
                where = None
        else:
            # take x[,y and z] - unrecognised names
            what_names = parsed.args
            where = None
    if where is player:
        raise ActionRefused("There's no reason to take things from yourself.")
    if isinstance(where, base.Living):
        player.tell_others("{Title} tries to steal things from %s." % where.title)
        if where.aggressive:
            where.start_attack(player)  # stealing stuff is a hostile act!
        raise ActionRefused("You can't just steal stuff from %s!" % where.title)
    elif parsed.verb == "steal" or parsed.verb == "rob":
        if where is None:
            raise ActionRefused("Steal what from whom?")
        raise ActionRefused("You can't steal stuff from an object. Try taking it instead.")
    if what_names == ["all"]:   # take ALL the things!
        if where:
            # take all stuff out of some container
            if where in player or where in player.location:
                # take all stuff from a bag that the player is carrying, or from a bag in the room.
                if where.inventory_size() > 0:
                    take_stuff(player, where.inventory(), where, where.title)
                    return
                else:
                    raise ActionRefused("There's nothing in there.")
            raise ActionRefused("Take what?")
        else:
            # take all stuff out of the room
            if not player.location.items:
                raise ActionRefused("There's nothing here to take.")
            else:
                take_stuff(player, player.location.items, player.location)
                return
    else:   # take one or more specific items
        if where:
            if where in player or where in player.location:
                # take specific items out of some container
                items_by_name = { item.name: item for item in where.inventory() }
                items_to_take = []
                for name in what_names:
                    if name in items_by_name:
                        items_to_take.append(items_by_name[name])
                    else:
                        print("There's no %s in there." % name)
                take_stuff(player, items_to_take, where, where.title)
                return
        else:
            # take things from the room
            if parsed.unrecognized:
                print("You don't see %s." % lang.join(parsed.unrecognized))
            livings = [item for item in parsed.who if item in player.location.livings]
            for living in livings:
                try_pick_up_living(player, living)
            if not player.location.items:
                raise ActionRefused("There's nothing here to take.")
            else:
                items_to_take = []
                for item in parsed.who:
                    if item in player.location.items:
                        items_to_take.append(item)
                    elif item not in player.location.livings:
                        print("There's no %s here." % item.name)
                take_stuff(player, items_to_take, player.location)
                return


def take_stuff(player, items, container, where_str=None):
    """Takes stuff and returns the number of items taken"""
    if not items:
        return 0
    print = player.tell
    if where_str:
        player_msg = "You take {items} from the %s." % where_str
        room_msg = "{{Title}} takes {items} from the %s." % where_str
    else:
        player_msg = "You take {items}."
        room_msg = "{{Title}} takes {items}."
    items = list(items)
    refused = []
    for item in items:
        try:
            item.move(container, player, player)
        except ActionRefused as x:
            refused.append((item, str(x)))
    for item, message in refused:
        print(message)
        items.remove(item)
    if items:
        items_str = lang.join(lang.a(item.title) for item in items)
        print(player_msg.format(items=items_str))
        player.tell_others(room_msg.format(items=items_str))
        return len(items)
    else:
        return 0


def try_pick_up_living(player, living):
    print = player.tell
    living_race = races.races[living.race]
    player_race = races.races[player.race]
    if player_race["size"] - living_race["size"] >= 2:
        # @todo: do an agi/str/spd/luck check to see if we can pick it up
        print("Even though {subj}'s small enough, you can't carry {obj} with you.".format(subj=living.subjective, obj=living.objective))
        if living.aggressive:
            print("Trying to pick {0} up wasn't a very good idea, you've made {0} angry!".format(living.objective))
            living.start_attack(player)
    else:
        print("You can't carry {obj} with you, {subj}'s too large.".format(subj=living.subjective, obj=living.objective))


@cmd("throw")
def do_throw(player, parsed, **ctx):
    """Throw something you are carrying at someone or something.
If you don't have it yet, you will first pick it up."""
    print = player.tell
    if len(parsed.who) != 2:
        raise ParseError("Throw what where?")
    item, where = parsed.who_order[0], parsed.who_order[1]
    if isinstance(item, base.Living):
        raise ActionRefused("You can't throw that.")
    if item in player.location:
        # first take the item from the room
        item.move(player.location, player, player)
        print("You take %s." % item.title)
        player.tell_others("{Title} takes %s." % item.title)
    # throw the item back into the room, missing the target by a hair. Possibly start combat.
    item.move(player, player.location, player)
    print("You throw the %s at %s, missing %s by a hair." % (item.title, where.title, where.objective))
    player.tell_others("{Title} throws the %s at %s, missing %s by a hair." % (item.title, where.title, where.objective))
    if isinstance(where, base.Living) and where.aggressive:
        where.start_attack(player)


@cmd("give")
def do_give(player, parsed, **ctx):
    """Give something (or all things) you are carrying to someone else."""
    if len(parsed.args) < 2:
        raise ParseError("Give what to whom?")
    if len(parsed.who) == 1:
        try:
            # first try if the first one or two words can be interpreted as an amount of money
            money = util.words_to_money(parsed.unrecognized)
            return give_money(player, money, parsed.who_order[0])
        except (ValueError, ParseError):
            pass
    if parsed.unrecognized:
        raise ParseError("You don't have %s." % lang.join(parsed.unrecognized))
    if player.inventory_size() == 0:
        raise ActionRefused("You're not carrying anything.")
    # check for "all"
    if "all" in parsed.args:
        # @todo ask for confirmation to give all
        if len(parsed.args) != 2:
            raise ParseError("Give all to who?")
        what = player.inventory()
        if parsed.args[0] == "all":
            # give all [to] living
            return give_stuff(player, what, parsed.args[1])
        else:
            # give living all
            return give_stuff(player, what, parsed.args[0])

    # give one or more specific items.
    if  len([who for who in parsed.who if isinstance(who, base.Living)]) > 1:
        # if there's more than one living, it's not clear who to give stuff to
        raise ActionRefused("It's not clear who you want to give things to.")
    if isinstance(parsed.who_order[0], base.Living):
        # if the first is a living, assume "give living [the] thing(s)"
        what = parsed.who_order[1:]
        return give_stuff(player, what, None, target=parsed.who_order[0])
    elif isinstance(parsed.who_order[-1], base.Living):
        # if the last is a living, assume "give thing(s) [to] living"
        what = parsed.who_order[:-1]
        return give_stuff(player, what, None, target=parsed.who_order[-1])
    else:
        raise ActionRefused("It's not clear who you want to give things to.")


def give_stuff(player, items, target_name, target=None):
    print = player.tell
    if not target:
        target = player.location.search_living(target_name)
    if not target:
        raise ActionRefused("%s isn't here." % target_name)
    if target is player:
        raise ActionRefused("There's no reason to give things to yourself.")
    items = list(items)
    refused = []
    for item in items:
        try:
            item.move(player, target, player)
        except ActionRefused as x:
            refused.append((item, str(x)))
    for item, message in refused:
        print(message)
        items.remove(item)
    if items:
        items_str = lang.join(lang.a(item.title) for item in items)
        player_str = lang.capital(player.title)
        room_msg = "%s gives %s to %s." % (player_str, items_str, target.title)
        target_msg = "%s gives you %s." % (player_str, items_str)
        player.location.tell(room_msg, exclude_living=player, specific_targets=[target], specific_target_msg=target_msg)
        print("You give %s %s." % (target.title, items_str))
    else:
        print("You didn't give %s anything." % target.title)


def give_money(player, amount, recipient):
    if not recipient:
        raise ActionRefused("Give it to whom?")
    if not isinstance(recipient, base.Living):
        raise ActionRefused("You can't do that.")
    if recipient is player:
        raise ActionRefused("There's no reason to give it to yourself.")
    if amount <= 0:
        player.tell("You don't give away anything.")
    elif player.money < amount:
        player.tell("You don't have that amount of wealth.")
    else:
        #@ todo ask for confirmation to give away money
        #recipient.allow_give_money(player, amount)
        player.money -= amount
        recipient.money += amount
        player.tell("You gave %s %s." % (recipient.title, util.money_display(amount)))
        player.tell_others("{Title} gave %s some money." % recipient.title)


@cmd("help")
def do_help(player, parsed, **ctx):
    """Provides some helpful information about different aspects of the game."""
    print = player.tell
    if parsed.args:
        do_what(player, parsed, **ctx)
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
        print(", ".join(sorted(cmds_help)))
        print("Abbreviations:")
        print(", ".join(sorted("%s=%s" % (a, v) for a, v in abbrevs.items())))
        print("You can get more info about all kinds of stuff by asking 'what is <topic>'.")


@cmd("look")
def do_look(player, parsed, **ctx):
    """Look around to see where you are and what's around you."""
    print = player.tell
    if parsed.args:
        arg = parsed.args[0]
        # look <direction> is the only thing we support, the rest should be done with examine
        if arg in player.location.exits:
            exit = player.location.exits[arg]
            print(exit.short_description)
            if exit.short_description != exit.long_description:
                print("Maybe you should examine it?")
        elif arg in abbreviations and abbreviations[arg] in player.location.exits:
            print(player.location.exits[abbreviations[arg]].short_description)
        else:
            raise ParseError("Maybe you should examine that instead.")
    else:
        print(player.look())


@cmd("examine", "inspect")
def do_examine(player, parsed, **ctx):
    """Examine something or someone thoroughly."""
    print = player.tell
    if not parsed.args:
        raise ParseError("Examine what or who?")
    name = parsed.args[0]
    living = player.location.search_living(name)
    if living:
        if "wizard" in player.privileges:
            print(repr(living))
        if living.name.lower() != name.lower() and name.lower() in living.aliases:
            print("(by %s you probably mean %s)" % (name, living.name))
        print("This is %s." % living.title)
        if living.description:
            print(living.description)
        race = races.races[living.race]
        if living.race == "human":
            # don't print as much info when dealing with mere humans
            msg = lang.capital("%s speaks %s." % (living.subjective, race["language"]))
            print(msg)
        else:
            print("{subj}'s a {size} {btype} {race}, and speaks {lang}.".format(
                subj=lang.capital(living.subjective),
                size=races.sizes[race["size"]],
                btype=races.bodytypes[race["bodytype"]],
                race=living.race,
                lang=race["language"]
            ))
        return
    item, container = player.locate_item(name)
    if item:
        if "wizard" in player.privileges:
            print(repr(item))
        if item.name.lower() != name.lower() and name.lower() in item.aliases:
            print("(by %s you probably mean %s)" % (name, item.name))
        if item in player:
            print("You're carrying %s." % lang.a(item.title))
        elif container and container in player:
            util.print_object_location(player, item, container)
        else:
            print("You see %s." % lang.a(item.title))
        if item.description:
            print(item.description)
        try:
            inventory = item.inventory()
        except ActionRefused:
            pass
        else:
            if inventory:
                print("It contains: %s." % lang.join(subitem.title for subitem in inventory))
            else:
                print("It's empty.")
    elif name in player.location.exits:
        print("It seems you can go there:")
        print(player.location.exits[name].long_description)
    elif name in abbreviations and abbreviations[name] in player.location.exits:
        print("It seems you can go there:")
        print(player.location.exits[abbreviations[name]].long_description)
    else:
        raise ActionRefused("%s isn't here." % name)


@cmd("stats")
def do_stats(player, parsed, **ctx):
    """Prints the gender, race and stats information of yourself, or another creature or player."""
    print = player.tell
    if not parsed.args:
        target = player
    elif len(parsed.who) == 1:
        target = parsed.who.pop()
        if not isinstance(target, base.Living):
            raise ActionRefused("That doesn't have stats.")
    else:
        raise ActionRefused("Show stats from who?")
    gender = lang.GENDERS[target.gender]
    living_type = target.__class__.__name__.lower()
    race = races.races[target.race]
    race_size = races.sizes[race["size"]]
    race_bodytype = races.bodytypes[race["bodytype"]]
    print("%s (%s) - %s %s %s" % (target.title, target.name, gender, target.race, living_type))
    print("%s %s, speaks %s, weighs ~%s kg." % (lang.capital(race_size), race_bodytype, race["language"], race["mass"]))
    if target.aggressive:
        print("%s looks aggressive." % lang.capital(target.subjective))
    print(", ".join("%s:%s" % (s[0], s[1]) for s in sorted(target.stats.items())))


@cmd("tell")
def do_tell(player, parsed, **ctx):
    """Pass a message to another player or creature that nobody else can hear.
The other player doesn't have to be in the same location as you."""
    if len(parsed.args) < 1:
        raise ActionRefused("Tell whom what?")
    # we can't use parsed.who directly, because the message could be directed to a player
    # that is not in the same location (and hence will not appear in parsed.who)
    name = parsed.args[0]
    living = player.location.search_living(name)
    if not living:
        living = ctx["driver"].search_player(name)   # is there a player around with this name?
        if not living:
            if name == "all":
                raise ActionRefused("You can't tell something to everyone, only to individuals.")
            raise ActionRefused("%s isn't here." % name)
    if living is player:
        player.tell("You're talking to yourself...")
    else:
        unparsed = parsed.unparsed[len(name):].lstrip()
        if unparsed:
            living.tell("%s tells you: %s" % (player.name, unparsed))
            player.tell("You told %s." % name)
        else:
            player.tell("Tell %s what?" % living.objective)


@cmd("emote")
def do_emote(player, parsed, **ctx):
    """Emit a custom 'emote' message literally, such as: 'emote looks stupid.' -> '<player> looks stupid."""
    if not parsed.unparsed:
        raise ParseError("Emote what message?")
    emote_msg = lang.capital(player.title) + " " + parsed.unparsed
    if not parsed.unparsed.endswith(("!", "?", ".")):
        emote_msg += "."
    player.tell("You emote: %s" % emote_msg)
    player.tell_others(emote_msg)


@cmd("yell")
def do_yell(player, parsed, **ctx):
    """Yell something. People in nearby locations will also be able to hear you."""
    print = player.tell
    if not parsed.unparsed:
        raise ActionRefused("Yell what?")
    message = parsed.unparsed
    if not parsed.unparsed.endswith((".", "!", "?")):
        message += "!"
    print("You yell:", message)
    player.tell_others("{Title} yells: %s" % message)
    util.yell_to_nearby_locations(player.location, message)  # yell this to adjacent locations as well


@cmd("say")
def do_say(player, parsed, **ctx):
    """Say something."""
    print = player.tell
    if not parsed.unparsed:
        raise ActionRefused("Say what?")
    message = parsed.unparsed
    if not parsed.unparsed.endswith((".", "!", "?")):
        message += "."
    target = ""
    if parsed.who:
        possible_target = parsed.who_order[0]
        if parsed.who_info[possible_target].previous_word == "to":
            if parsed.args[0] in (possible_target.name, possible_target.title) or parsed.args[0] in possible_target.aliases:
                target = " to " + possible_target.title
                _, _, message = message.partition(parsed.args[0])
                message = message.lstrip()
    print("You say%s: %s" % (target, message))
    player.tell_others("{Title} says%s: %s" % (target, message))


@cmd("wait")
def do_wait(player, parsed, **ctx):
    """Let time pass. You can specify how long you want to wait."""
    print = player.tell
    if parsed.who:
        who = lang.join(who.title for who in parsed.who)
        print("You wait for %s." % who)
        player.tell_others("{Title} waits for %s." % who)
        return
    if parsed.args:
        duration = util.parse_duration(parsed.args)
    else:
        duration = datetime.timedelta(minutes=10)
    if duration.total_seconds() / 3600 > 2:
        raise ActionRefused("You can't wait more than two hours at once.")
    ok, message = ctx["driver"].do_wait(duration)
    if ok:
        print("Time passes. You've waited %s." % util.duration_display(duration))
    else:
        print(message)


@cmd("quit")
def do_quit(player, parsed, **ctx):
    """Quit the game."""
    # @todo: ask for confirmation (async)
    player.tell("Goodbye, %s." % player.title)
    raise SessionExit()


def print_item_removal(player, item, container, print_parentheses=True):
    if print_parentheses:
        player.tell("(you take the %s from the %s)" % (item.name, container.name))
    else:
        player.tell("You take the %s from the %s." % (item.name, container.name))
    player.tell_others("{Title} takes the %s from the %s." % (item.name, container.name))


@cmd("who")
def do_who(player, parsed, **ctx):
    """Search for all players, a specific player or creature, and shows some information about them."""
    print = player.tell
    if parsed.args:
        if parsed.args[0] == "are":
            raise ActionRefused("Be more specific.")
        elif parsed.args[0] == "is":
            if len(parsed.args) >= 2:
                del parsed.args[0]   # skip 'is'
            else:
                raise ActionRefused("Who do you mean?")
        name = parsed.args[0].rstrip("?")
        found = False
        otherplayer = ctx["driver"].search_player(name)  # global player search
        if otherplayer:
            found = True
            player.tell("%s is playing, %s is currently in '%s'." % (lang.capital(otherplayer.title), otherplayer.subjective, otherplayer.location.name))
        try:
            do_examine(player, parsed, **ctx)
        except ActionRefused:
            pass
        if not found:
            print("Right now, there's nobody here or playing with that name.")
    else:
        # print all players
        print("All players currently in the game:")
        for player in ctx["driver"].all_players():  # list of all players
            player.tell("%s (%s): currently in '%s'." % (lang.capital(player.name), player.title, player.location.name))


@cmd("open", "close", "lock", "unlock")
def do_open(player, parsed, **ctx):
    """Do something with a door, exit or item, possibly by using something.
Example: open door,  unlock chest with key"""
    if len(parsed.args) not in (1, 2) or parsed.unrecognized:
        raise ParseError("%s what? With what?" % lang.capital(parsed.verb))
    if parsed.who:
        if isinstance(parsed.who_order[0], base.Living):
            raise ActionRefused("You can't do that with %s." % parsed.who_order[0].title)
    what_name = parsed.args[0]
    with_item_name = None
    with_item = None
    if len(parsed.args) == 2:
        with_item_name = parsed.args[1]
    what = player.search_item(what_name, include_inventory=True, include_location=True, include_containers_in_inventory=False)
    if not what:
        if what_name in player.location.exits:
            what = player.location.exits[what_name]
    if what:
        if with_item_name:
            with_item = player.search_item(with_item_name, include_inventory=True, include_location=False, include_containers_in_inventory=False)
            if not with_item:
                raise ActionRefused("You don't have %s." % lang.a(with_item_name))
        getattr(what, parsed.verb)(with_item, player)
        # no need to tell the player or the room, because the verb handler already did this
    else:
        raise ActionRefused("You don't see %s." % lang.a(what_name))


@cmd("what")
def do_what(player, parsed, **ctx):
    """Tries to answer your question about what something is.
The topics range from game commands to location exits to creature and items.
For more general help, try the 'help' command first."""
    print = player.tell
    if not parsed.args:
        raise ParseError("What do you mean?")
    if parsed.args[0] == "are":
        raise ActionRefused("Be more specific.")
    if len(parsed.args) >= 2 and parsed.args[0] == "is":
        del parsed.args[0]
    name = parsed.args[0].rstrip("?")
    if not name:
        raise ActionRefused("What do you mean?")
    found = False
    # is it an abbreviation?
    if name in abbreviations:
        name = abbreviations[name]
        print("It's an abbreviation for %s." % name)
    # is it a verb?
    if name in soul.VERBS:
        found = True
        parsed = soul.ParseResults(name)
        if name == "emote":
            parsed.who = {player}
            parsed.message = "goes wild."
            _, playermessage, roommessage, _ = player.socialize_parsed(parsed)
            name = "emote goes wild"
        else:
            parsed.who = {player}
            _, playermessage, roommessage, _ = player.socialize_parsed(parsed)
        print("It is a soul emote you can do. %s: %s" % (name, playermessage))
        if name in soul.AGGRESSIVE_VERBS:
            print("It might be regarded as offensive to certain people or beings.")
    if name in soul.BODY_PARTS:
        found = True
        parsed = soul.ParseResults("pat", who={player}, bodypart=name, message="hi")
        _, playermessage, roommessage, _ = player.socialize_parsed(parsed)
        print("It denotes a body part. pat myself %s -> %s" % (name, playermessage))
    if name in soul.ACTION_QUALIFIERS:
        found = True
        parsed = soul.ParseResults("smile", qualifier=name)
        _, playermessage, roommessage, _ = player.socialize_parsed(parsed)
        print("It is a qualifier for something. %s smile -> %s" % (name, playermessage))
    if name in lang.ADVERBS:
        found = True
        parsed = soul.ParseResults("smile", adverb=name)
        _, playermessage, roommessage, _ = player.socialize_parsed(parsed)
        print("That's an adverb you can use with the soul emote commands.")
        print("smile %s -> %s" % (name, playermessage))
    if name in races.races:
        found = True
        race = races.races[name]
        size_msg = races.sizes[race["size"]]
        body_msg = races.bodytypes[race["bodytype"]]
        lang_msg = race["language"]
        print("That's a race. They're %s, their body type is %s, and they usually speak %s." % (size_msg, body_msg, lang_msg))
    # is it a command?
    if name in ctx["verbs"]:
        found = True
        doc = ctx["verbs"][name].__doc__ or ""
        doc = doc.strip()
        if doc:
            print(doc)
        else:
            print("It is a command that you can use to perform some action.")
    # is it an exit in the current room?
    if name in player.location.exits:
        found = True
        print("It's a possible way to leave your current location: %s" % player.location.exits[name].short_description)
    # is it a npc here?
    living = player.location.search_living(name)
    if living and living.name.lower() != name.lower() and name.lower() in living.aliases:
        print("(by %s you probably mean %s)" % (name, living.name))
    if living:
        found = True
        if living is player:
            print("That's you.")
        else:
            title = lang.capital(living.title)
            gender = lang.GENDERS[living.gender]
            subj = lang.capital(living.subjective)
            if type(living) is type(player):
                print("%s is a %s %s (player). %s's here." % (title, gender, living.race, subj))
            else:
                print("%s is a %s %s. %s's here." % (title, gender, living.race, subj))
    # is it an item somewhere?
    item, container = player.locate_item(name, include_inventory=True, include_location=True, include_containers_in_inventory=True)
    if item:
        found = True
        if item.name.lower() != name.lower() and name.lower() in item.aliases:
            print("(by %s you probably mean %s)" % (name, item.name))
        print("It's an item in your vicinity. You should perhaps try to examine it.")
    if name == "soul":
        # if player is asking about the soul, give some general info
        found = True
        print("Your soul provides a large amount of 'emotes' or 'verbs' that you can do.")
        print("An emote is a command that you can do to perform something, or tell something.")
        print("They usually are just for socialization or fun and are not normally considered")
        print("considered to be a command to actually do something or interact with things.")
        print("Your soul knows %d emotes. See them all by asking about 'emotes'." % len(soul.VERBS))
        print("Your soul knows %d adverbs. You can use them by their full name, or make" % len(lang.ADVERBS))
        print("a selection by using prefixes (sa/sar/sarcas -> sarcastically).")
        print("There are all sorts of emote possibilities, for instance:")
        print("  fail sit zen  ->  You try to sit zen-likely, but fail miserably.")
        print("  pat max on the back  ->  You pat Max on the back.")
        print("  reply max sure thing  ->  You reply to Max: sure thing.")
        print("  die  ->  You fall down and play dead. (others see: XYZ falls, dead.)")
        print("  slap all  ->  You slap X, Y and Z in the face.")
        print("  slap all and me  ->  You slap yourself, X, Y and Z in the face.")
    if name == "emotes":
        # if player asks about the emotes, print all soul emote verbs
        found = True
        print("All available soul verbs (emotes):")
        lines = [""] * (len(soul.VERBS) // 5 + 1)
        index = 0
        for v in sorted(soul.VERBS):
            lines[index % len(lines)] += "  %-13s" % v
            index += 1
        for line in lines:
            print(line)
    if name in ("adverb", "averbs"):
        found = True
        print("You can use adverbs such as 'happily', 'zen', 'aggressively' with soul emotes.")
        print("Your soul knows %d adverbs. You can use them by their full name, or make" % len(lang.ADVERBS))
        print("a selection by using prefixes (sa/sar/sarcas -> sarcastically).")
    if name in ("bodypart", "bodyparts"):
        found = True
        print("You can sometimes use a specific body part with certain soul emotes.")
        print("For instance, 'hit max knee' -> You hit Max on the knee.")
        print("Recognised body parts:", ", ".join(soul.BODY_PARTS))
    if name in ("qualifier", "qualifiers"):
        found = True
        print("You can use an action qualifier to change the meaning of a soul emote.")
        print("For instance, 'fail stand' -> You try to stand up, but fail miserably.")
        print("Recognised qualifiers:", ", ".join(soul.ACTION_QUALIFIERS))
    if name in ("that", "this", "they", "them", "it"):
        raise ActionRefused("Be more specific.")
    if not found:
        # too bad, no help available :)
        print("Sorry, there is no information available about that.")


@cmd("exits")
def do_exits(player, parsed, **ctx):
    """Provides a tiny clue about possible exits from your current location."""
    if "wizard" in player.privileges:
        player.tell("The following exits are defined for your current location:")
        for direction, exit in player.location.exits.items():
            if exit.bound:
                player.tell("Exit: %s -> %s" % (direction, exit.target.name))
            else:
                player.tell("Exit: %s -> %s (unbound)" % (direction, exit.target))
    else:
        player.tell("If you want to know about the possible exits from your location,")
        player.tell("look around the room. Usually the exits are easily visible.")
        if len(player.location.exits) == 1:
            player.tell("Your current location seems to have a possible exit.")
        elif len(player.location.exits) > 1:
            player.tell("Your current location seems to have some possible exits.")
        else:
            player.tell("Your current location doesn't seem to have obvious exits.")


@cmd("use")
def do_use(player, parsed, **ctx):
    """General object use. Most of the time, you'll need to be more specific to say exactly what you want to do with it."""
    if not parsed.who:
        raise ActionRefused("Use what?")
    if len(parsed.who) > 1:
        subj = "them"
    else:
        who = parsed.who.pop()
        if isinstance(who, base.Living):
            if who is player:
                raise ActionRefused("Please be more specific: what do you want to do?")
            subj = who.objective
        else:
            subj = "it"
    raise ActionRefused("Please be more specific: what do you want to do with %s?" % subj)


@cmd("dice", "roll")
def do_dice(player, parsed, **ctx):
    """Roll a 6-sided die. Use the familiar '3d6' argument style if you want to roll multiple dice."""
    print = player.tell
    if not parsed.args:
        if parsed.verb == "roll":
            raise RetrySoulVerb
        number = 1
        sides = 6
    else:
        try:
            n, _, s = parsed.args[0].partition("d")
            number, sides = int(n), int(s)
        except ValueError:
            raise ActionRefused("What kind of dice do you want to roll (such as 3d6)?")
    if not (1 <= number <= 20 and sides >= 2):
        raise ActionRefused("Please try a bit more sensible values.")
    total, values = util.roll_die(number, sides)
    die = "a die"
    if (number, sides) != (1, 6):
        die = "%dd%d" % (number, sides)
    print("You roll %s. The result is: %d" % (die, total))
    player.tell_others("{Title} rolls %s. The result is: %d" % (die, total))
    if number > 1:
        player.location.tell("The individual rolls were: %s" % values)


@cmd("coin")
def do_coin(player, parsed, **ctx):
    """Toss a coin."""
    number, _ = util.roll_die(sides=2)
    result = ["heads", "tails"][number - 1]
    player.tell("You toss a coin. The result is: %s!" % result)
    player.tell_others("{Title} tosses a coin. The result is: %s!" % result)


@cmd("motd")
def do_motd(player, parsed, **ctx):
    """Show the message-of-the-day again."""
    motd, mtime = util.get_motd()
    if motd:
        player.tell("Message-of-the-day, last modified on %s:" % mtime)
        player.tell(motd)
    else:
        player.tell("There's currently no message-of-the-day.")


@cmd("flee")
def do_flee(player, parsed, **ctx):
    """Flee in a random or given direction, possibly escaping a combat situation."""
    print = player.tell
    exit = None
    if len(parsed.who) == 1:
        exit = parsed.who_order[0]
        if not isinstance(exit, base.Exit):
            raise ParseError("You can't flee there.")
        exit.allow_passage(player)
    elif parsed.args:
        raise ParseError("Flee where?")
    if not exit:
        # choose a random exit direction
        if not player.location.exits:
            raise ActionRefused("You can't flee anywhere!")
        exit = random.choice(list(player.location.exits.values()))
    exits_to_try = list(player.location.exits.values())
    exits_to_try.insert(0, exit)
    for exit in exits_to_try:
        try:
            exit.allow_passage(player)
            print("You flee!")
            # @todo stop combat
            player.move(exit.target)
            player.tell(player.look())
            return
        except ActionRefused:
            pass
    raise ActionRefused("You can't flee anywhere!")
