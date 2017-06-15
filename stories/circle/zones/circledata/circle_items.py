"""
Creating the special items in the Circle story.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from types import SimpleNamespace
from typing import Set, Dict, no_type_check
from tale.base import Item, Armour, Container, Weapon, Key
from tale.items.basic import *
from tale.items.board import BulletinBoard
from tale.items.bank import Bank
from .parse_obj_files import get_objs


__all__ = ("converted_items", "make_item", "unconverted_objs")


objs = {}    # type: Dict[int, SimpleNamespace]


def init_circle_items() -> None:
    global objs
    objs = get_objs()
    print(len(objs), "objects loaded.")


# various caches, DO NOT CLEAR THESE, or duplicates might be spawned
converted_items = set()  # type: Set[int]


def unconverted_objs() -> Set[int]:
    return set(objs) - set(converted_items)


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
    if title.startswith(("a ", "A ")):
        title = title[2:]
    elif title.startswith(("an ", "An ")):
        title = title[3:]
    elif title.startswith(("the ", "The ")):
        title = title[4:]
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
        if c_obj.weight > 50:
            c_obj.takeable = False
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
        value = c_obj.typespecific["amount"]
        item = Money(name, value, title=title, short_descr=c_obj.longdesc)
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
    if c_obj.cost > 0:
        item.value = c_obj.cost
    item.rent = c_obj.rent
    item.weight = c_obj.weight
    item.takeable = c_obj.takeable
    # @todo: affects, effects, wear
    converted_items.add(vnum)
    return item
