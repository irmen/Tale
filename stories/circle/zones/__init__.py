"""
Package containing the zones of the game.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
from .circledata.parse_mob_files import get_mobs
from .circledata.parse_obj_files import get_objs
from .circledata.parse_shp_files import get_shops
from .circledata.parse_wld_files import get_rooms
from .circledata.parse_zon_files import get_zones
from tale.base import Location, Item, Exit, Door, Armour, Container, Weapon
from tale.items.basic import Boxlike, Newspaper
from tale.npc import Monster
from tale.errors import LocationIntegrityError
import pprint

print("Loading circle data files.")
mobs = get_mobs()
print(len(mobs), "mobs loaded.")
objs = get_objs()
print(len(objs), "objects loaded.")
shops = get_shops()
print(len(shops), "shops loaded.")
rooms = get_rooms()
print(len(rooms), "rooms loaded.")
zones = get_zones()
print(len(zones), "zones loaded.")


converted_rooms = {}   # doubles as a cache for the rooms
converted_mobs = set()
converted_items = set()


def make_location(vnum):
    """
    Get a Tale location object for the given circle room vnum
    This performs an on-demand conversion of the circle room data to Tale.
    """
    try:
        return converted_rooms[vnum]   # get cached version if available
    except KeyError:
        c_room = rooms[vnum]
        loc = Location(c_room.name, c_room.desc)
        loc.vnum = vnum  # keep the circle vnum
        converted_rooms[vnum] = loc
        for xt in c_room.exits.values():
            if xt.roomlink >= 0:
                exit = make_exit(xt)
                while True:
                    try:
                        exit.bind(loc)
                        break
                    except LocationIntegrityError as x:
                        if x.direction in exit.aliases:
                            # circlemud exit keywords can be duplicated over various exits
                            # if we have a conflict, just remove the alias from the exit and try again
                            exit.aliases = exit.aliases - {x.direction}
                            continue
                        else:
                            if loc.exits[x.direction] is exit:
                                # this can occur, the exit is already bound
                                break
                            else:
                                # in this case a true integrity error occurred
                                raise
            else:
                # add the description of the inaccessible exit to the room's own description.
                loc.description += " " + xt.desc
        return loc


def make_exit(c_exit):
    if c_exit.type in ("normal", "pickproof"):
        xt = Door(c_exit.direction, make_location(c_exit.roomlink), c_exit.desc)
    else:
        xt = Exit(c_exit.direction, make_location(c_exit.roomlink), c_exit.desc)
    xt.aliases |= c_exit.keywords
    return xt


def make_mob(vnum):
    c_mob = mobs[vnum]
    aliases = list(c_mob.aliases)
    name = aliases[0]
    aliases = set(aliases[1:])
    race = "human"  # XXX todo find solution for race, which is not a concept in circle
    title = c_mob.shortdesc
    if title.startswith("the ") or title.startswith("The "):
        title = title[4:]
    if title.startswith("a ") or title.startswith("A "):
        title = title[2:]
    mob = Monster(name, c_mob.gender, race, title, description=c_mob.detaileddesc, short_description=c_mob.longdesc)
    mob.vnum = vnum  # keep the vnum
    mob.aliases = aliases
    mob.aggressive = "aggressive" in c_mob.actions
    # XXX todo stats, alignment, ...
    converted_mobs.add(vnum)
    return mob


def make_item(vnum):
    c_obj = objs[vnum]
    aliases = list(c_obj.aliases)
    name = aliases[0]
    aliases = set(aliases[1:])
    title = c_obj.shortdesc
    if title.startswith("the ") or title.startswith("The "):
        title = title[4:]
    if title.startswith("a ") or title.startswith("A "):
        title = title[2:]
    # make a long description text from extradesc if it exists.
    # this can only deal with extra description texts that are linked to the item name/alias itself.
    descr = None
    for extra in c_obj.extradesc:
        if set(c_obj.aliases) & extra["keywords"]:
            descr = extra["text"]
    if c_obj.type == "container":
        if c_obj.typespecific.get("closeable"):
            item = Boxlike(name, title, description=descr, short_description=c_obj.longdesc)
            item.opened = True
            if "closed" in c_obj.typespecific:
                item.opened = not c_obj.typespecific["closed"]
        else:
            item = Container(name, title, description=descr, short_description=c_obj.longdesc)
    elif c_obj.type == "weapon":
        item = Weapon(name, title, description=descr, short_description=c_obj.longdesc)
    elif c_obj.type == "armor":
        item = Armour(name, title, description=descr, short_description=c_obj.longdesc)
    else:
        item = Item(name, title, description=descr, short_description=c_obj.longdesc)
    item.aliases = aliases
    # XXX todo cost, effects, wear, weight, typespecific array, ...
    item.vnum = vnum  # keep the vnum
    converted_items.add(vnum)
    return item


def init_zones():
    print("Initializing zones.")
    for vnum in sorted(zones):
        zone = zones[vnum]
        print("%3d  %s" % (zone.vnum, zone.name))
        for mobref in zone.mobs:
            mob = make_mob(mobref.vnum)
            #@todo globalmax
            for vnum, details in mobref.equipped.items():
                obj = make_item(vnum)
                # @todo actually wield the item
                pass
            inventory = set()
            for vnum, maxexists in mobref.inventory.items():
                obj = make_item(vnum)
                inventory.add(obj)
            if inventory:
                mob.init_inventory(inventory)
            loc = make_location(mobref.room)
            loc.insert(mob, None)
        for details in zone.objects:
            obj = make_item(details["vnum"])
            loc = make_location(details["room"])
            loc.insert(obj, None)
            #@todo globalmax
            inventory = set()
            for vnum, maxexists in details["contains"].items():
                sub_item = make_item(vnum)
                inventory.add(sub_item)
            if inventory:
                assert isinstance(obj, Container)
                obj.init_inventory(inventory)
        for door_state in zone.doors:
            loc = make_location(door_state["room"])
            try:
                xt = loc.exits[door_state["exit"]]
            except KeyError:
                pass
            else:
                state = door_state["state"]
                if not isinstance(xt, Door):
                    raise TypeError("exit type not door, but asked to set state")
                if state == "open":
                    xt.locked = False
                    xt.opened = True
                elif state == "closed":
                    xt.locked = False
                    xt.opened = False
                elif state == "locked":
                    xt.locked = True
                    xt.opened = False
                else:
                    raise ValueError("invalid door state: " + state)

    # create the handful of rooms that have no incoming paths (unreachable)
    for vnum in (0, 3, 3055):
        make_location(vnum)
    print("Activated: %d mob types, %d item types, %d rooms, %d zones" % (
        len(converted_mobs), len(converted_items), len(converted_rooms), len(zones)
    ))
    missing = set(objs) - set(converted_items)
    print("unused item types (%d):" % len(missing))
    pprint.pprint([objs[v] for v in sorted(missing)])

