"""
The central town, which is the place where mud players start/log in

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import copy
from ..baseobjects import Location, Exit, Item
from ..npc import NPC, Monster
from ..errors import ActionRefused
from ..items.basic import trashcan, newspaper

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

paper = copy.copy(newspaper)
paper.aliases = {"paper"}
square.enter(paper)
square.enter(trashcan)

lane.exits["south"] = Exit(square, "The town square lies to the south.")


class WizardTowerEntry(Exit):
    def allow(self, actor):
        if "wizard" in actor.privileges:
            actor.tell("You pass through the force-field.")
        else:
            raise ActionRefused("You can't go that way, the force-field is impenetrable.")

lane.exits["west"] = WizardTowerEntry("wizardtower.hall", "To the west is the wizard's tower. It seems to be protected by a force-field.")

towncrier = NPC("laish", "f", "Laish the town crier",
    """
    The town crier of Essglen is awfully quiet today. She seems rather preoccupied with something.
    """)
towncrier.aliases = {"crier"}
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

ant = NPC("ant", "n", race="insect")

square.enter(towncrier)
square.enter(idiot)
square.enter(rat)
square.enter(ant)
