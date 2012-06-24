"""
The Wizard Tower, which is the place where Wizards start/log in

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division, unicode_literals
import random
from tale.base import Location, Exit, Item, heartbeat
from tale.npc import Monster


hall = Location("Main hall of the Tower of Magic",
    """
    The main hall of this ancient wizard tower sparkles with traces of magic.
    Everything seems to glow a little from within. You can hear a very faint hum.
    """)
table = Item("table", "oak table", "A large dark table with a lot of cracks in its surface.")
key = Item("key", "rusty key", "An old rusty key without a label.")


@heartbeat
class Drone(Monster):
    def heartbeat(self, ctx):
        if random.random() < 0.1:
            self.location.tell("The drone hums softly.")

drone = Drone("drone", "n", race="bot", title="mindless drone", description="A stupid metallic drone. It just hovers here with no apparent reason.")
hall.init_inventory([table, key, drone])

attic = Location("Tower attic",
    """
    The dark and dusty attic of the wizard tower.
    There are piles of old scrolls and assorted stuff here of which you assume
    it once held great magical power. All of it is now covered with a thick
    layer of dust.
    """)

kitchen = Location("Tower kitchen",
    """
    A cozy little kitchen for hungry wizards.
    Magically conjured food often tastes like cardboard, so even wizards need to
    prepare their meals the old-fashioned way. The kitchen looks small but tidy.
    """)

hall.exits["up"] = Exit(attic, "A small ladder leads up through a hole in the ceiling.")
hall.exits["ladder"] = hall.exits["up"]
hall.exits["door"] = Exit("town.lane", "A heavy wooden door to the east blocks the noises from the street outside.")
hall.exits["east"] = hall.exits["door"]
hall.exits["north"] = Exit(kitchen, "A door to the north leads to the kitchen.")
kitchen.exits["south"] = Exit(hall, "A door to the south leads back to the hall.")

attic.exits["down"] = Exit(hall, "A small ladder leads back down to the hall.")
attic.exits["ladder"] = attic.exits["down"]
