# The Wizard Tower,
# which is the place where mud Wizards start/log in

from mudlib.baseobjects import Location, Exit

hall = Location("Main hall of the Tower of Magic",
    """The main hall of this ancient wizard tower sparkles with traces of magic.
       Everything seems to glow a little from within. You can hear a very faint hum.""")

attic = Location("Tower attic",
    """The dark and dusty attic of the wizard tower.
       There are piles of old scrolls and assorted stuff here of which you assume
       it once held great magical power. All of it is now covered with a thick
       layer of dust.""")


hall.exits["up"] = Exit(attic, "A small ladder leads up through a hole in the ceiling.")
hall.exits["ladder"] = hall.exits["up"]
