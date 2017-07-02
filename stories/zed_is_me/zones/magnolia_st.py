"""
Magnolia street.
Connects with Rose Street on the Crossing.

magnolia st. 1, pharmacy
magnolia st. 2, magnolia st. 3, factory
"""

import random
from tale import mud_context, lang
from tale.base import Location, Exit, Door, Living, ParseResult, Item
from tale.errors import StoryCompleted, ActionRefused, ParseError, TaleError
from zones import houses, rose_st


street1 = Location("Magnolia Street", "Your house is on Magnolia Street, one of the larger streets in town. "
                                      "The rest of the town lies eastwards.")
street2 = Location("Magnolia Street", "Another part of the street.")
street3 = Location("Magnolia Street (east)", "The eastern part of Magnolia Street.")


Door.connect(houses.livingroom,
             ["door", "outside", "street"], "Your front door leads outside, to the street.",
             "There's a heavy front door here that leads to the streets outside.",
             street1,
             ["house", "north", "inside"], "You can go back inside your house.",
             "It's your house, on the north side of the street.")


pharmacy = Location("Pharmacy", "A pharmacy. It is completely empty, all medicine seems gone.")

Exit.connect(pharmacy, ["east", "outside", "street"], "Magnolia street is outside towards the east.", None,
             street1, ["pharmacy", "west"], "The west end of the street leads to the pharmacy.", None)


factory = Location("ArtiGrow factory", "This area is the ArtiGrow fertilizer factory.")

Exit.connect(factory, ["west", "street"], "You can leave the factory to the west, back to Magnolia Street.", None,
             street3, ["factory", "east"], "Eastwards you'll enter the ArtiGrow factory area.", None)

Exit.connect(street1, ["town", "east"], "The street extends eastwards, towards the rest of the town.", None,
             street2, "west", "The street extends to the west, where your house is.", None)

Door.connect(street2,
             ["north", "gate", "playground"],
             "To the north there is a small gate that connects to the children's playground.", None,
             rose_st.playground,
             ["gate", "south"],
             "The gate that leads back to Magnolia Street is south.", None)

Exit.connect(street2, ["south", "house", "neighbors"], "You can see the house from the neighbors across the street, to the south.", None,
             houses.neighbors_house, ["street", "north"], "The street is back north.", None)

street2.add_exits([
    Exit(["east", "crossing"], "rose_st.crossing", "There's a crossing to the east."),
])

street3.add_exits([
    Exit(["west", "crossing"], "rose_st.crossing", "There's a crossing to the west.")
])


# @todo A (temporary) location that exits the game, should be implemented later as part of the puzzle.
# For now, it is accessed via a hatch in the neighbors_house.  #
class TemporaryGameEnd(Location):
    def notify_player_arrived(self, player, previous_location: Location) -> None:
        # player has entered, and thus the story ends
        player.tell("\n")
        player.tell("\n")
        player.tell_text_file(mud_context.resources["messages/completion_success.txt"])
        raise StoryCompleted


temp_game_end = TemporaryGameEnd("Temporary Game Ending", "That is weird, you seem to fall trough the world...")
end_exit = Exit(["hatch"], temp_game_end, "There's an ominous looking open hatch here.",
                "The hatch is open, and you can easily go through. However there seems to be only endless darkness behind it.")
houses.neighbors_house.add_exits([end_exit])


# the pharmacy sales person
class Apothecary(Living):
    pills_price = 20.0   # don't randomly change this, there's a fixed amount of money lying in the game...

    def init(self):
        super().init()
        self.verbs["haggle"] = "Haggles with a person to make them sell you something below the actual price. " \
                               "Provide the price you're offering."
        self.verbs["bargain"] = "Try to make a person sell you something below the actual price. " \
                                "Provide the price you're offering."
        self.verbs["buy"] = "Purchase something."

    @property
    def description(self) -> str:
        if self.search_item("pills", include_location=False):
            return "%s looks scared, and clenches a small bottle in %s hands." % (lang.capital(self.subjective), self.possessive)
        return "%s looks scared." % self.subjective

    @description.setter
    def description(self, value: str) -> None:
        raise TaleError("cannot set dynamic description")

    def handle_verb(self, parsed: ParseResult, actor: Living) -> bool:
        pills = self.search_item("pills", include_location=False)
        if parsed.verb in ("bargain", "haggle"):
            if not parsed.args:
                raise ParseError("For how much money do you want to haggle?")
            if not pills:
                raise ActionRefused("It is no longer available for sale.")
            amount = mud_context.driver.moneyfmt.parse(parsed.args)
            price = mud_context.driver.moneyfmt.display(self.pills_price)
            if amount < self.pills_price/2:
                actor.tell("%s glares angrily at you and says, \"No way! I want at least half the original price! "
                           "Did't I tell you? They were %s!\"" % (lang.capital(self.title), price))
                raise ActionRefused()
            self.do_buy_pills(actor, pills, amount)
            return True
        if parsed.verb == "buy":
            if not parsed.args:
                raise ParseError("Buy what?")
            if "pills" in parsed.args or "bottle" in parsed.args or "medicine" in parsed.args:
                if not pills:
                    raise ActionRefused("It is no longer available for sale.")
                self.do_buy_pills(actor, pills, self.pills_price)
                return True
            if pills:
                raise ParseError("There's nothing left to buy in the shop, except for the pills the apothecary is holding.")
            else:
                raise ParseError("There's nothing left to buy.")
        return False

    def do_buy_pills(self, actor: Living, pills: Item, price: float) -> None:
        if actor.money < price:
            raise ActionRefused("You don't have enough money!")
        actor.money -= price
        self.money += price
        pills.move(actor, self)
        price_str = mud_context.driver.moneyfmt.display(price)
        actor.tell("After handing %s the %s, %s gives you the %s." % (self.objective, price_str, self.subjective, pills.title))
        self.tell_others("{Actor} says: \"Here's your medicine, now get out of here!\"")

    def notify_action(self, parsed: ParseResult, actor: Living) -> None:
        # react on mentioning the medicine
        if parsed.verb in self.verbs:
            return
        if "medicine" in parsed.unparsed or "pills" in parsed.unparsed or "bottle" in parsed.unparsed:
            if self.search_item("pills", include_location=False):  # do we still have the pills?
                price = mud_context.driver.moneyfmt.display(self.pills_price)
                self.tell_others("{Actor} clenches the bottle %s's holding even tighter. %s says: "
                                 "\"You won't get them for free! They will cost you %s!\""
                                 % (self.subjective, lang.capital(self.subjective), price))
            else:
                self.tell_others("{Actor} says: \"Good luck with it!\"")
        if random.random() < 0.5:
            actor.tell("%s glares at you." % lang.capital(self.title))


apothecary = Apothecary("carla", "f", title="apothecary Carla")
apothecary.extra_desc["bottle"] = "It is a small bottle of the pills that your friend Peter needs for his illness."
apothecary.extra_desc["pills"] = apothecary.extra_desc["bottle"]
apothecary.aliases.add("apothecary")

medicine = Item("pills", "bottle of pills", descr="It looks like the medicine your friend Peter needs for his illness.")
medicine.value = Apothecary.pills_price
medicine.aliases = {"bottle", "medicine"}
apothecary.init_inventory([medicine])
pharmacy.insert(apothecary, None)
