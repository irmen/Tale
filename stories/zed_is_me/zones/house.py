"""
The house, where the player starts the game
"""

from __future__ import print_function, division, unicode_literals
from tale.base import Location, Exit, Door


livingroom = Location("Living room", "The living room in your home in the outskirts of the city.")

room1 = Location("Small room", "A small room.")
room2 = Location("Large room", "A large room.")

livingroom.exits["small room"] = Exit(room1, "There's a small room in your house.")
room1.exits["living room"] = Exit(livingroom, "You can see the living room.")
livingroom.exits["large room"] = Exit(room2, "There's a large room in your house.")
room2.exits["living room"] = Exit(livingroom, "You can see the living room.")


class GameEnd(Location):
    def init(self):
        pass

    def notify_player_arrived(self, player, previous_location):
        # player has entered!
        player.story_completed()

outside = GameEnd("Outside", "You escaped the house.")
livingroom.exits["door"] = Door(outside, "A door leads to the garden.", "There's a heavy door here that leads to the garden outside the house.", opened=False)
