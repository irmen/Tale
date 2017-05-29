"""
Magnolia street.
Connects with Rose Street on the Crossing.

magnolia st. 1, pharmacy
magnolia st. 2, magnolia st. 3, factory
"""

from zones import houses

from tale import mud_context
from tale.base import Location, Exit, Door
from tale.errors import StoryCompleted


street1 = Location("Magnolia Street", "Your house is on Magnolia Street, one of the larger streets in town. "
                                      "The rest of the town lies eastwards.")
street2 = Location("Magnolia Street", "Another part of the street.")
street3 = Location("Magnolia Street (east)", "The eastern part of Magnolia Street.")


pharmacy = Location("Pharmacy", "A pharmacy.")
pharmacy.add_exits([
    Exit(["east", "outside", "street"], street1, "Magnolia street is outside towards the east.")
])

factory = Location("ArtiGrow factory", "This area is the ArtiGrow fertilizer factory.")
factory.add_exits([
    Exit(["west", "street"], street3, "You can leave the factory to the west, back to Magnolia Street.")
])


street1.add_exits([
    houses.house_door,
    Exit(["pharmacy", "west"], pharmacy, "The west end of the street leads to the pharmacy."),
    Exit(["town", "east"], street2, "The street extends eastwards, towards the rest of the town.")
])

playground_gate = Door(["north", "gate", "playground"], "rose_st.playground",
                       "To the north there is a small gate that connects to the children's playground.", opened=False)
street_gate = playground_gate.reverse_door(["gate", "south"], street2, "The gate that leads back to Magnolia Street is south.")
street2.add_exits([
    Exit(["west"], street1, "The street extends to the west, where your house is."),
    Exit(["east", "crossing"], "rose_st.crossing", "There's a crossing to the east."),
    Exit(["south", "house", "neighbors"], houses.neighbors_house,
         "You can see the house from the neighbors across the street, to the south."),
    playground_gate
])

street3.add_exits([
    Exit(["factory", "east"], factory, "Eastwards you'll enter the ArtiGrow factory area."),
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
