# coding=utf-8
"""
A couple of basic items that go beyond the few base types.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import textwrap
from collections import namedtuple
from ..base import Item, Container, Weapon
from ..errors import ActionRefused
from .. import lang, mud_context


__all__ = ["Boxlike", "Drink", "Food", "GameClock", "Light", "MagicItem", "Money",
           "Note", "Potion", "Scroll", "Trash", "Boat", "Wearable", "Fountain" ]


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
        self.txt_descr_closed = "The lid is closed."
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
    """
    A clock that is able to tell you the in-game time.
    """
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


class Note(Item):
    """
    A (paper) note with or without something written on it. You can read it.
    """
    def init(self):
        super(Note, self).init()
        self._text = "There is nothing written on it."

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = textwrap.dedent(text)

    def read(self, actor):
        actor.tell("The %s reads:" % self.title, end=True)
        actor.tell(self.text)


class Light(Item):
    def init(self):
        super(Light, self).init()
        self.capacity = 0   # hours (-1=eternal, 0=burned out)


class Scroll(Item):
    def init(self):
        super(Scroll, self).init()
        self.spell_level = 0   # level of spells
        self.spells = set()

    def read(self, actor):
        actor.tell("The %s reads:" % self.title, end=True)
        actor.tell(self.spells)   # @todo spell descriptions


class MagicItem(Weapon):
    def init(self):
        super(MagicItem, self).init()
        self.spell_level = 0
        self.capacity = 0
        self.remaining = 0
        self.spell = None


class Trash(Item):
    """Trash -- junked by cleaners, not bought by any shopkeeper."""
    pass


class Drink(Item):
    drinkeffects = namedtuple("drinkeffects", ["drunkness", "fullness", "thirst"])
    drinktypes = { 'water':         drinkeffects( 0, 1, 10),
                   'beer':          drinkeffects( 3, 2, 5),
                   'wine':          drinkeffects( 5, 2, 5),
                   'ale':           drinkeffects( 2, 2, 5),
                   'darkale':       drinkeffects( 1, 2, 5),
                   'whisky':        drinkeffects( 6, 1, 4),
                   'lemonade':      drinkeffects( 0, 1, 8),
                   'firebreath':    drinkeffects(10, 0, 0),
                   'localspecial':  drinkeffects( 3, 3, 3),
                   'slime':         drinkeffects( 0, 4, -8),
                   'milk':          drinkeffects( 0, 3, 6),
                   'tea':           drinkeffects( 0, 1, 6),
                   'coffee':        drinkeffects( 0, 1, 6),
                   'blood':         drinkeffects( 0, 2, -1),
                   'saltwater':     drinkeffects( 0, 1, -2),
                   'clearwater':    drinkeffects( 0, 0, 13),
                   }

    def init(self):
        super(Drink, self).init()
        self.contents = "water"
        self.capacity = 1
        self.quantity = 0
        self.affect_drunkness = 0
        self.affect_fullness = 0
        self.affect_thirst = 0
        self.poisoned = False


class Potion(Item):
    def init(self):
        super(Potion, self).init()
        self.spell_level = 0
        self.spells = set()


class Food(Item):
    def init(self):
        super(Food, self).init()
        self.affect_fullness = 0
        self.poisoned = False


class Money(Item):
    def init(self):
        super(Money, self).init()
        # the amount of money is stored in item.value


class Boat(Item):
    def init(self):
        super(Boat, self).init()


class Wearable(Item):
    def init(self):
        super(Wearable, self).init()


class Fountain(Item):
    def init(self):
        super(Fountain, self).init()
        self.contents = "water"
        self.capacity = 1
        self.quantity = 0
        self.poisoned = False


newspaper = Note("newspaper", description="""
    Looking at the date on the front page, you see that it is last week's newspaper.
    Perhaps by reading the paper you can see if it still has something interesting to say.
    The paper faintly smells of fish though.""")
newspaper.text = """
        "Last year's Less Popular Sports."
        "Any fan will tell you the big-name leagues aren't the whole sporting world.
         As time expired on last year, we take a look at major accomplishments, happenings,
         and developments in the less popular sports."
        It looks like a boring article, and you have better things to do."""
newspaper.aliases.add("paper")

rock = Item("rock", "large rock", "A pretty large rock. It looks extremely heavy.")
gem = Item("gem", "sparkling gem", "Light sparkles from this beautiful gem.")
diamond = Item("diamond", "large blinking diamond", "This is the biggest diamond you have ever seen.")
pouch = Container("pouch", "small leather pouch", "It is opened and closed with a thin leather strap.")
trashcan = Boxlike("trashcan", "dented steel trashcan")
gameclock = GameClock("clock", title="ticking clock", short_description="The clock makes ticking noises.")
