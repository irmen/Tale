"""
Wizard commands.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function
import inspect
import copy
import functools
import sys
from ..errors import SecurityViolation, ParseError, ActionRefused
from .. import baseobjects
from .. import languagetools
from .. import npc
from .. import rooms

all_commands = {}


def wizcmd(command):
    """decorator to add the command to the global dictionary of commands, with a privilege check wrapper"""
    def wizcmd2(func):
        @functools.wraps(func)
        def makewizcmd(player, verb, rest, **ctx):
            if not "wizard" in player.privileges:
                raise SecurityViolation("Wizard privilege required for verb " + verb)
            return func(player, verb, rest, **ctx)
        if command in all_commands:
            raise ValueError("Command defined more than once: " + command)
        all_commands[command] = makewizcmd
        return makewizcmd
    return wizcmd2


@wizcmd("ls")
def do_ls(player, verb, path, **ctx):
    print = player.tell
    if not path.startswith("."):
        raise ActionRefused("Path must start with '.'")
    try:
        module_name = "mudlib"
        if len(path) > 1:
            module_name += path
        __import__(module_name)
        module = sys.modules[module_name]
    except (ImportError, ValueError):
        raise ActionRefused("There's no module named " + path)
    print("<%s>" % path)
    m_items = vars(module).items()
    modules = [x[0] for x in m_items if inspect.ismodule(x[1])]
    classes = [x[0] for x in m_items if type(x[1]) is type and issubclass(x[1], baseobjects.MudObject)]
    items = [x[0] for x in m_items if isinstance(x[1], baseobjects.Item)]
    livings = [x[0] for x in m_items if isinstance(x[1], baseobjects.Living)]
    locations = [x[0] for x in m_items if isinstance(x[1], baseobjects.Location)]
    if locations:
        print("Locations: " + ", ".join(locations))
    if livings:
        print("Livings: " + ", ".join(livings))
    if items:
        print("Items: " + ", ".join(items))
    if modules:
        print("Submodules: " + ", ".join(modules))
    if classes:
        print("Classes: " + ", ".join(classes))


@wizcmd("clone")
def do_clone(player, verb, path, **ctx):
    print = player.tell
    if not path:
        raise ParseError("Clone what?")
    if path.startswith("."):
        # find an item somewhere in a module path
        path, objectname = path.rsplit(".", 1)
        if not objectname:
            raise ActionRefused("Invalid object path")
        try:
            module_name = "mudlib"
            if len(path) > 1:
                module_name += path
            __import__(module_name)
            module = sys.modules[module_name]
            obj = getattr(module, objectname, None)
        except (ImportError, ValueError):
            raise ActionRefused("There's no module named " + path)
    else:
        # find an object or living from the inventory or the room
        obj = player.search_item(path) or player.location.search_living(path)
    # clone it
    if not obj:
        raise ActionRefused("Object not found")
    elif isinstance(obj, baseobjects.Item):
        item = copy.deepcopy(obj)
        player.inventory.add(item)
        print("Cloned: " + repr(item))
        player.location.tell("{player} conjures up {item}, and quickly pockets it."
                             .format(player=languagetools.capital(player.title),
                                     item=languagetools.a(item.title)),
                             exclude_living=player)
    elif isinstance(obj, npc.NPC):
        clone = copy.deepcopy(obj)
        clone.cpr()  # (re)start heartbeat
        print("Cloned: " + repr(clone))
        player.location.tell("{player} summons {npc}."
                             .format(player=languagetools.capital(player.title),
                                     npc=languagetools.a(clone.title)),
                             exclude_living=player)
        player.location.enter(clone)
    else:
        raise ActionRefused("Can't clone " + languagetools.a(obj.__class__.__name__))


@wizcmd("destroy")
def do_destroy(player, verb, arg, **ctx):
    # @todo: ask for confirmation (async)
    print = player.tell
    if not arg:
        raise ParseError("Destroy what?")
    victim = player.search_item(arg)
    if victim:
        if victim in player:
            player.inventory.remove(victim)
        else:
            player.location.leave(victim)
        victim.destroy(ctx)
    else:
        # maybe there's a living here instead
        victim = player.location.search_living(arg)
        if victim:
            if victim is player:
                raise ActionRefused("You can't destroy yourself, are you insane?!")
            victim.tell("%s creates a black hole that sucks you up. You're utterly destroyed." % languagetools.capital(player.title))
            victim.destroy(ctx)
        else:
            raise ActionRefused("There's no %s here." % arg)
    print("You destroyed %r." % victim)
    player.location.tell("{player} makes some gestures and a tiny black hole appears.\n"
                         "{victim} disappears in it, and the black hole immediately vanishes."
                         .format(player=languagetools.capital(player.title),
                                 victim=languagetools.capital(victim.title)),
                         exclude_living=player)


@wizcmd("pdb")
def do_pdb(player, verb, rest, **ctx):
    import pdb
    pdb.set_trace()   # @todo: remove this when going multiuser (I don't think you can have a synchronous debug session anymore)


@wizcmd("wiretap")
def do_wiretap(player, verb, arg, **ctx):
    print = player.tell
    if not arg:
        print("Installed wiretaps:", ", ".join(str(tap) for tap in player.installed_wiretaps) or "none")
        print("Use 'wiretap .' or 'wiretap living' to tap the room or a living.")
        print("Use 'wiretap -clear' to remove all your wiretaps.")
        return
    if arg == ".":
        player.create_wiretap(player.location)
        print("Wiretapped room '%s'." % player.location.name)
    elif arg == "-clear":
        player.installed_wiretaps.clear()
        print("All wiretaps removed.")
    else:
        living = player.location.search_living(arg)
        if living:
            if living is player:
                raise ActionRefused("Can't wiretap yourself.")
            player.create_wiretap(living)
            print("Wiretapped %s." % living.name)
        else:
            raise ActionRefused(arg, "isn't here.")


@wizcmd("teleport")
def do_teleport(player, verb, args, **ctx):
    if not args:
        raise ActionRefused("Usage: teleport [to] [.module.path.to.object | playername | @start]")
    teleport_self = False
    if args.startswith("to "):
        teleport_self = True
        args = args.split(None, 1)[1]
    if args.startswith("."):
        # teleport player to a location somewhere in a module path
        path, objectname = args.rsplit(".", 1)
        if not objectname:
            raise ActionRefused("Invalid object path")
        try:
            module_name = "mudlib"
            if len(path) > 1:
                module_name += path
            __import__(module_name)
            module = sys.modules[module_name]
        except (ImportError, ValueError):
            raise ActionRefused("There's no module named " + path)
        target = getattr(module, objectname, None)
        if not target:
            raise ActionRefused("Object not found")
        if teleport_self:
            if isinstance(target, baseobjects.Living):
                target = target.location  # teleport to target living's location
            if not isinstance(target, baseobjects.Location):
                raise ActionRefused("Can't determine location to teleport to.")
            teleport_to(player, target)
        else:
            teleport_someone_to_player(target, player)
    else:
        # target is a player (or @start - the wizard starting location)
        if args == "@start":
            teleport_to(player, rooms.STARTLOCATION_WIZARD)
        else:
            target = ctx["driver"].search_player(args)
            if not target:
                raise ActionRefused("%s isn't here." % args)
            if teleport_self:
                teleport_to(player, target.location)
            else:
                teleport_someone_to_player(target, player)


def teleport_to(player, location):
    """helper function for teleport command, to teleport the player somewhere"""
    print = player.tell
    player.location.tell("%s makes some gestures and a portal suddenly opens." %
                         languagetools.capital(player.title), exclude_living=player)
    player.location.tell("%s jumps into the portal, which quickly closes behind %s." %
                         (languagetools.capital(player.subjective), player.objective), exclude_living=player)
    player.move(location, force_and_silent=True)
    print("You've been teleported.")
    print(player.look())
    location.tell("Suddenly, a shimmering portal opens!", exclude_living=player)
    location.tell("%s jumps out, and the portal quickly closes behind %s." %
                  (languagetools.capital(player.title), player.objective), exclude_living=player)


def teleport_someone_to_player(who, player):
    """helper function for teleport command, to teleport someone to the player"""
    who.location.tell("Suddenly, a shimmering portal opens!")
    room_msg = "%s is sucked into it, and the portal quickly closes behind %s." % (languagetools.capital(who.title), who.objective)
    who.location.tell(room_msg, specific_targets=[who], specific_target_msg="You are sucked into it!")
    who.move(player.location, force_and_silent=True)
    player.location.tell("%s makes some gestures and a portal suddenly opens." %
                         languagetools.capital(player.title), exclude_living=who)
    player.location.tell("%s tumbles out of it, and the portal quickly closes again." %
                         languagetools.capital(who.title), exclude_living=who)


@wizcmd("reload")
def do_reload(player, verb, path, **ctx):
    print = player.tell
    if not path.startswith("."):
        raise ActionRefused("Path must start with '.'")
    try:
        module_name = "mudlib"
        if len(path) > 1:
            module_name += path
        __import__(module_name)
        module = sys.modules[module_name]
    except (ImportError, ValueError):
        raise ActionRefused("There's no module named " + path)
    import imp
    imp.reload(module)
    print("Module has been reloaded:", module.__name__)


@wizcmd("move")
def do_move(player, verb, arg, **ctx):
    print = player.tell
    thing_name, _, target_name = arg.partition(" ")
    target_name = target_name.strip()
    if not thing_name or not target_name:
        raise ParseError("Move what where?")
    thing = player.search_item(thing_name, include_location=False)
    thing_type = "item"
    thing_container = player
    thing_container_type = "living"
    if not thing:
        thing = player.search_item(thing_name, include_inventory=False, include_location=True)
        thing_type = "item"
        thing_container = player.location
        thing_container_type = "location"
    if not thing:
        thing = player.location.search_living(thing_name)
        thing_type = "living"
        thing_container = player.location
        thing_container_type = "location"
    if not thing:
        raise ActionRefused("There's no %s here." % thing_name)
    if thing_type == "living":
        raise ActionRefused("* move can't yet move livings around, it will screw up their location. Sorry.")  # @todo fix moving livings
    if target_name == ".":
        # current room is the target
        target = player.location
        target_type = "location"
    else:
        target = player.search_item(target_name, include_location=True)
        target_type = "item"
        if not target:
            target = player.location.search_living(target_name)
            target_type = "living"
            if not target:
                raise ActionRefused("There's no %s here." % target_name)
    if thing is target:
        raise ActionRefused("You can't move things inside themselves.")
    move_something(thing, thing_container, thing_container_type, target, target_type)
    print("Moved %s (%s) from %s (%s) to %s (%s)." %
        (thing.name, thing_type, thing_container.name, thing_container_type, target.name, target_type))


def move_something(thing, thing_container, thing_container_type, destination, destination_type):
    if destination_type == "item" and not isinstance(destination, baseobjects.Container):
        raise ActionRefused("Destination item is not a bag/container and can't hold anything.")
    # remove the thing from where it is now
    if thing_container_type == "location":
        thing_container.leave(thing, force_and_silent=True)
    else:
        thing_container.inventory.remove(thing)  # all other types: just pop it from their inventory
    # move the thing to its destination
    if destination_type == "location":
        destination.enter(thing, force_and_silent=True)
    else:
        destination.inventory.add(thing)  # all other types: just chuck it in their inventory
    # @todo: when moving livings, it screws up their location.
    # This needs a complex fix (hierarchic container lookup bubbling until we reach a Location object?)
