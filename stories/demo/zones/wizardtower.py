"""
The Wizard Tower, which is the place where Wizards start/log in

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import random

from tale import lang, util
from tale.base import Location, Exit, Item, Living


hall = Location("Main hall of the Tower of Magic",
    """
    The main hall of this ancient wizard tower sparkles with traces of magic.
    Everything seems to glow a little from within. You can hear a very faint hum.
    """)
table = Item("table", "oak table", descr="A large dark table with a lot of cracks in its surface.")
key = Item("key", "rusty key", descr="An old rusty key without a label.")


class Drone(Living):
    @util.call_periodically(2)
    def do_whizz(self, ctx: util.Context) -> None:
        rand = random.random()
        if rand < 0.14:
            self.do_socialize("twitch erra")
        elif rand < 0.28:
            self.do_socialize("rotate random")
        elif rand < 0.40:
            self.location.tell("%s hums softly." % lang.capital(self.title))


drone = Drone("drone", "n", race="bot", title="mindless drone",
              descr="A stupid metallic drone. It just hovers here with no apparent reason. It has a little label attached to it.")
drone.add_extradesc({"label"}, "The label reads: \"Wall-E was my cousin\".")
drone.aggressive = True

hall.init_inventory([table, key, drone])

attic = Location("Tower attic",
    """
    The dark and dusty attic of the wizard tower.
    There are piles of old scrolls and assorted stuff here of which you assume
    it once held great magical power. All of it is now covered with a thick
    layer of dust.
    """)
attic.add_extradesc({"dust", "stuff", "scrolls"}, "The scrolls look ancient. One looks like a spell!")
attic.add_extradesc({"spell"}, "The scroll looks like it contains a spell, but on closer inspection, "
                               "it has become too faded to be understood anymore.")


kitchen = Location("Tower kitchen",
    """
    A cozy little kitchen for hungry wizards.
    Magically conjured food often tastes like cardboard, so even wizards need to
    prepare their meals the old-fashioned way. The kitchen looks small but tidy.
    """)

hall.add_exits([
    Exit(["up", "ladder"], attic, "A small ladder leads up through a hole in the ceiling."),
    Exit(["door", "east"], "town.lane", "A heavy wooden door to the east blocks the noises from the street outside."),
    Exit("north", kitchen, "A door to the north leads to the kitchen.")
])

kitchen.add_exits([Exit("south", hall, "A door to the south leads back to the hall.")])
attic.add_exits([Exit(["down", "ladder"], hall, "A small ladder leads back down to the hall.")])
