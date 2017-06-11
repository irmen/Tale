"""
Package containing the zones of the game.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from typing import Dict
from tale.base import Door, Container
from tale.shop import ShopBehavior
from .circledata.parse_shp_files import get_shops
from .circledata.parse_zon_files import get_zones


shops = get_shops()
print(len(shops), "shops loaded.")
zones = get_zones()
print(len(zones), "zones loaded.")


from .circle_mobs import make_mob, converted_mobs, MShopkeeper
from .circle_locations import make_location, make_exit, converted_rooms
from .circle_items import make_item, converted_items, unconverted_objs


# various caches, DO NOT CLEAR THESE, or duplicates might be spawned
converted_shops = {}     # type: Dict[int, ShopBehavior]


def make_shop(vnum: int) -> ShopBehavior:
    """Create an instance of a shop given by the vnum"""
    try:
        return converted_shops[vnum]
    except KeyError:
        c_shop = shops[vnum]
        shop = ShopBehavior()
        shop.circle_vnum = c_shop.circle_vnum  # type: ignore  # keep the vnum
        shop.shopkeeper_vnum = c_shop.shopkeeper   # keep the vnum of the shopkeeper
        shop.banks_money = c_shop.banks
        shop.will_fight = c_shop.fights
        shop.buyprofit = c_shop.buyprofit       # price factor when shop buys an item
        assert shop.buyprofit <= 1.0
        shop.sellprofit = c_shop.sellprofit     # price factor when shop sells item
        assert shop.sellprofit >= 1.0
        open_hrs = (max(0, c_shop.open1), min(24, c_shop.close1))
        shop.open_hours = [open_hrs]
        if c_shop.open2 and c_shop.close2:
            open_hrs = (max(0, c_shop.open2), min(24, c_shop.close2))
            shop.open_hours.append(open_hrs)
        # items to be cloned when sold (endless supply):
        shop.forsale = set()
        missing_items = set()
        for item_vnum in c_shop.forsale:
            try:
                shop.forsale.add(make_item(item_vnum))
            except KeyError:
                missing_items.add(item_vnum)
        if missing_items:
            print("Shop #%d: unknown items:" % vnum, missing_items)
        shop.msg_playercantafford = c_shop.msg_playercantafford
        shop.msg_playercantbuy = c_shop.msg_playercantbuy
        shop.msg_playercantsell = c_shop.msg_playercantsell
        shop.msg_shopboughtitem = c_shop.msg_shopboughtitem
        shop.msg_shopcantafford = c_shop.msg_shopcantafford
        shop.msg_shopdoesnotbuy = c_shop.msg_shopdoesnotbuy
        shop.msg_shopsolditem = c_shop.msg_shopsolditem
        shop.action_temper = c_shop.msg_temper
        shop.willbuy = c_shop.willbuy
        shop.wontdealwith = c_shop.wontdealwith
        converted_shops[vnum] = shop
        return shop


def init_zones() -> None:
    """Populate the zones and initialize inventories and door states. Set up shops."""
    print("Initializing zones.")
    num_shops = num_mobs = num_items = 0
    all_shopkeepers = {shop.shopkeeper for shop in shops.values()}
    for vnum in sorted(zones):
        zone = zones[vnum]
        for mobref in zone.mobs:
            if mobref.circle_vnum in all_shopkeepers:
                # mob is a shopkeeper, we need to make a shop+shopkeeper rather than a regular mob
                mob = make_mob(mobref.circle_vnum, mob_class=MShopkeeper)
                # find the shop it works for
                shop_vnums = [vnum for vnum, shop in shops.items() if shop.shopkeeper == mobref.circle_vnum]
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
    # for vnum in sorted(missing):
    #    item = make_item(vnum)
    #    print("  cvnum %d: %s" % (item.circle_vnum, item))
