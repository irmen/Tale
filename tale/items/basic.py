"""
Basic items.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from ..base import Item, Container
from ..errors import ActionRefused
from ..globals import mud_context, DISPLAY_GAMETIME
from .. import lang


class TrashCan(Container):
    def init(self):
        super(TrashCan, self).init()
        self.opened = False

    def allow_move(self, actor):
        raise ActionRefused("You can't move %s." % self.title)

    @property
    def title(self):
        if self.opened:
            return "filled trashcan" if self.inventory_size else "empty trashcan"
        else:
            return "trashcan"

    @property
    def description(self):
        if self.opened:
            if self.inventory_size:
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

    @property
    def inventory(self):
        if self.opened:
            return super(TrashCan, self).inventory
        else:
            raise ActionRefused("You can't peek inside, maybe you should open it first?")

    @property
    def inventory_size(self):
        if self.opened:
            return super(TrashCan, self).inventory_size
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
        if DISPLAY_GAMETIME:
            return "It reads: " + str(mud_context.driver.game_clock)
        else:
            return "It looks broken."

    def activate(self, actor):
        raise ActionRefused("It's already running.")

    def deactivate(self, actor):
        raise ActionRefused("Better to keep it running as it is.")

    def manipulate(self, verb, actor):
        actor.tell("%s the %s won't have much effect." % (lang.capital(lang.fullverb(verb)), self.title))

    def read(self, actor):
        actor.tell(self.description)


class Newspaper(Item):
    def read(self, actor):
        actor.tell("The newspaper reads: \"Last year's Less Popular Sports.\"", end=True)
        actor.tell("\"Any fan will tell you the big-name leagues aren't the whole sporting world. "
            "As time expired on last year, we take a look at major accomplishments, happenings, "
            "and developments in the less popular sports.\"")
        actor.tell("It looks like a boring article, you have better things to do.")


newspaper = Newspaper("newspaper", description="Reading the date, you see it is last week's newspaper. It smells of fish.")
rock = Item("rock", "large rock", "A pretty large rock. It looks extremely heavy.")
gem = Item("gem", "sparkling gem", "Light sparkles from this beautiful red gem.")
pouch = Container("pouch", "small leather pouch", "It is closed with a leather strap.")
trashcan = TrashCan("trashcan", "dented steel trashcan")
worldclock = WorldClock("clock")
