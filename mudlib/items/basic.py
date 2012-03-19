"""
Basic items.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from ..baseobjects import Item, Container
from ..errors import ActionRefused


class FixedItem(Container):  # something that cannot be picked up
    def allow(self, action, item, actor):
        if action == "take":
            if item:
                return      # taking something from the container is ok
            else:
                raise ActionRefused("You can't pick up %s." % self.title)
        else:
            super(FixedItem, self).allow(action, item, actor)


newspaper = Item("newspaper", description="Reading the date, you see it is last week's newspaper. It smells funky too.")
rock = Item("rock", "large rock", "A pretty large rock. It looks extremely heavy.")
gem = Item("gem", "sparkling gem", "Light sparkles from this beautiful red gem.")
pouch = Container("pouch", "small leather pouch", "It is closed with a leather strap.")
trashcan = FixedItem("trashcan", "dented steel trashcan", description="A steel trash can, looking worn. The lid is closed, probably for the better.")
