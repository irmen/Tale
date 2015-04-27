"""
Basic items.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import textwrap
from ..base import Item, Container
from ..errors import ActionRefused
from .. import lang, mud_context


class Boxlike(Container):
    """
    Container base class/prototype. The container can be opened/closed.
    Only if it is open you can put stuff in it or take stuff out of it.
    You can set a couple of txt attributes that change the visual aspect of this object.
    """
    def init(self):
        super(Boxlike, self).init()
        self.opened = False
        self.txt_title_closed = self._title
        self.txt_title_open_filled = "filled " + self._title
        self.txt_title_open_empty = "empty " + self._title
        self.txt_descr_closed = "It looks old. The lid is closed."
        self.txt_descr_open_filled = "It is a %s, with an open lid, and there's something in it." % self.name
        self.txt_descr_open_empty = "It is a %s, with an open lid." % self.name

    def allow_item_move(self, actor, verb="move"):
        raise ActionRefused("You can't %s %s." % (verb, self.title))

    @property
    def title(self):
        if self.opened:
            return self.txt_title_open_filled if self.inventory_size else self.txt_title_open_empty
        else:
            return self.txt_title_closed

    @property
    def description(self):
        if self.opened:
            if self.inventory_size:
                return self.txt_descr_open_filled
            else:
                return self.txt_descr_open_empty
        else:
            return self.txt_descr_closed

    def open(self, actor, item=None):
        if self.opened:
            raise ActionRefused("It's already open.")
        self.opened = True
        actor.tell("You opened the %s." % self.name)
        actor.tell_others("{Title} opened the %s." % self.name)

    def close(self, actor, item=None):
        if not self.opened:
            raise ActionRefused("It's already closed.")
        self.opened = False
        actor.tell("You closed the %s." % self.name)
        actor.tell_others("{Title} closed the %s." % self.name)

    @property
    def inventory(self):
        if self.opened:
            return super(Boxlike, self).inventory
        else:
            raise ActionRefused("You can't peek inside, maybe you should open it first?")

    @property
    def inventory_size(self):
        if self.opened:
            return super(Boxlike, self).inventory_size
        else:
            raise ActionRefused("You can't peek inside, maybe you should open it first?")

    def insert(self, item, actor):
        if self.opened:
            super(Boxlike, self).insert(item, actor)
        else:
            raise ActionRefused("You can't put things in the %s: you should open it first." % self.title)

    def remove(self, item, actor):
        if self.opened:
            super(Boxlike, self).remove(item, actor)
        else:
            raise ActionRefused("You can't take things from the %s: you should open it first." % self.title)


class GameClock(Item):
    def init(self):
        super(GameClock, self).init()
        self.use_locale = True

    @property
    def description(self):
        if mud_context.config.display_gametime:
            if self.use_locale:
                display = mud_context.driver.game_clock.clock.strftime("%c")
            else:
                display = mud_context.driver.game_clock.clock.strftime("%Y-%m-%d %H:%M:%S")
            return "It reads: " + display
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
    def init(self):
        super(Newspaper, self).init()
        self.article = '''
        "Last year's Less Popular Sports."
        "Any fan will tell you the big-name leagues aren't the whole sporting world.
         As time expired on last year, we take a look at major accomplishments, happenings,
         and developments in the less popular sports."
        It looks like a boring article, you have better things to do.
        '''
        self.article = textwrap.dedent(self.article)

    def read(self, actor):
        actor.tell("The newspaper reads:", end=True)
        actor.tell(self.article)


newspaper = Newspaper("newspaper", description="Reading the date, you see it is last week's newspaper. It smells of fish.")
rock = Item("rock", "large rock", "A pretty large rock. It looks extremely heavy.")
gem = Item("gem", "sparkling gem", "Light sparkles from this beautiful gem.")
pouch = Container("pouch", "small leather pouch", "It is opened and closed with a thin leather strap.")
trashcan = Boxlike("trashcan", "dented steel trashcan")
gameclock = GameClock("clock")
