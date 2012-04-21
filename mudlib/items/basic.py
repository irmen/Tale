"""
Basic items.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from ..base import Item, Container
from ..errors import ActionRefused
from ..globals import mud_context


class TrashCan(Container):
    def init(self):
        self.opened = False

    def allow_move(self, actor):
        raise ActionRefused("You can't move %s." % self.title)

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
        actor.tell("You opened the %s." % self.title)
        actor.tell_others("{Title} opened the %s." % self.title)

    def close(self, item, actor):
        if not self.opened:
            raise ActionRefused("It's already closed.")
        self.opened = False
        actor.tell("You closed the %s." % self.title)
        actor.tell_others("{Title} closed the %s." % self.title)

    def inventory(self):
        if self.opened:
            return super(TrashCan, self).inventory()
        else:
            raise ActionRefused("You can't peek inside, maybe you should open it first?")

    def inventory_size(self):
        if self.opened:
            return super(TrashCan, self).inventory_size()
        else:
            raise ActionRefused("You can't peek inside, maybe you should open it first?")

    def insert(self, item, actor):
        if self.opened:
            super(TrashCan, self).insert(item, actor)
        else:
            raise ActionRefused("You can't put things in the trashcan: you should open it first.")

    def remove(self, item, actor):
        if self.opened:
            super(TrashCan, self).remove(item, actor)
        else:
            raise ActionRefused("You can't take things from the trashcan: you should open it first.")


class WorldClock(Item):
    @property
    def description(self):
        return "The clock reads " + str(mud_context.driver.game_clock)


newspaper = Item("newspaper", description="Reading the date, you see it is last week's newspaper. It smells of fish.")
rock = Item("rock", "large rock", "A pretty large rock. It looks extremely heavy.")
gem = Item("gem", "sparkling gem", "Light sparkles from this beautiful red gem.")
pouch = Container("pouch", "small leather pouch", "It is closed with a leather strap.")
trashcan = TrashCan("trashcan", "dented steel trashcan")
worldclock = WorldClock("clock")
