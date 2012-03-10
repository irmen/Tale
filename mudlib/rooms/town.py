# The central town,
# which is the place where mud players start/log in

from ..baseobjects import Location, Exit, ExitStub
from ..npc import NPC, Monster

square = Location("Essglen Town square",
    """
    The old town square of Essglen. It is not much really, and narrow
    streets quickly lead away from the small fountain in the center.
    """)

lane = Location("Lane of Magicks",
    """
    A long straight road leading to the horizon. Apart from a nearby small tower,
    you can't see any houses or other landmarks. The road seems to go on forever though.
    """)

square.exits["north"] = Exit(lane, "A long straight lane leads north towards the horizon.")
square.exits["lane"] = square.exits["north"]

lane.exits["south"] = Exit(square, "The town square lies to the south.")
lane.exits["west"] = ExitStub("wizardtower.hall", "To the west is the wizard's tower.")

towncrier = NPC("laish", "f", "Laish the town crier",
    """
    The town crier of Essglen is awfully quiet today. She seems rather preoccupied with something.
    """)
idiot = NPC("idiot", "m", "blubbering idiot",
    """
    This person's engine is running but there is nobody behind the wheel.
    He is a few beers short of a six-pack. Three ice bricks shy of an igloo.
    Not the sharpest knife in the drawer. Anyway you get the idea: it's an idiot.
    """)
rat = Monster("rat", "n", "rodent", None,
    """
    A filthy looking rat. Its whiskers tremble slightly as it peers back at you.
    """,)

square.enter(towncrier)
square.enter(idiot)
square.enter(rat)
