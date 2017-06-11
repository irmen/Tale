"""
Package containing the zones of the game.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from typing import Set, Dict, no_type_check
from tale.base import Item, Door, Armour, Container, Weapon, Key
from tale.items.basic import *
from tale.items.board import BulletinBoard
from tale.items.bank import Bank
from tale.shop import ShopBehavior
from .circledata.parse_obj_files import get_objs
from .circledata.parse_shp_files import get_shops
from .circledata.parse_zon_files import get_zones


print("\nPre-loading circle data files.")
objs = get_objs()
print(len(objs), "objects loaded.")
shops = get_shops()
print(len(shops), "shops loaded.")
zones = get_zones()
print(len(zones), "zones loaded.")


from .circle_mobs import *
from .circle_locations import *


# various caches, DO NOT CLEAR THESE, or duplicates might be spawned
converted_items = set()  # type: Set[int]
converted_shops = {}     # type: Dict[int, ShopBehavior]


# the four bulletin boards
# see spec_assign.c/assign_objects()
# @todo board levels, readonly, etc.
circle_bulletin_boards = {
    3096: "boards/social.json",
    3097: "boards/frozen.json",
    3098: "boards/immort.json",
    3099: "boards/mort.json"
}

# the banks (atms, credit card)
# see spec_assign.c/assign_objects()
# @todo bank class and its verbs
circle_banks = {
    3034: "bank/bank.json",
    3036: "bank/bank.json"
}


@no_type_check
def make_item(vnum: int) -> Item:
    """Create an instance of an item for the given vnum"""
    c_obj = objs[vnum]
    aliases = list(c_obj.aliases)
    name = aliases[0]
    aliases = set(aliases[1:])
    title = c_obj.shortdesc
    if title.startswith("the ") or title.startswith("The "):
        title = title[4:]
    if title.startswith("a ") or title.startswith("A "):
        title = title[2:]
    if vnum in circle_bulletin_boards:
        # it's a bulletin board
        item = BulletinBoard(name, title, short_descr=c_obj.longdesc)
        item.storage_file = circle_bulletin_boards[vnum]   # note that some instances reuse the same board
        item.load()
        # remove the item name from the extradesc to avoid 'not working' messages
        c_obj.extradesc = [ed for ed in c_obj.extradesc if ed["keywords"] != {item.name}]
    elif vnum in circle_banks:
        # it's a bank (atm, creditcard)
        item = Bank(name, title, short_descr=c_obj.longdesc)
        item.storage_file = circle_banks[vnum]    # instances may reuse the same bank storage file
        if c_obj.weight > 50 or "canttake" in c_obj.wear:
            item.portable = False
        else:
            item.portable = True
        item.load()
    elif c_obj.type == "container":
        if c_obj.typespecific.get("closeable"):
            item = Boxlike(name, title, short_descr=c_obj.longdesc)
            item.opened = True
            if "closed" in c_obj.typespecific:
                item.opened = not c_obj.typespecific["closed"]
        else:
            item = Container(name, title, short_descr=c_obj.longdesc)
    elif c_obj.type == "weapon":
        item = Weapon(name, title, short_descr=c_obj.longdesc)
        # @todo weapon attrs
    elif c_obj.type == "armor":
        item = Armour(name, title, short_descr=c_obj.longdesc)
        # @todo armour attrs
    elif c_obj.type == "key":
        item = Key(name, title, short_descr=c_obj.longdesc)
        item.key_for(code=vnum)   # the key code is just the item's vnum
    elif c_obj.type == "note":  # doesn't yet occur in the obj files though
        item = Note(name, title, short_descr=c_obj.longdesc)
    elif c_obj.type == "food":
        item = Food(name, title, short_descr=c_obj.longdesc)
        item.affect_fullness = c_obj.typespecific["filling"]
        item.poisoned = c_obj.typespecific.get("ispoisoned", False)
    elif c_obj.type == "light":
        item = Light(name, title, short_descr=c_obj.longdesc)
        item.capacity = c_obj.typespecific["capacity"]
    elif c_obj.type == "scroll":
        item = Scroll(name, title, short_descr=c_obj.longdesc)
        item.spell_level = c_obj.typespecific["level"]
        spells = {c_obj.typespecific["spell1"]}
        if "spell2" in c_obj.typespecific:
            spells.add(c_obj.typespecific["spell2"])
        if "spell3" in c_obj.typespecific:
            spells.add(c_obj.typespecific["spell3"])
        item.spells = frozenset(spells)
    elif c_obj.type in ("staff", "wand"):
        item = MagicItem(name, title, short_descr=c_obj.longdesc)
        item.level = c_obj.typespecific["level"]
        item.capacity = c_obj.typespecific["capacity"]
        item.remaining = c_obj.typespecific["remaining"]
        item.spell = c_obj.typespecific["spell"]
    elif c_obj.type == "trash":
        item = Trash(name, title, short_descr=c_obj.longdesc)
    elif c_obj.type == "drinkcontainer":
        item = Drink(name, title, short_descr=c_obj.longdesc)
        item.capacity = c_obj.typespecific["capacity"]
        item.quantity = c_obj.typespecific["remaining"]
        item.contents = c_obj.typespecific["drinktype"]
        drinktype = Drink.drinktypes[item.contents]
        item.affect_drunkness = drinktype.drunkness
        item.affect_fullness = drinktype.fullness
        item.affect_thirst = drinktype.thirst
        item.poisoned = c_obj.typespecific.get("ispoisoned", False)
    elif c_obj.type == "potion":
        item = Potion(name, title, short_descr=c_obj.longdesc)
        item.spell_level = c_obj.typespecific["level"]
        spells = {c_obj.typespecific["spell1"]}
        if "spell2" in c_obj.typespecific:
            spells.add(c_obj.typespecific["spell2"])
        if "spell3" in c_obj.typespecific:
            spells.add(c_obj.typespecific["spell3"])
        item.spells = frozenset(spells)
    elif c_obj.type == "money":
        item = Money(name, title, short_descr=c_obj.longdesc)
        item.value = c_obj.typespecific["amount"]
    elif c_obj.type == "boat":
        item = Boat(name, title, short_descr=c_obj.longdesc)
    elif c_obj.type == "worn":
        item = Wearable(name, title, short_descr=c_obj.longdesc)
        # @todo worn attrs
    elif c_obj.type == "fountain":
        item = Fountain(name, title, short_descr=c_obj.longdesc)
        item.capacity = c_obj.typespecific["capacity"]
        item.quantity = c_obj.typespecific["remaining"]
        item.contents = c_obj.typespecific["drinktype"]
        item.poisoned = c_obj.typespecific.get("ispoisoned", False)
    elif c_obj.type in ("treasure", "other"):
        item = Item(name, title, short_descr=c_obj.longdesc)
    else:
        raise ValueError("invalid obj type: " + c_obj.type)
    for ed in c_obj.extradesc:
        kwds = ed["keywords"] - {name}  # remove the item name from the extradesc to avoid doubles
        item.add_extradesc(kwds, ed["text"])
    item.circle_vnum = vnum  # keep the vnum
    item.aliases = aliases
    item.value = c_obj.cost
    item.rent = c_obj.rent
    item.weight = c_obj.weight
    # @todo: affects, effects, wear
    converted_items.add(vnum)
    return item


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
    missing = set(objs) - set(converted_items)
    print(len(missing), "unused item types.")
    # for vnum in sorted(missing):
    #    item = make_item(vnum)
    #    print("  cvnum %d: %s" % (item.circle_vnum, item))
