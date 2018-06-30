"""
Package containing the zones of the game.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from collections import deque
from typing import MutableSequence, List
from tale.driver import Driver
from tale.base import Door, Container, Item
from tale.util import Context
from .circledata.parse_zon_files import get_zones
from .circledata.circle_mobs import make_mob, converted_mobs, mobs_with_special, MShopkeeper, init_circle_mobs
from .circledata.circle_locations import make_location, converted_rooms, make_shop, converted_shops, init_circle_locations
from .circledata.circle_items import make_item, converted_items, unconverted_objs, init_circle_items


def init_zones(driver: Driver) -> None:
    """Populate the zones and initialize inventories and door states. Set up shops."""
    print("Initializing zones.")
    zones = get_zones()
    print(len(zones), "zones loaded.")
    init_circle_mobs()
    init_circle_items()
    all_shop_defs = init_circle_locations()
    num_shops = num_mobs = num_items = 0
    all_shopkeepers = {shop.shopkeeper for shop in all_shop_defs.values()}
    for vnum in sorted(zones):
        zone = zones[vnum]
        for mobref in zone.mobs:
            if mobref.vnum in all_shopkeepers:
                # mob is a shopkeeper, we need to make a shop+shopkeeper rather than a regular mob
                mob = make_mob(mobref.vnum, mob_class=MShopkeeper)
                # find the shop it works for
                shop_vnums = [vnum for vnum, shop in all_shop_defs.items() if shop.shopkeeper == mobref.vnum]
                assert len(shop_vnums) == 1
                shop_vnum = shop_vnums[0]
                shopdata = make_shop(shop_vnum)
                mob.shop = shopdata
                num_shops += 1
            else:
                mob = make_mob(mobref.vnum)
            inventory = []  # type: List[Item]
            for wear_position, obj_ref in mobref.equip.items():
                obj = make_item(obj_ref.vnum)
                inventory.append(obj)    # @todo actually wield/wear the item! instead of putting it in the inventory
                num_items += 1
                if obj_ref.contains:
                    items_in_equipped = []  # type: List[Item]
                    for (c_vnum, c_max_exists) in obj_ref.contains:
                        items_in_equipped.append(make_item(c_vnum))
                    obj.init_inventory(items_in_equipped)
                    num_items += len(items_in_equipped)
            for obj_ref in mobref.inventory:
                obj = make_item(obj_ref.vnum)
                inventory.append(obj)
                num_items += 1
                if obj_ref.contains:
                    items_in_carried = []  # type: List[Item]
                    for (c_vnum, c_max_exists) in obj_ref.contains:
                        items_in_carried.append(make_item(c_vnum))
                    obj.init_inventory(items_in_carried)
                    num_items += len(items_in_carried)
            if inventory:
                mob.init_inventory(inventory)
                del inventory
            if mobref.vnum in all_shopkeepers:
                # if it is a shopkeeper, the shop.forsale items should also be present in his inventory
                if mob.inventory_size < len(mob.shop.forsale):
                    raise ValueError("shopkeeper %d's inventory missing some shop.forsale items from shop %d" %
                                     (mobref.vnum, mob.shop.circle_vnum))
                for item in mob.shop.forsale:
                    if not any(i for i in mob.inventory if i.title == item.title):
                        raise ValueError("shop.forsale item %d (%s) not in shopkeeper %d's inventory" %
                                         (item.circle_vnum, item.title, mobref.vnum))
            loc = make_location(mobref.room)
            loc.insert(mob, None)
            num_mobs += 1
        for obj_ref in zone.objects:
            obj = make_item(obj_ref.vnum)
            loc = make_location(obj_ref.room)
            loc.insert(obj, None)
            if obj_ref.contains:
                items_in_room_obj = []  # type: List[Item]
                for vnum, max_exists in obj_ref.contains:
                    items_in_room_obj.append(make_item(vnum))
                obj.init_inventory(items_in_room_obj)
                num_items += len(items_in_room_obj)
            num_items += 1
        for door_state in zone.doorstates:
            loc = make_location(door_state.room)
            try:
                xt = loc.exits[door_state.exit]
            except KeyError:
                pass
            else:
                if not isinstance(xt, Door):
                    raise TypeError("exit type not door, but asked to set state")
                if door_state.state == "open":
                    xt.locked = False
                    xt.opened = True
                elif door_state.state == "closed":
                    xt.locked = False
                    xt.opened = False
                elif door_state.state == "locked":
                    xt.locked = True
                    xt.opened = False
                else:
                    raise ValueError("invalid door state: " + door_state.state)

    # create the handful of rooms that have no incoming paths (unreachable)
    for vnum in (0, 3, 3055):
        make_location(vnum)

    print("Activated: %d mob types, %d item types, %d rooms, %d shop types" % (
        len(converted_mobs), len(converted_items), len(converted_rooms), len(converted_shops)))
    print("Spawned: %d mobs (%d specials), %d items, %d shops" % (num_mobs, len(mobs_with_special), num_items, num_shops))
    print(len(unconverted_objs()), "unused item defs.")

    # divide all the special mobs over the 5 mobs buckets (via their hash number)
    # this prevents all 300+ special mobs doing something every 10 seconds at the same time
    global _special_mobs_buckets
    assert len(_special_mobs_buckets) == 5
    for mob in mobs_with_special:
        _special_mobs_buckets[(hash(mob) // 10) % 5].append(mob)
    mobs_with_special.clear()
    # set up the periodical pulse events
    mobile_timer = 10.0 / len(_special_mobs_buckets)
    driver.defer((1.6, mobile_timer, mobile_timer), pulse_mobile)
    driver.defer((4.5, 10.0, 10.0), pulse_zone)


_special_mobs_buckets = deque([[], [], [], [], []])   # type: MutableSequence[list]


def pulse_mobile(ctx: Context=None) -> None:
    """
    Called every so often to handle mob activity (other than combat).
    Via round robin scheduling every mob gets called once every 10 seconds, but not all at the same time.
    """
    for mob in _special_mobs_buckets[0]:
        mob.do_special(ctx)
    _special_mobs_buckets.rotate()


def pulse_zone(ctx: Context=None) -> None:
    """Called every 10 seconds to handle zone activity"""
    pass   # @todo zone pulse
