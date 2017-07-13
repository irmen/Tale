"""
Magnolia street.
Connects with Rose Street on the Crossing.

magnolia st. 1, pharmacy
magnolia st. 2, magnolia st. 3, factory
"""

from tale import mud_context
from tale.base import Location, Exit, Door, Item
from tale.errors import StoryCompleted
from zones import houses, rose_st
from zones.npcs import Apothecary


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


apothecary = Apothecary("carla", "f", title="apothecary Carla")
apothecary.extra_desc["bottle"] = "It is a small bottle of the pills that your friend Peter needs for his illness."
apothecary.extra_desc["pills"] = apothecary.extra_desc["bottle"]
apothecary.aliases.add("apothecary")

# the medicine Peter needs
medicine = Item("pills", "bottle of pills", descr="It looks like the medicine your friend Peter needs for his illness.")
medicine.value = Apothecary.pills_price
medicine.aliases = {"bottle", "medicine"}
apothecary.init_inventory([medicine])
pharmacy.insert(apothecary, None)
