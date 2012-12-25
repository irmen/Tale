"""
The house, where the player starts the game
"""

from __future__ import absolute_import, print_function, division, unicode_literals
from tale.base import Location, Exit, Door

# define the locations

class GameEnd(Location):
    def init(self):
        pass

    def notify_player_arrived(self, player, previous_location):
        # player has entered!
        player.story_completed()

livingroom = Location("Living room", "The living room in your home in the outskirts of the city.")
room1 = Location("Small room", "A small room.")
room2 = Location("Large room", "A large room.")
outside = GameEnd("Outside", "You escaped the house.")


# define the exits that connect the locations

livingroom.add_exits([
    Exit("small room", room1, "There's a small room in your house."),
    Exit("large room", room2, "There's a large room in your house."),
    Door("door", outside, "A door leads to the garden.", "There's a heavy door here that leads to the garden outside the house.", opened=False)
])
room1.add_exits([Exit("living room", livingroom, "You can see the living room.")])
room2.add_exits([Exit("living room", livingroom, "You can see the living room.")])
