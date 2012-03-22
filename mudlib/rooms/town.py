"""
The central town, which is the place where mud players start/log in

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import copy
from ..baseobjects import Location, Exit, Door, Item, Container
from ..npc import NPC, Monster
from ..errors import ActionRefused
from ..items.basic import trashcan, newspaper, gem

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


class CursedGem(Item):
    def allow_put(self, target, actor):
        raise ActionRefused("The gem is cursed! It sticks to your hand, you can't get rid of it!")


class InsertOnlyBox(Container):
    def __isub__(self, item):
        raise ActionRefused("The box is cursed! You can't take anything out of it!")


class RemoveOnlyBox(Container):
    def __iadd__(self, item):
        raise ActionRefused("No matter how hard you try, you can't fit %s in the box." % item.title)

insertonly_box = InsertOnlyBox("box1", "box1 (a black box)")
removeonly_box = RemoveOnlyBox("box2", "box2 (a white box)")
normal_gem = copy.copy(gem)
removeonly_box.init_inventory([normal_gem])

cursed_gem = CursedGem("gem", "a dark gem")
square.enter(cursed_gem)
square.enter(paper)
square.enter(trashcan)
square.enter(insertonly_box)
square.enter(removeonly_box)

lane.exits["south"] = Exit(square, "The town square lies to the south.")


class WizardTowerEntry(Exit):
    def allow_move(self, actor):
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


alley = Location("Alley of doors", "An alley filled with doors.")
door1 = Door(alley, "door1 (unlocked and open)", direction="door1", locked=False, opened=True)
door2 = Door(alley, "door2 (locked and open)", direction="door2", locked=True, opened=True)
door3 = Door(alley, "door3 (unlocked and closed)", direction="door3", locked=False, opened=False)
door4 = Door(alley, "door4 (locked and closed)", direction="door4", locked=True, opened=False)

alley.add_exits([door1, door2, door3, door4])
alley.exits["north"] = Exit(square, "You can go north which brings you back to the square.")
square.exits["alley"] = Exit(alley, "There's an alley to the south.")
square.exits["south"] = square.exits["alley"]
