"""
Wizard commands.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division
import inspect
import copy
import functools
import sys
from ..errors import SecurityViolation, ParseError, ActionRefused
from .. import base
from .. import lang
from .. import npc
from .. import rooms
from .. import util

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
    """List the contents of a module path under the mudlib tree (try .items.basic)"""
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
    classes = [x[0] for x in m_items if type(x[1]) is type and issubclass(x[1], base.MudObject)]
    items = [x[0] for x in m_items if isinstance(x[1], base.Item)]
    livings = [x[0] for x in m_items if isinstance(x[1], base.Living)]
    locations = [x[0] for x in m_items if isinstance(x[1], base.Location)]
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
    """Clone an item or living directly from the room or inventory, or from an object in the module path"""
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
        obj = player.search_item(path, include_containers_in_inventory=False) or player.location.search_living(path)
    # clone it
    if not obj:
        raise ActionRefused("Object not found")
    elif isinstance(obj, base.Item):
        item = copy.deepcopy(obj)
        player.insert(item, player)
        print("Cloned: " + repr(item))
        player.location.tell("{player} conjures up {item}, and quickly pockets it."
                             .format(player=lang.capital(player.title),
                                     item=lang.a(item.title)),
                             exclude_living=player)
    elif isinstance(obj, npc.NPC):
        clone = copy.deepcopy(obj)
        clone.cpr()  # (re)start heartbeat
        print("Cloned: " + repr(clone))
        player.location.tell("{player} summons {npc}."
                             .format(player=lang.capital(player.title),
                                     npc=lang.a(clone.title)),
                             exclude_living=player)
        player.location.insert(clone, player)
    else:
        raise ActionRefused("Can't clone " + lang.a(obj.__class__.__name__))


@wizcmd("destroy")
def do_destroy(player, verb, arg, **ctx):
    """Destroys an object or creature."""
    print = player.tell
    if not arg:
        raise ParseError("Destroy what?")
    # @todo: ask for confirmation (async)
    victim = player.search_item(arg, include_containers_in_inventory=False)
    if victim:
        if victim in player:
            player.remove(victim, player)
        else:
            player.location.remove(victim, player)
        victim.destroy(ctx)
    else:
        # maybe there's a living here instead
        victim = player.location.search_living(arg)
        if victim:
            if victim is player:
                raise ActionRefused("You can't destroy yourself, are you insane?!")
            victim.tell("%s creates a black hole that sucks you up. You're utterly destroyed." % lang.capital(player.title))
            victim.destroy(ctx)
        else:
            raise ActionRefused("There's no %s here." % arg)
    print("You destroyed %r." % victim)
    player.location.tell("{player} makes some gestures and a tiny black hole appears.\n"
                         "{victim} disappears in it, and the black hole immediately vanishes."
                         .format(player=lang.capital(player.title),
                                 victim=lang.capital(victim.title)),
                         exclude_living=player)


@wizcmd("pdb")
def do_pdb(player, verb, rest, **ctx):
    """Starts a Python debugging session."""
    import pdb
    pdb.set_trace()   # @todo: remove this when going multiuser (I don't think you can have a synchronous debug session anymore)


@wizcmd("wiretap")
def do_wiretap(player, verb, arg, **ctx):
    """Adds a wiretap to something to overhear the messages they receive.
'wiretap .' taps the room, 'wiretap name' taps a creature with that name,
'wiretap' shows all your taps, 'wiretap -clear' gets rid of all taps."""
    print = player.tell
    if not arg:
        print("Installed wiretaps:", ", ".join(str(tap) for tap in player.installed_wiretaps) or "none")
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
            raise ActionRefused(arg + " isn't here.")


@wizcmd("teleport")
def do_teleport(player, verb, args, **ctx):
    """Teleport to a location or creature, or teleport a creature to you.
'teleport [to] .module.path.to.object' teleports [to] that object (location or creature)
'teleport [to] playername' teleports [to] that player,
'teleport [to] @start' teleports you to the starting location for wizards."""
    if not args:
        raise ActionRefused("Teleport what to where?")
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
            if isinstance(target, base.Living):
                target = target.location  # teleport to target living's location
            if not isinstance(target, base.Location):
                raise ActionRefused("Can't determine location to teleport to.")
            teleport_to(player, target)
        else:
            if isinstance(target, base.Location):
                raise ActionRefused("Can't teleport a room here, maybe you wanted to teleport TO somewhere?")
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
                         lang.capital(player.title), exclude_living=player)
    player.location.tell("%s jumps into the portal, which quickly closes behind %s." %
                         (lang.capital(player.subjective), player.objective), exclude_living=player)
    player.move(location)
    print("You've been teleported.")
    print(player.look())
    location.tell("Suddenly, a shimmering portal opens!", exclude_living=player)
    location.tell("%s jumps out, and the portal quickly closes behind %s." %
                  (lang.capital(player.title), player.objective), exclude_living=player)


def teleport_someone_to_player(who, player):
    """helper function for teleport command, to teleport someone to the player"""
    who.location.tell("Suddenly, a shimmering portal opens!")
    room_msg = "%s is sucked into it, and the portal quickly closes behind %s." % (lang.capital(who.title), who.objective)
    who.location.tell(room_msg, specific_targets=[who], specific_target_msg="You are sucked into it!")
    who.move(player.location)
    player.location.tell("%s makes some gestures and a portal suddenly opens." %
                         lang.capital(player.title), exclude_living=who)
    player.location.tell("%s tumbles out of it, and the portal quickly closes again." %
                         lang.capital(who.title), exclude_living=who)


@wizcmd("reload")
def do_reload(player, verb, path, **ctx):
    """Reload the given module (Python)."""
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
    """Move something or someone to another location or creature.
This may work around possible restrictions that could prevent stuff
to be moved around normally. For instance you could use it to pick up
items that are normally fixed in place (move item to playername)."""
    print = player.tell
    thing_name, _, target_name = arg.partition(" ")
    target_name = target_name.strip()
    if not thing_name or not target_name:
        raise ParseError("Move what where?")
    thing = player.search_item(thing_name, include_location=False, include_containers_in_inventory=False)
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
        raise ActionRefused("* use 'teleport' instead to move livings around.")
    if target_name == ".":
        # current room is the target
        target = player.location
        target_type = "location"
    else:
        target = player.search_item(target_name, include_location=True, include_containers_in_inventory=False)
        target_type = "item"
        if not target:
            target = player.location.search_living(target_name)
            target_type = "living"
            if not target:
                raise ActionRefused("There's no %s here." % target_name)
    if thing is target:
        raise ActionRefused("You can't move things inside themselves.")
    thing.move(thing_container, target, player, wiz_force=True)
    print("Moved %s (%s) from %s (%s) to %s (%s)." %
        (thing.name, thing_type, thing_container.name, thing_container_type, target.name, target_type))
    player.location.tell("%s moved %s into %s." %
        (lang.capital(player.title), thing.title, target.title), exclude_living=player)


@wizcmd("debug")
def do_debug(player, verb, name, **ctx):
    """Dumps the internal attribute values of a location (.), item or creature."""
    print = player.tell
    if not name:
        raise ParseError("Debug what?")
    if name == ".":
        obj, container = player.location, None
    else:
        obj, container = player.locate_item(name, include_inventory=True, include_location=True, include_containers_in_inventory=True)
    if not obj:
        obj, container = player.location.search_living(name), player.location
    if not obj:
        raise ActionRefused("Can't find %s." % name)
    print(repr(obj))
    if container:
        util.print_object_location(player, obj, container, False)
    for varname, value in sorted(vars(obj).items()):
        print(".%s: %r" % (varname, value))


@wizcmd("set")
def do_set(player, verb, args, **ctx):
    """Set an internal attribute of a location (.), object or creature to a new value.
Usage is: set xxx.fieldname=value (you can use Python literals only)"""
    print = player.tell
    args = args.split("=")
    if len(args) != 2:
        raise ParseError("Set what? (usage: set xxx.fieldname=value)")
    name, field = args[0].split(".")
    if name == ".":
        obj = player.location
    else:
        obj = player.search_item(name, include_inventory=True, include_location=True)
    if not obj:
        obj = player.location.search_living(name)
    if not obj:
        raise ActionRefused("Can't find %s." % name)
    print(repr(obj))
    import ast
    value = ast.literal_eval(args[1])
    expected_type = type(getattr(obj, field))
    if expected_type is type(value):
        setattr(obj, field, value)
        print("Field set: %s.%s = %r" % (name, field, value))
    else:
        raise ActionRefused("Data type mismatch, expected %s." % expected_type)
