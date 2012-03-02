import textwrap
import mudlib.languagetools as lang
from mudlib.races import races

"""
object hierarchy:

MudObject
  |
  +-- Thing
  |     |
  |     +-- Item
  |           |
  |           +-- Weapon
  |           +-- Armour
  |
  +-- Living
  |     |
  |     +-- Player
  |     +-- NPC
  |          |
  |          +-- Monster
  |
  +-- Container
        |
        +-- Bag
        +-- Location

Exit
ExitStub
Effect

"""


class MudObject(object):
    """
    Root class of all objects in the mud world
    All objects have an identifying short name,
    an optional short title (shown when listed in a room),
    and an optional longer description (shown when explicitly 'examined').
    The long description is 'dedented' first, which means you can put it between triple-quoted-strings easily.
    """
    def __init__(self, name, title=None, description=None):
        self.name = name
        self.title = title or name
        if description:
            self.description = textwrap.dedent(description).strip()
        else:
            self.description = self.title

    def __repr__(self):
        clazz = type(self).__name__
        return "<%s '%s' (%s) at %s>" % (clazz, self.name, self.title, hex(id(self)))


class Item(MudObject):
    """
    Root class of all Items in the mud world. Items are physical objects.
    Items can usually be moved, carried, or put inside other items.
    They have a name and optional short and longer descriptions.
    They are always inside a Container, or in an itemslot on another MudObject.
    """
    def __init__(self, name, title=None, description=None):
        super(Item, self).__init__(name, title, description)


class Weapon(Item):
    """
    An item that can be wielded by a Living (i.e. present in a weapon itemslot),
    and that can be used to attack another Living.
    """
    def __init__(self, name, title=None, description=None):
        super(Weapon, self).__init__(name, title, description)


class Armour(Item):
    """
    An item that can be worn by a Living (i.e. present in an armour itemslot)
    """
    def __init__(self, name, title=None, description=None):
        super(Armour, self).__init__(name, title, description)


class Living(MudObject):
    """
    Root class of the living entities in the mud world.
    Livings tend to have a heart beat 'tick' that makes them interact with the world (or a callback).
    They are always inside a Location.
    """
    def __init__(self, name, gender=None, title=None, description=None, race=None):
        super(Living, self).__init__(name, title, description)
        self.gender = gender
        self.subjective = lang.SUBJECTIVE[self.gender]
        self.possessive = lang.POSSESSIVE[self.gender]
        self.objective = lang.OBJECTIVE[self.gender]
        self.location = None
        self.race = None
        self.stats = {}
        if race:
            self.set_race(race)

    def set_race(self, race):
        """set the race for this Living and copy the initial set of stats from that race"""
        self.race = races[race]
        self.stats = {}
        for stat_name, (stat_avg, stat_class) in self.race["stats"].items():
            self.stats[stat_name] = stat_avg


class Container(MudObject):
    """
    Root class for anything that can contain other MudObjects (in the most abstract sense)
    """
    def __init__(self, name, title=None, description=None):
        super(Container, self).__init__(name, title, description)


class Bag(Item, Container):
    """
    A bag-type container (i.e. an item that acts as a container)
    This can be inside another Container by itself.
    """
    def __init__(self, name, title=None, description=None):
        super(Bag, self).__init__(name, title, description)


class Location(Container):
    """
    A location in the mud world. Livings and Items are in it.
    Has connections ('exits') to other Locations.
    """
    def __init__(self, name, description=None):
        super(Location, self).__init__(name, description=description)
        self.livings = set()  # set of livings
        self.items = []       # sequence of all items in the room
        self.exits = {}       # dictionary of all exits: exit_direction -> Exit object with target & descr

    def look(self, short=False):
        """returns a string describing the surroundings"""
        r = ["[" + self.name + "]"]
        if self.description:
            if not short:
                r.append(self.description)
        if self.items:
            if short:
                item_names = sorted(item.name for item in self.items)
                r.append("You see: " + ", ".join(item_names))
            else:
                titles = sorted(item.title for item in self.items)
                titles = [lang.a(title) for title in titles]
                r.append("You see " + lang.join(titles) + ".")
        if self.exits:
            # r.append("You can see the following exits:")
            if short:
                r.append("Exits: " + ", ".join(sorted(set(self.exits.keys()))))
            else:
                exits_seen=set()
                for exit_name in sorted(self.exits):
                    exit = self.exits[exit_name]
                    if exit not in exits_seen:
                        exits_seen.add(exit)
                        r.append(exit.description)
        if self.livings:
            if short:
                living_names = sorted(living.name for living in self.livings)
                r.append("Present: " + ", ".join(living_names))
            else:
                titles = sorted(living.title for living in self.livings)
                titles = lang.join(titles)
                if len(self.livings) > 1:
                    titles += " are here."
                else:
                    titles += " is here."
                r.append(lang.capital(titles))
        return "\n".join(r)


class Exit(object):
    """
    An 'exit' that connects one location to another.
    """
    def __init__(self, target_location, description):
        if type(target_location) is not Location:
            raise TypeError("target of Exit must be a Location")
        self.target = target_location
        self.description = description


class ExitStub(object):
    """
    An 'exit' that connects one location to another.
    This one is a stub in the sense that the target location is not
    the actual location, but a string path to it so that it can be
    retrieved at runtime.
    """
    def __init__(self, target_location_name, description):
        if type(target_location_name) is not str:
            raise TypeError("target of ExitStub must be a str")
        self.target = target_location_name
        self.description = description


class Effect(object):
    """
    An abstract effect or alteration that is present on or in another object.
    This could be a curse or buff, or some other spell effect such as darkness.
    """
    def __init__(self, name, description=None):
        self.name = name
        self.description = description
