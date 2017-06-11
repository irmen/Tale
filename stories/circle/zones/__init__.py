"""
Package containing the zones of the game.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from tale.base import Door, Container
from .circledata.parse_zon_files import get_zones
from .circledata.circle_mobs import make_mob, converted_mobs, MShopkeeper, init_circle_mobs
from .circledata.circle_locations import make_location, make_exit, converted_rooms, make_shop, converted_shops, init_circle_locations
from .circledata.circle_items import make_item, converted_items, unconverted_objs, init_circle_items


def init_zones() -> None:
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
            if mobref.circle_vnum in all_shopkeepers:
                # mob is a shopkeeper, we need to make a shop+shopkeeper rather than a regular mob
                mob = make_mob(mobref.circle_vnum, mob_class=MShopkeeper)
                # find the shop it works for
                shop_vnums = [vnum for vnum, shop in all_shop_defs.items() if shop.shopkeeper == mobref.circle_vnum]
                assert len(shop_vnums) == 1
                shop_vnum = shop_vnums[0]
                shopdata = make_shop(shop_vnum)
                mob.shop = shopdata  # type: ignore
                num_shops += 1
            else:
                mob = make_mob(mobref.circle_vnum)
            for vnum, details in mobref.equipped.items():
                obj = make_item(vnum)
                # @todo actually wield the item
                num_items += 1
            inventory = set()
            for vnum, maxexists in mobref.inventory.items():
                obj = make_item(vnum)
                inventory.add(obj)
                num_items += 1
            if inventory:
                mob.init_inventory(inventory)
            if mobref.circle_vnum in all_shopkeepers:
                # if it is a shopkeeper, the shop.forsale items should also be present in his inventory
                if mob.inventory_size < len(mob.shop.forsale):   # type: ignore
                    raise ValueError("shopkeeper %d's inventory missing some shop.forsale items from shop %d" %
                                     (mobref.circle_vnum, mob.shop.circle_vnum))   # type: ignore
                for item in mob.shop.forsale:  # type: ignore
                    if not any(i for i in mob.inventory if i.title == item.title):
                        raise ValueError("shop.forsale item %d (%s) not in shopkeeper %d's inventory" %
                                         (item.circle_vnum, item.title, mobref.circle_vnum))
            loc = make_location(mobref.room)
            loc.insert(mob, None)
            num_mobs += 1
        for details in zone.objects:
            obj = make_item(details["vnum"])
            loc = make_location(details["room"])
            loc.insert(obj, None)
            inventory = set()
            for vnum, maxexists in details["contains"].items():
                sub_item = make_item(vnum)
                num_items += 1
                inventory.add(sub_item)
            if inventory:
                assert isinstance(obj, Container)
                obj.init_inventory(inventory)
            num_items += 1
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

    print("Activated: %d mob types, %d item types, %d rooms, %d shop types" % (
        len(converted_mobs), len(converted_items), len(converted_rooms), len(converted_shops)))
    print("Spawned: %d mobs, %d items, %d shops" % (num_mobs, num_items, num_shops))
    print(len(unconverted_objs()), "unused item types.")
