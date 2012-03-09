# wizard commands
from __future__ import print_function
import types
import copy
import functools
from ..errors import SecurityViolation
from .. import baseobjects
from .. import languagetools

all_commands = {}


def wizcmd(command):
    def wizcmd2(func):
        """decorator that adds wizard privilege check to the command"""
        @functools.wraps(func)
        def makewizcmd(player, verb, rest, **ctx):
            if not "wizard" in player.privileges:
                raise SecurityViolation("wizard privilege required for verb " + verb)
            return func(player, verb, rest, **ctx)
        if command in all_commands:
            raise ValueError("command defined more than once: "+command)
        all_commands[command] = makewizcmd
        return makewizcmd
    return wizcmd2


@wizcmd("ls")
def do_ls(player, verb, path, **ctx):
    print = player.tell
    if not path.startswith("."):
        print("* ls: path must start with '.'")
        return
    try:
        module = __import__("mudlib" + path)
        for name in path.split("."):
            if name:
                module = getattr(module, name)
    except (ImportError, ValueError):
        print("* ls: here is no module named " + path)
        return
    print("<%s>" % path)
    modules = [x[0] for x in vars(module).items() if type(x[1]) is types.ModuleType]
    classes = [x[0] for x in vars(module).items() if type(x[1]) is type and issubclass(x[1], baseobjects.MudObject)]
    items = [x[0] for x in vars(module).items() if isinstance(x[1], baseobjects.Item)]
    if modules:
        print("Modules: " + ", ".join(modules))
    if classes:
        print("Classes: " + ", ".join(classes))
    if items:
        print("Items: " + ", ".join(items))


@wizcmd("clone")
def do_clone(player, verb, path, **ctx):
    print = player.tell
    if not path.startswith("."):
        # clone an object from the inventory or the room
        obj = player.search_item(path)
    else:
        # clone an item somewhere in a module path
        path, objectname = path.rsplit(".", 1)
        if not objectname:
            print("* clone: invalid object path")
            return
        try:
            module = __import__("mudlib" + path)
        except (ImportError, ValueError):
            print("* clone: there is no module named " + path)
            return
        if len(path) > 1:
            for name in path.split(".")[1:]:
                module = getattr(module, name)
        obj = getattr(module, objectname, None)
    if obj is None or not isinstance(obj, baseobjects.Item):
        print("* clone: object not found")
        return
    item = copy.deepcopy(obj)
    player.inventory.add(item)
    print("* cloned: " + repr(item))
    player.location.tell("{player} conjures up {item}, and quickly pockets it."
                         .format(player=languagetools.capital(player.title),
                                 item=languagetools.a(item.title)),
                         exclude_living=player)


@wizcmd("destroy")
def do_destroy(player, verb, arg, **ctx):
    # @todo: ask for confirmation
    print = player.tell
    item = player.search_item(arg)
    if not item:
        print("There's no %s here." % arg)
    else:
        if item in player.inventory:
            player.inventory.remove(item)
        else:
            player.location.remove_item(item)
        print("You destroyed %r." % item)
        player.location.tell("{player} unmakes {item}: it's suddenly gone."
                             .format(player=languagetools.capital(player.title),
                                     item=languagetools.a(item.title)),
                             exclude_living=player)


@wizcmd("pdb")
def do_pdb(player, verb, rest, **ctx):
    import pdb
    pdb.set_trace()   # @todo: remove this when going multiuser (can't debug anymore then)
