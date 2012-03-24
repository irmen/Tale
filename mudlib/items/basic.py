"""
Basic items.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from ..base import Item, Container
from ..errors import ActionRefused


class FixedItem(Container):  # something that cannot be picked up
    def allow_move(self, actor):
        raise ActionRefused("You can't move %s." % self.title)


class TrashCan(FixedItem):
    @property
    def description(self):
        if self.inventory():
            return "It is a stinking trash can, maybe there's something rotten in it?"
        return "It looks worn and rusty."


newspaper = Item("newspaper", description="Reading the date, you see it is last week's newspaper. It smells funky too.")
rock = Item("rock", "large rock", "A pretty large rock. It looks extremely heavy.")
gem = Item("gem", "sparkling gem", "Light sparkles from this beautiful red gem.")
pouch = Container("pouch", "small leather pouch", "It is closed with a leather strap.")
trashcan = TrashCan("trashcan", "dented steel trashcan")
