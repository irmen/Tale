"""
Package containing new and overridden game commands.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from zones import make_location, make_item, make_mob

from tale import lang, util
from tale.cmds.decorators import wizcmd
from tale.cmds.wizard import teleport_to
from tale.driver import Commands
from tale.errors import ActionRefused, ParseError
from tale.parseresult import ParseResult
from tale.player import Player


def register_all(cmd_processor: Commands) -> None:
    cmd_processor.add("!vgo", go_vnum, "wizard")
    cmd_processor.add("!vnum", show_vnum, "wizard")
    cmd_processor.add("!vspawn", spawn_vnum, "wizard")


@wizcmd
def go_vnum(player: Player, parsed: ParseResult, ctx: util.Context) -> None:
    """Go to a specific circlemud room, given by its vnum."""
    if len(parsed.args) != 1:
        raise ParseError("You have to give the rooms' vnum.")
    vnum = int(parsed.args[0])
    try:
        room = make_location(vnum)
    except KeyError:
        raise ActionRefused("No room with that vnum exists.")
    teleport_to(player, room)


@wizcmd
def show_vnum(player: Player, parsed: ParseResult, ctx: util.Context) -> None:
    """Show the vnum of a location (.) or an object/living,
    or when you provide a vnum as arg, show the object(s) with that vnum."""
    if not parsed.args:
        raise ParseError("From what should I show the vnum?")
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
        player.tell("Objects with vnum %d:" % vnum + " " + (lang.join(str(o) for o in objects) or "none"))
        return
    try:
        vnum = obj.circle_vnum   # type: ignore
        player.tell("Vnum of %s = %d." % (obj, vnum))
    except AttributeError:
        player.tell(str(obj) + " has no vnum.")


@wizcmd
def spawn_vnum(player: Player, parsed: ParseResult, ctx: util.Context) -> None:
    """Spawn an item or monster with the given vnum (or both if the vnum is the same)."""
    if len(parsed.args) != 1:
        raise ParseError("You have to give the rooms' vnum.")
    vnum = int(parsed.args[0])
    try:
        item = make_item(vnum)
    except KeyError:
        player.tell("There's no item with that vnum.")
    else:
        player.tell("Spawned " + repr(item) + " (into your inventory)")
        item.move(player, actor=player)
    try:
        mob = make_mob(vnum)
    except KeyError:
        player.tell("There's no mob with that vnum.")
    else:
        player.tell("Spawned " + repr(mob) + " (into your current location)")
        mob.move(player.location, actor=player)
