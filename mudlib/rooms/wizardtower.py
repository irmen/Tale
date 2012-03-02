# The Wizard Tower,
# which is the place where mud Wizards start/log in

from mudlib.baseobjects import Location, Exit, ExitStub, Item

hall = Location("Main hall of the Tower of Magic",
    """
    The main hall of this ancient wizard tower sparkles with traces of magic.
    Everything seems to glow a little from within. You can hear a very faint hum.
    """)
hall.items += [ Item("table", "oak table", "a large dark table with a lot of cracks in its surface"),
                Item("key", "rusty key", "an old rusty key without a label") ]

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
hall.exits["door"] = ExitStub("town.lane", "A heavy wooden door to the east blocks the noises from the street outside.")
hall.exits["east"] = hall.exits["door"]
hall.exits["north"] = Exit(kitchen, "A door to the north leads to the kitchen.")
kitchen.exits["south"] = Exit(hall, "A door to the south leads back to the hall.")

attic.exits["down"] = Exit(hall, "A small ladder leads back down to the hall.")
attic.exits["ladder"] = attic.exits["down"]

print hall.look()
