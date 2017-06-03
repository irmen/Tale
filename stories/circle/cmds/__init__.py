"""
Package containing new and overridden game commands.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from zones import make_location, make_item, make_mob

from tale import lang, util
from tale.cmds import wizcmd
from tale.cmds.wizard import teleport_to
from tale.errors import ActionRefused, ParseError
from tale.player import Player
from tale.base import ParseResult


@wizcmd("cvgo")
def go_vnum(player: Player, parsed: ParseResult, ctx: util.Context) -> None:
    """Go to a specific circlemud room, given by its circle-vnum."""
    if len(parsed.args) != 1:
        raise ParseError("You have to give the rooms' circle-vnum.")
    vnum = int(parsed.args[0])
    try:
        room = make_location(vnum)
    except KeyError:
        raise ActionRefused("No room with that circle-vnum exists.")
    teleport_to(player, room)


@wizcmd("cvnum")
def show_vnum(player: Player, parsed: ParseResult, ctx: util.Context) -> None:
    """Show the circle-vnum of a location (.) or an object/living,
    or when you provide a circle-vnum as arg, show the object(s) with that circle-vnum."""
    if not parsed.args:
        raise ParseError("From what should I show the circle-vnum?")
    name = parsed.args[0]
    if name == ".":
        obj = player.location
    elif parsed.who_order:
        obj = parsed.who_order[0]
    else:
        try:
            vnum = int(parsed.args[0])
        except ValueError as x:
            raise ActionRefused(str(x))
        objects = []
        try:
            objects.append(make_item(vnum))
        except KeyError:
            pass
        try:
            objects.append(make_location(vnum))
        except KeyError:
            pass
        try:
            objects.append(make_mob(vnum))
        except KeyError:
            pass
        player.tell("Objects with circle-vnum %d:" % vnum + " " + (lang.join(str(o) for o in objects) or "none"))
        return
    try:
        vnum = obj.circle_vnum   # type: ignore
        player.tell("Circle-Vnum of %s = %d." % (obj, vnum))
    except AttributeError:
        player.tell(str(obj) + " has no circle-vnum.")


@wizcmd("cvspawn")
def spawn_vnum(player: Player, parsed: ParseResult, ctx: util.Context) -> None:
    """Spawn an item or monster with the given circle-vnum (or both if the circle-vnum is the same)."""
    if len(parsed.args) != 1:
        raise ParseError("You have to give the item or monster's circle-vnum.")
    vnum = int(parsed.args[0])
    try:
        item = make_item(vnum)
    except KeyError:
        player.tell("There's no item with that circle-vnum.")
    else:
        player.tell("Spawned " + repr(item) + " (into your inventory)")
        item.move(player, actor=player)
    try:
        mob = make_mob(vnum)
    except KeyError:
        player.tell("There's no monster with that circle-vnum.")
    else:
        player.tell("Spawned " + repr(mob) + " (into your current location)")
        mob.move(player.location, actor=player)
