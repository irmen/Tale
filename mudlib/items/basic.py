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
    def __init__(self, name, title=None, description=None):
        super(TrashCan, self).__init__(name, title, description)
        self.opened = False

    @property
    def title(self):
        if self.opened:
            return "filled trashcan" if self.inventory_size() else "empty trashcan"
        else:
            return "trashcan"

    @property
    def description(self):
        if self.opened:
            if self.inventory_size():
                return "It is a trash can, with an open lid, and it stinks!"
            else:
                return "It is a trash can, with an open lid."
        else:
            status = "It's lid is open." if self.opened else "It's closed."
            return "It looks worn and rusty. " + status

    def open(self, item, actor):
        if self.opened:
            raise ActionRefused("It's already open.")
        self.opened = True

    def close(self, item, actor):
        if not self.opened:
            raise ActionRefused("It's already closed.")
        self.opened = False

    def inventory(self):
        if self.opened:
            return super(TrashCan, self).inventory()
        else:
            raise ActionRefused("You can't peek into it, maybe you should open it first?")

    def inventory_size(self):
        if self.opened:
            return super(TrashCan, self).inventory_size()
        else:
            raise ActionRefused("You can't peek into it, maybe you should open it first?")

    def insert(self, item, actor):
        if self.opened:
            super(TrashCan, self).insert(item, actor)
        else:
            raise ActionRefused("You should open it first.")

    def remove(self, item, actor):
        if self.opened:
            super(TrashCan, self).remove(item, actor)
        else:
            raise ActionRefused("You should open it first.")


newspaper = Item("newspaper", description="Reading the date, you see it is last week's newspaper. It smells funky too.")
rock = Item("rock", "large rock", "A pretty large rock. It looks extremely heavy.")
gem = Item("gem", "sparkling gem", "Light sparkles from this beautiful red gem.")
pouch = Container("pouch", "small leather pouch", "It is closed with a leather strap.")
trashcan = TrashCan("trashcan", "dented steel trashcan")
