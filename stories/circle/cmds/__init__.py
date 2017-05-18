"""
Package containing new and overridden game commands.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from tale.cmds.decorators import wizcmd
from tale.errors import ActionRefused, ParseError
from zones import make_location, make_item, make_mob
from tale import lang, util
from tale.driver import Commands
from tale.player import Player
from tale.parseresult import ParseResult


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
    player.tell("Teleporting to room {}...".format(room))
    player.tell("\n")
    player.move(room, actor=player)
    player.look()


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
        player.tell("Objects with vnum %d:" % vnum, lang.join(str(o) for o in objects))
        return
    try:
        vnum = obj.vnum
        player.tell("Vnum of %s = %d." % (obj, vnum))
    except AttributeError:
        player.tell("{} has no vnum.".format(obj))


@wizcmd
def spawn_vnum(player: Player, parsed: ParseResult, ctx: util.Context) -> None:
    """Spawn an item or monster with the given vnum (or both if the vnum is the same)."""
    if len(parsed.args) != 1:
        raise ParseError("You have to give the rooms' vnum.")
    vnum = int(parsed.args[0])
    spawned = []
    try:
        spawned.append(make_item(vnum))
    except KeyError:
        pass
    try:
        spawned.append(make_mob(vnum))
    except KeyError:
        pass
    for obj in spawned:
        player.tell("Spawned", obj)
        obj.move(player.location, actor=player)
