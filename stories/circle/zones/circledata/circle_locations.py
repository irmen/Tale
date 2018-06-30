"""
The specialized location classes of the game.
It also builds the Shops (which are not strictly locations but are most natural here).

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from types import SimpleNamespace
from typing import Dict
from tale import mud_context, lang
from tale.base import Location, Living, ParseResult, Exit, Door
from tale.errors import ActionRefused, LocationIntegrityError
from tale.shop import ShopBehavior
from .parse_wld_files import get_rooms
from .parse_shp_files import get_shops
from .circle_mobs import make_mob
from .circle_items import make_item


__all__ = ("converted_rooms", "converted_shops", "make_location", "make_exit", "make_shop", "init_circle_locations")


rooms = {}  # type: Dict[int, SimpleNamespace]
shops = {}   # type: Dict[int, SimpleNamespace]


def init_circle_locations() -> Dict[int, SimpleNamespace]:
    global rooms, shops
    rooms = get_rooms()
    print(len(rooms), "rooms loaded.")
    shops = get_shops()
    print(len(shops), "shops loaded.")
    return shops   # zone init needs these


class PetShop(Location):
    """
    A special shop where you can buy pets.
    Because Livings cannot be in anyone's inventory (and because the Circle data files
    specify it this way) the pets for sale are in the 'back room' that has a circle vnum +1 of this room itself.
    """
    def init(self):
        super().init()
        self.verbs = {
            "list": "Show a list of the pets that are for sale.",
            "buy": "Purchase a pet, optionally giving it a name as well."
        }

    def get_pets(self):
        pet_room = make_location(self.circle_vnum + 1)  # Yuck... but circle defines it this way, the pets are in the back room...
        return {pet: pet.stats.level * 300.0 for pet in pet_room.livings}

    def handle_verb(self, parsed: ParseResult, actor: Living) -> bool:
        if parsed.verb == "list":
            pets = self.get_pets()
            actor.tell("Available pets at the moment are:", end=True)
            txt = ["<ul>  pet            <dim>|</><ul> price     </>"]
            for i, (pet, price) in enumerate(pets.items(), start=1):
                txt.append("  %-15s  %s" % (pet.name, mud_context.driver.moneyfmt.display(price)))
            actor.tell("\n".join(txt), format=False)
            return True
        elif parsed.verb == "buy":
            if not parsed.args:
                raise ActionRefused("Buy which pet? Don't forget to name it as well (optional).")
            pets = self.get_pets()
            for pet, price in pets.items():
                if pet.name == parsed.args[0].lower():
                    pet = make_mob(pet.circle_vnum, type(pet))
                    if price > actor.money:
                        raise ActionRefused("You can't afford that pet.")
                    if len(parsed.args) == 2:
                        name = parsed.args[1].lower()
                        pet.title = "%s %s" % (pet.name, lang.capital(name))
                        pet.description += " A small sign on a chain around the neck says 'My name is %s'." % lang.capital(name)
                        pet.aliases.add(pet.name)
                        pet.name = name
                    pet.following = actor   # @todo make pet charmed as well (see circle doc/src)
                    pet.is_pet = True
                    actor.money -= price
                    actor.tell_others("{Actor} buys %s as a pet." % pet.title)
                    actor.tell("You paid %s and received %s as your new pet. Happy times!"
                               % (mud_context.driver.moneyfmt.display(price), pet.title))
                    pet.move(actor.location, pet)
                    return True
            raise ActionRefused("There is no such pet!")
        else:
            return super().handle_verb(parsed, actor)


class Garbagedump(Location):
    """
    Special location that is a garbage dump. It destroys stuff dropped here
    (and rewards players for keeping things tidy)
    """
    def init(self):
        super().init()
    # @todo trash cleanup


# various caches, DO NOT CLEAR THESE, or duplicates might be spawned
converted_rooms = {}     # type: Dict[int, Location]
converted_shops = {}     # type: Dict[int, ShopBehavior]

circle_donation_room = 3063    # items and gold donated by wizards end up here as help for newbies  @todo make donation room
circle_pet_shops = {3031}      # special shops, they sell living creatures!
circle_dump_rooms = {3030}     # special rooms that are a garbage dump and destroy dropped stuff.


def make_location(vnum: int) -> Location:
    """
    Get a Tale location object for the given circle room vnum.
    This performs an on-demand conversion of the circle room data to Tale.
    """
    # @todo deal with location type ('inside') and attributes ('nomob', 'dark', 'death'...)
    try:
        return converted_rooms[vnum]   # get cached version if available
    except KeyError:
        c_room = rooms[vnum]
        loc = None
        if vnum in circle_dump_rooms or "death" in c_room.attributes:
            loc = Garbagedump(c_room.name, c_room.desc)
        elif vnum in circle_pet_shops:
            loc = PetShop(c_room.name, c_room.desc)
        else:
            loc = Location(c_room.name, c_room.desc)
        loc.circle_vnum = vnum   # keep the circle vnum
        loc.circle_zone = c_room.zone    # keep the circle zone number
        for ed in c_room.extradesc:
            loc.add_extradesc(ed["keywords"], ed["text"])
        converted_rooms[vnum] = loc
        for circle_exit in c_room.exits.values():
            if circle_exit.roomlink >= 0:
                xt = make_exit(circle_exit)
                while True:
                    try:
                        xt.bind(loc)
                        break
                    except LocationIntegrityError as x:
                        if x.direction in xt.aliases:
                            # circlemud exit keywords can be duplicated over various exits
                            # if we have a conflict, just remove the alias from the exit and try again
                            xt.aliases = xt.aliases - {x.direction}
                            continue
                        else:
                            if loc.exits[x.direction] is xt:
                                # this can occur, the exit is already bound
                                break
                            else:
                                # in this case a true integrity error occurred
                                raise
            else:
                # add the description of the inaccessible exit to the room's own description.
                loc.description += " " + circle_exit.desc
        return loc


def make_exit(c_exit: SimpleNamespace) -> Exit:
    """Create an instance of a door or exit for the given circle exit"""
    if c_exit.type in ("normal", "pickproof"):  # @todo other door types? reverse doors? locks/keys?
        door = Door(c_exit.direction, make_location(c_exit.roomlink), c_exit.desc)
        door.aliases |= c_exit.keywords
        return door
    else:
        exit = Exit(c_exit.direction, make_location(c_exit.roomlink), c_exit.desc)
        exit.aliases |= c_exit.keywords
        return exit


def make_shop(vnum: int) -> ShopBehavior:
    """Create an instance of a shop given by the vnum"""
    try:
        return converted_shops[vnum]
    except KeyError:
        c_shop = shops[vnum]
        shop = ShopBehavior()
        shop.circle_vnum = c_shop.circle_vnum  # keep the vnum
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
