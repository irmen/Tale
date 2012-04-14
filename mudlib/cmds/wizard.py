"""
Wizard commands.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division
import inspect
import copy
import functools
import sys
from ..errors import SecurityViolation, ParseError, ActionRefused, RetrySoulVerb
from .. import base
from .. import lang
from .. import rooms

all_commands = {}


def wizcmd(command, *aliases):
    """decorator to add the command to the global dictionary of commands, with a privilege check wrapper"""
    def wizcmd2(func):
        @functools.wraps(func)
        def makewizcmd(player, parsed, **ctx):
            if not "wizard" in player.privileges:
                raise SecurityViolation("Wizard privilege required for verb " + verb)
            return func(player, parsed, **ctx)
        if command in all_commands:
            raise ValueError("Command defined more than once: " + command)
        argspec = inspect.getargspec(func)
        if argspec.args == ["player", "parsed"] and argspec.varargs is None and argspec.keywords == "ctx" and argspec.defaults is None:
            all_commands[command] = makewizcmd
            for alias in aliases:
                if alias in all_commands:
                    raise ValueError("Command defined more than once: " + alias)
                all_commands[alias] = makewizcmd
            return makewizcmd
        else:
            raise SyntaxError("invalid wizcmd function signature for: " + func.__name__)
    return wizcmd2


@wizcmd("ls")
def do_ls(player, parsed, **ctx):
    """List the contents of a module path under the mudlib tree (try .items.basic)"""
    print = player.tell
    if not parsed.args:
        raise ParseError("ls what path?")
    path = parsed.args[0]
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
def do_clone(player, parsed, **ctx):
    """Clone an item or living directly from the room or inventory, or from an object in the module path"""
    print = player.tell
    if not parsed.args:
        raise ParseError("Clone what?")
    path = parsed.args[0]
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
    elif parsed.who:
        obj = parsed.who.pop()
    else:
        raise ActionRefused("Object not found")
    # clone it
    if isinstance(obj, base.Item):
        item = copy.deepcopy(obj)
        player.insert(item, player)
        print("Cloned: " + repr(item))
        player.location.tell("{player} conjures up {item}, and quickly pockets it."
                             .format(player=lang.capital(player.title),
                                     item=lang.a(item.title)),
                             exclude_living=player)
    elif isinstance(obj, base.Living):
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
def do_destroy(player, parsed, **ctx):
    """Destroys an object or creature."""
    print = player.tell
    if not parsed.who:
        raise ParseError("Destroy what or who?")
    if parsed.unrecognized:
        raise ParseError("It's not clear what you mean by: " + ",".join(parsed.unrecognized))
    # @todo: ask for confirmation (async)
    for victim in parsed.who:
        if isinstance(victim, base.Item):
            if victim in player:
                player.remove(victim, player)
            else:
                player.location.remove(victim, player)
            victim.destroy(ctx)
        elif isinstance(victim, base.Living):
            if victim is player:
                raise ActionRefused("You can't destroy yourself, are you insane?!")
            victim.tell("%s creates a black hole that sucks you up. You're utterly destroyed." % lang.capital(player.title))
            victim.destroy(ctx)
        else:
            raise ActionRefused("Can't destroy " + lang.a(victim.__class__.__name__))
        print("You destroyed %r." % victim)
        player.location.tell("{player} makes some gestures and a tiny black hole appears.\n"
                             "{victim} disappears in it, and the black hole immediately vanishes."
                             .format(player=lang.capital(player.title),
                                     victim=lang.capital(victim.title)),
                             exclude_living=player)


@wizcmd("pdb")
def do_pdb(player, parsed, **ctx):
    """Starts a Python debugging session."""
    import pdb
    pdb.set_trace()   # @todo: remove this when going multiuser (I don't think you can have a synchronous debug session anymore)


@wizcmd("wiretap")
def do_wiretap(player, parsed, **ctx):
    """Adds a wiretap to something to overhear the messages they receive.
'wiretap .' taps the room, 'wiretap name' taps a creature with that name,
'wiretap' shows all your taps, 'wiretap -clear' gets rid of all taps."""
    print = player.tell
    if not parsed.args:
        print("Installed wiretaps:", ", ".join(str(tap) for tap in player.installed_wiretaps) or "none")
        return
    arg = parsed.args[0]
    if arg == ".":
        player.create_wiretap(player.location)
        print("Wiretapped room '%s'." % player.location.name)
    elif arg == "-clear":
        player.installed_wiretaps.clear()
        print("All wiretaps removed.")
    elif parsed.who:
        for living in parsed.who:
            if living is player:
                raise ActionRefused("Can't wiretap yourself.")
            player.create_wiretap(living)
            print("Wiretapped %s." % living.name)
    else:
        raise ActionRefused("Wiretap who?")


@wizcmd("teleport", "teleport_to")
def do_teleport(player, parsed, **ctx):
    """Teleport to a location or creature, or teleport a creature to you.
'teleport[_to] .module.path.to.object' teleports [to] that object (location or creature)
'teleport[_to] playername' teleports [to] that player,
'teleport_to @start' teleports you to the starting location for wizards."""
    if not parsed.args:
        raise ActionRefused("Teleport what to where?")
    args = parsed.args
    teleport_self = parsed.verb == "teleport_to"
    if args[0].startswith("."):
        # teleport player to a location somewhere in a module path
        path, objectname = args[0].rsplit(".", 1)
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
        if args[0] == "@start":
            teleport_to(player, rooms.STARTLOCATION_WIZARD)
        else:
            target = ctx["driver"].search_player(args[0])
            if not target:
                raise ActionRefused("%s isn't here." % args[0])
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
def do_reload(player, parsed, **ctx):
    """Reload the given module (Python)."""
    print = player.tell
    if not parsed.args:
        raise ActionRefused("Reload what?")
    path = parsed.args[0]
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
def do_move(player, parsed, **ctx):
    """Move something or someone to another location (.), item or creature.
This may work around possible restrictions that could prevent stuff
to be moved around normally. For instance you could use it to pick up
items that are normally fixed in place (move item to playername)."""
    print = player.tell
    if len(parsed.args) != 2 or len(parsed.who_order) < 1:
        raise ParseError("Move what where?")
    thing = parsed.who_order[0]
    if isinstance(thing, base.Living):
        raise ActionRefused("* use 'teleport' instead to move livings around.")
    if parsed.args[1] == "." and len(parsed.who_order) == 1:
        # current room is the target
        target = player.location
    elif len(parsed.who_order) == 2:
        target = parsed.who_order[1]
    else:
        raise ParseError("It's not clear what you want to move where.")
    if thing is target:
        raise ActionRefused("You can't move things inside themselves.")
    # determine the current container of the object that is being moved
    if thing in player:
        thing_container = player
    elif thing in player.location:
        thing_container = player.location
    else:
        raise ParseError("There seems to be no %s here." % thing.name)
    thing.move(thing_container, target, player, wiz_force=True)
    print("Moved %s from %s to %s." % (thing.name, thing_container.name, target.name))
    player.location.tell("%s moved %s into %s." %
        (lang.capital(player.title), thing.title, target.title), exclude_living=player)


@wizcmd("debug")
def do_debug(player, parsed, **ctx):
    """Dumps the internal attribute values of a location (.), item or creature."""
    print = player.tell
    if not parsed.args:
        raise ParseError("Debug what?")
    name = parsed.args[0]
    if name == ".":
        obj = player.location
    elif parsed.who:
        obj = parsed.who.pop()
    else:
        raise ActionRefused("Can't find %s." % name)
    print(repr(obj))
    for varname, value in sorted(vars(obj).items()):
        print(".%s: %r" % (varname, value))


@wizcmd("set")
def do_set(player, parsed, **ctx):
    """Set an internal attribute of a location (.), object or creature to a new value.
Usage is: set xxx.fieldname=value (you can use Python literals only)"""
    print = player.tell
    if not parsed.args:
        raise ParseError("Set what? (usage: set xxx.fieldname=value)")
    args = parsed.args[0].split("=")
    if len(args) != 2:
        raise ParseError("Set what? (usage: set xxx.fieldname=value)")
    name, field = args[0].split(".")
    if name == "":
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
