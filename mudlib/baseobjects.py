import languagetools
import races

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
    All objects have an identifying short name, and an optional longer description.
    """
    def __init__(self, name, description=None):
        self.name = name
        self.description = description or languagetools.a(name)

    def __repr__(self):
        clazz = type(self).__name__
        return "<%s '%s' at %s>" % (clazz, self.name, hex(id(self)))


class Thing(MudObject):
    """
    Root class of all 'things' in the mud world.
    Things have a name and an optional longer description.
    """
    def __init__(self, name, description=None, visible=True):
        super(Thing, self).__init__(name, description)
        self.visible = visible


class Item(Thing):
    """
    Root class of all Items in the mud world. Items are physical objects.
    Items can usually be moved, carried, or put inside other items.
    They have a name and an optional longer description.
    They are always inside a Container, or in an itemslot on another MudObject.
    """
    def __init__(self, name, description=None):
        super(Item, self).__init__(name, description)


class Weapon(Item):
    """
    An item that can be wielded by a Living (i.e. present in a weapon itemslot),
    and that can be used to attack another Living.
    """
    def __init__(self, name, description=None):
        super(Weapon, self).__init__(name, description)


class Armour(Item):
    """
    An item that can be worn by a Living (i.e. present in an armour itemslot)
    """
    def __init__(self, name, description=None):
        super(Armour, self).__init__(name, description)


class Living(MudObject):
    """
    Root class of the living entities in the mud world.
    Livings tend to have a heart beat 'tick' that makes them interact with the world (or a callback).
    They are always inside a Location.
    """
    def __init__(self, name, gender=None, description=None, race=None):
        super(Living, self).__init__(name, description)
        self.display_name = self.name
        self.gender = gender
        self.subjective = languagetools.SUBJECTIVE[self.gender]
        self.possessive = languagetools.POSSESSIVE[self.gender]
        self.objective = languagetools.OBJECTIVE[self.gender]
        self.location = None
        self.race = None
        self.stats = {}
        if race:
            self.set_race(race)

    def set_race(self, race):
        """set the race for this Living and copy the initial set of stats from that race"""
        self.race = races.races[race]
        self.stats = {}
        for stat_name, (stat_avg, stat_class) in self.race["stats"].items():
            self.stats[stat_name] = stat_avg


class Container(MudObject):
    """
    Root class for anything that can contain other MudObjects (in the most abstract sense)
    """
    def __init__(self, name, description=None):
        super(Container, self).__init__(name, description)


class Bag(Item, Container):
    """
    A bag-type container (i.e. an item that acts as a container)
    This can be inside another Container by itself.
    """
    def __init__(self, name, description=None):
        super(Bag, self).__init__(name, description)


class Location(Container):
    """
    A location in the mud world. Livings and Items are in it.
    Has connections ('exits') to other Locations.
    """
    def __init__(self, name, description=None):
        super(Location, self).__init__(name, description)
        self.livings = set()  # set of livings
        self.items = []       # sequence of all items in the room
        self.exits = {}       # dictionary of all exits: exit_direction -> Exit object with target & descr

    def look(self):
        """returns a string describing the surroundings"""
        r = ["[" + self.name + "]", self.description if self.description else "You see nothing special about it."]
        if self.items:
            itemnames = sorted([item.name for item in self.items if item.visible])
            itemnames = [languagetools.a(name) for name in itemnames]
            r.append("You see " + languagetools.join(itemnames) + ".")
        if self.exits:
            r.append("You can see the following exits:")
            exits_seen=set()
            for exitname in sorted(self.exits):
                exit = self.exits[exitname]
                if exit not in exits_seen:
                    exits_seen.add(exit)
                    r.append(exit.description)
        else:
            r.append("There are no obvious exits.")
        if self.livings:
            livings = languagetools.join(sorted(living.name for living in self.livings))
            if len(self.livings) > 1:
                livings += " are here."
            else:
                livings += " is here."
            r.append(livings)
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
