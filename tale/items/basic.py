"""
A couple of basic items that go beyond the few base types.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import textwrap
from typing import NamedTuple, FrozenSet, Optional, Union, List

from .. import lang, mud_context
from ..base import Item, Container, Weapon, Living, ParseResult
from ..errors import ActionRefused, TaleError


__all__ = ["Boxlike", "Drink", "Food", "GameClock", "Light", "MagicItem", "Money",
           "Note", "Potion", "Scroll", "Trash", "Boat", "Wearable", "Fountain"]


class Boxlike(Container):
    """
    Container base class/prototype. The container can be opened/closed.
    Only if it is open you can put stuff in it or take stuff out of it.
    You can set a couple of txt attributes that change the visual aspect of this object.
    """
    def init(self) -> None:
        super().init()
        self.opened = False
        self.txt_title_closed = self._title
        self.txt_title_open_filled = "filled " + self._title
        self.txt_title_open_empty = "empty " + self._title
        self.txt_descr_closed = "The lid is closed."
        self.txt_descr_open_filled = "It is a %s, with an open lid, and there's something in it." % self.name
        self.txt_descr_open_empty = "It is a %s, with an open lid." % self.name

    def allow_item_move(self, actor: Living, verb: str="move") -> None:
        raise ActionRefused("You can't %s %s." % (verb, self.title))

    @property
    def title(self) -> str:
        if self.opened:
            return self.txt_title_open_filled if self.inventory_size else self.txt_title_open_empty
        else:
            return self.txt_title_closed

    @title.setter
    def title(self, value: str) -> None:
        raise TaleError("you cannot set the title of a Boxlike because it is dynamic")

    @property
    def description(self) -> str:
        if self.opened:
            if self.inventory_size:
                return self.txt_descr_open_filled
            else:
                return self.txt_descr_open_empty
        else:
            return self.txt_descr_closed

    @description.setter
    def description(self, value: str) -> None:
        raise TaleError("you cannot set the description of a Boxlike because it is dynamic")

    def open(self, actor: Living, item: Item=None) -> None:
        if self.opened:
            raise ActionRefused("It's already open.")
        self.opened = True
        actor.tell("You opened the %s." % self.name)
        actor.tell_others("{Actor} opened the %s." % self.name)

    def close(self, actor: Living, item: Item=None) -> None:
        if not self.opened:
            raise ActionRefused("It's already closed.")
        self.opened = False
        actor.tell("You closed the %s." % self.name)
        actor.tell_others("{Actor} closed the %s." % self.name)

    @property
    def inventory(self) -> FrozenSet[Item]:
        if self.opened:
            return super().inventory
        else:
            raise ActionRefused("You can't peek inside, maybe you should open it first?")

    @property
    def inventory_size(self) -> int:
        if self.opened:
            return super().inventory_size
        else:
            raise ActionRefused("You can't peek inside, maybe you should open it first?")

    def insert(self, item: Union[Living, Item], actor: Optional[Living]) -> None:
        if self.opened:
            super().insert(item, actor)
        else:
            raise ActionRefused("You can't put things in the %s: you should open it first." % self.title)

    def remove(self, item: Union[Living, Item], actor: Optional[Living]) -> None:
        if self.opened:
            super().remove(item, actor)
        else:
            raise ActionRefused("You can't take things from the %s: you should open it first." % self.title)


class GameClock(Item):
    """
    A clock that is able to tell you the in-game time.
    """
    def init(self) -> None:
        super().init()
        self.use_locale = True

    @property
    def description(self) -> str:
        if mud_context.config.display_gametime:
            if self.use_locale:
                display = mud_context.driver.game_clock.clock.strftime("%c")
            else:
                display = mud_context.driver.game_clock.clock.strftime("%Y-%m-%d %H:%M:%S")
            return "It reads: " + display
        else:
            return "It looks broken."

    @description.setter
    def description(self, value: str) -> None:
        raise TaleError("you cannot set the description of a GameClock because it is dynamic")

    def activate(self, actor: Living) -> None:
        raise ActionRefused("It's already running.")

    def deactivate(self, actor: Living) -> None:
        raise ActionRefused("Better to keep it running as it is.")

    def manipulate(self, verb: str, actor: Living) -> None:
        actor.tell("%s the %s won't have much effect." % (lang.capital(lang.fullverb(verb)), self.title))

    def read(self, actor: Living) -> None:
        actor.tell(self.description)


class Note(Item):
    """
    A (paper) note with or without something written on it. You can read it.
    """
    def init(self) -> None:
        super().init()
        self._text = "There is nothing written on it."

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = textwrap.dedent(text)

    def read(self, actor: Living) -> None:
        actor.tell("The %s reads:" % self.title, end=True)
        actor.tell(self.text)


class Light(Item):
    def init(self) -> None:
        super().init()
        self.capacity = 0   # hours (-1=eternal, 0=burned out)


class Scroll(Item):
    def init(self) -> None:
        super().init()
        self.spell_level = 0   # level of spells
        self.spells = frozenset()   # type: FrozenSet[str]

    def read(self, actor: Living) -> None:
        actor.tell("The %s reads:" % self.title, end=True)
        actor.tell("It contains the following spells: " + str(self.spells))   # @todo spell descriptions


class MagicItem(Weapon):
    def init(self) -> None:
        super().init()
        self.spell_level = 0
        self.capacity = 0
        self.remaining = 0
        self.spell = None


class Trash(Item):
    """Trash -- junked by cleaners, not bought by any shopkeeper."""
    pass


class Drink(Item):
    drinkeffects = NamedTuple("drinkeffects", [("drunkness", int), ("fullness", int), ("thirst", int)])
    drinktypes = {'water':        drinkeffects(0, 1, 10),
                  'beer':         drinkeffects(3, 2, 5),
                  'wine':         drinkeffects(5, 2, 5),
                  'ale':          drinkeffects(2, 2, 5),
                  'darkale':      drinkeffects(1, 2, 5),
                  'whisky':       drinkeffects(6, 1, 4),
                  'lemonade':     drinkeffects(0, 1, 8),
                  'firebreath':   drinkeffects(10, 0, 0),
                  'localspecial': drinkeffects(3, 3, 3),
                  'slime':        drinkeffects(0, 4, -8),
                  'milk':         drinkeffects(0, 3, 6),
                  'tea':          drinkeffects(0, 1, 6),
                  'coffee':       drinkeffects(0, 1, 6),
                  'blood':        drinkeffects(0, 2, -1),
                  'saltwater':    drinkeffects(0, 1, -2),
                  'clearwater':   drinkeffects(0, 0, 13),
                  }

    def init(self) -> None:
        super().init()
        self.contents = "water"
        self.capacity = 1
        self.quantity = 0
        self.affect_drunkness = 0
        self.affect_fullness = 0
        self.affect_thirst = 0
        self.poisoned = False


class Potion(Item):
    def init(self) -> None:
        super().init()
        self.spell_level = 0
        self.spells = frozenset()   # type: FrozenSet[str]


class Food(Item):
    def init(self) -> None:
        super().init()
        self.affect_fullness = 0
        self.poisoned = False


class Money(Item):
    def init(self) -> None:
        super().init()
        # the amount of money is stored in item.value


class Boat(Item):
    def init(self) -> None:
        super().init()


class Wearable(Item):
    def init(self) -> None:
        super().init()


class Fountain(Item):
    def init(self) -> None:
        super().init()
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


class WoodenYstick(Item):
    # this Y-stick is part of a catapult .
    def combine(self, other: List[Item], actor: Living) -> Optional[Item]:
        if len(other) == 1:
            thing = other[0]
            if isinstance(thing, ElasticBand):
                # combine elastic band and Y-stick into .... the catapult
                catapult = Catapult("catapult", "flimsy catapult", "A flimsy looking catapult. It looks like it might just work though!")
                catapult.aliases.add("flimsy catapult")
                return catapult
        return None


class ElasticBand(Item):
    # the band is part of a catapult.
    # This is a class to be able to identify items of this type easily when combining stuff.
    pass


class Catapult(Weapon):
    # you can create this directly but it is more fun if it is created by combining a Y-stick and an elastic band.
    def init(self):
        super().init()
        self.verbs = {"shoot": "Fire the weapon!"}

    def handle_verb(self, parsed: ParseResult, actor: Living) -> bool:
        if parsed.verb == "shoot":
            if self in actor:
                actor.tell("While the weapon is fine, you don't have munition. Shooting is not happening.")
                actor.tell_others("{Actor} fiddles a bit with %s %s." % (actor.possessive, self.title))
            else:
                actor.tell("You see the weapon lying there. To use it, you'll have to pick it up first though.")
            return True
        return False


woodenYstick = WoodenYstick("stick", "wooden y-shaped stick", "A firm, Y-shaped wooden stick. You can hold it pretty comfortably.")
elastic_band = ElasticBand("band", "large elastic band", "It is a pretty strong and large elastic band. "
                                                         "It's not the type used to hold small packages but rather looks "
                                                         "like it came off a catapult of some sort.")
elastic_band.aliases.add("elastic")
elastic_band.aliases.add("elastic band")
