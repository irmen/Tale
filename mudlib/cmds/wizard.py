# wizard commands
from __future__ import print_function
import types
import copy
import functools
from ..errors import SecurityViolation, ParseError, ActionRefused
from .. import baseobjects
from .. import languagetools
from .. import npc


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
            raise ValueError("Command defined more than once: "+command)
        all_commands[command] = makewizcmd
        return makewizcmd
    return wizcmd2


@wizcmd("ls")
def do_ls(player, verb, path, **ctx):
    print = player.tell
    if not path.startswith("."):
        raise ActionRefused("Path must start with '.'")
    try:
        module = __import__("mudlib" + path)
        for name in path.split("."):
            if name:
                module = getattr(module, name)
    except (ImportError, ValueError):
        raise ActionRefused("There's no module named " + path)
    print("<%s>" % path)
    modules = [x[0] for x in vars(module).items() if type(x[1]) is types.ModuleType]
    classes = [x[0] for x in vars(module).items() if type(x[1]) is type and issubclass(x[1], baseobjects.MudObject)]
    items = [x[0] for x in vars(module).items() if isinstance(x[1], baseobjects.Item)]
    livings = [x[0] for x in vars(module).items() if isinstance(x[1], baseobjects.Living)]
    if modules:
        print("Modules: " + ", ".join(modules))
    if classes:
        print("Classes: " + ", ".join(classes))
    if livings:
        print("Livings: " + ", ".join(livings))
    if items:
        print("Items: " + ", ".join(items))


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
            module = __import__("mudlib" + path)
        except (ImportError, ValueError):
            raise ActionRefused("There's no module named " + path)
        if len(path) > 1:
            for name in path.split(".")[1:]:
                module = getattr(module, name)
        obj = getattr(module, objectname, None)
    else:
        # find an object or living from the inventory or the room
        obj = player.search_item(path)
        if not obj:
            obj = player.location.search_living(path)
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
        raise ActionRefused("Can't clone "+languagetools.a(obj.__class__.__name__))


@wizcmd("destroy")
def do_destroy(player, verb, arg, **ctx):
    # @todo: ask for confirmation (async)
    print = player.tell
    if not arg:
        raise ParseError("Destroy what?")
    victim = player.search_item(arg)
    if victim:
        if victim in player.inventory:
            player.inventory.remove(victim)
        else:
            player.location.remove_item(victim)
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
