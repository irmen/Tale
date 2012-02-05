import languagetools

"""
object hierarchy:

MudObject
  |
  +-- Effect
  |
  +-- Item
  |     |
  |     +-- Weapon
  |     +-- Armour
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


"""


class MudObject(object):
    """
    Root class of all objects in the mud world
    All objects have an identifying short name, and an optional longer description.
    """
    def __init__(self, name, description=None):
        self.name = name
        self.description = description or languagetools.a(name)
        self.subjective = None
        self.possessive = None
        self.objective = None

    def __repr__(self):
        clazz = type(self).__name__
        return "<%s '%s' at %s>" % (clazz, self.name, hex(id(self)))


class Effect(MudObject):
    """
    An abstract effect or alteration that is present on or in another object.
    This could be a curse or buff, or some other spell effect such as darkness.
    """
    def __init__(self, name, description=None):
        super(Item, self).__init__(name, description)


class Item(MudObject):
    """
    Root class of all items in the mud world.
    Items have a name and an optional longer description.
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
    Livings tend to have a heart beat 'tick' that makes them interact with the world.
    They are always inside a Location.
    """
    def __init__(self, name, gender=None, description=None):
        super(Living, self).__init__(name, description)
        self.gender = gender
        self.subjective = languagetools.SUBJECTIVE[self.gender]
        self.possessive = languagetools.POSSESSIVE[self.gender]
        self.objective = languagetools.OBJECTIVE[self.gender]


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
