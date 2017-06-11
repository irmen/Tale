"""
Package containing the specialized location classes of the game.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from types import SimpleNamespace
from typing import Dict
from tale import mud_context, lang
from tale.base import Location, Living, ParseResult, Exit, Door
from tale.errors import ActionRefused, LocationIntegrityError
from .circledata.parse_wld_files import get_rooms
from .circle_mobs import make_mob


__all__ = ["PetShop", "converted_rooms", "make_location", "make_exit"]


class PetShop(Location):
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
                    # @todo make pet a follower and charmed
                    actor.money -= price
                    actor.tell_others("{Actor} buys %s as a pet." % pet.title)
                    actor.tell("You paid %s and received %s as your new pet. Happy times!"
                               % (mud_context.driver.moneyfmt.display(price), pet.title))
                    pet.move(actor.location, pet)
                    return True
            raise ActionRefused("There is no such pet!")
        else:
            return super().handle_verb(parsed, actor)


# various caches, DO NOT CLEAR THESE, or duplicates might be spawned
converted_rooms = {}     # type: Dict[int, Location]

circle_donation_room = 3063    # items and gold donated by wizards end up here as help for newbies  @todo make donation room
circle_pet_shops = {3031}      # special shops, they sell living creatures!


rooms = get_rooms()
print(len(rooms), "rooms loaded.")


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
        if vnum not in circle_pet_shops:
            loc = Location(c_room.name, c_room.desc)
        else:
            # location is a special shop
            loc = PetShop(c_room.name, c_room.desc)
        loc.circle_vnum = vnum   # type: ignore  # keep the circle vnum
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
    if c_exit.type in ("normal", "pickproof"):
        door = Door(c_exit.direction, make_location(c_exit.roomlink), c_exit.desc)
        door.aliases |= c_exit.keywords
        return door
    else:
        exit = Exit(c_exit.direction, make_location(c_exit.roomlink), c_exit.desc)
        exit.aliases |= c_exit.keywords
        return exit
