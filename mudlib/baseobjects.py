"""
Mudlib base objects.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division
import sys
import weakref
import textwrap
from . import languagetools as lang
from .errors import ActionRefused
from .races import races

if sys.version_info < (3, 0):
    basestring_type = basestring
else:
    basestring_type = str

"""
object hierarchy:

MudObject
  |
  +-- Location
  |
  +-- Item
  |     |
  |     +-- Weapon
  |     +-- Armour
  |     +-- Container
  |
  +-- Living
  |     |
  |     +-- Player
  |     +-- NPC
  |          |
  |          +-- Monster


Exit
  |
  +-- Door

Effect


Every object that can hold other objects does so in its "inventory" attribute (a set).
Except Location: it separates the items and livings it contains internally. Use its enter/leave methods.
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
        self.aliases = []
        self.title = title or name
        self.description = textwrap.dedent(description).strip() if description else ""

    def __repr__(self):
        return "<%s.%s '%s' @ 0x%x>" % (self.__class__.__module__, self.__class__.__name__, self.name, id(self))

    def destroy(self, ctx):
        pass


class Item(MudObject):
    """
    Root class of all Items in the mud world. Items are physical objects.
    Items can usually be moved, carried, or put inside other items.
    They have a name and optional short and longer descriptions.
    You can test for containment with 'in': item in bag (but the containment
    is always empty and so it will always return False for a regular Item)
    """
    def __init__(self, name, title=None, description=None):
        super(Item, self).__init__(name, title, description)
        self.inventory = frozenset()   # override this with set() to allow inventory modification

    def __contains__(self, item):
        return item in self.inventory

    def allow_take(self, actor):
        """Does it allow to be taken? (yes, no ActionRefused raised)"""
        pass

    def allow_put(self, target, actor):
        """Does it allow to be put inside something else? (yes, ActionRefused not raised)"""
        pass

    def allow_examine_inventory(self, actor):
        """Does it allow someone to look inside its inventory/contents? (no, raises ActionRefused)"""
        raise ActionRefused("You can't see what's in there.")

    def allow_remove(self, item, actor):
        """Does it allow something to be taken out of it? (no, raises ActionRefused)"""
        raise ActionRefused("You can't take things from there.")

    def allow_insert(self, item, actor):
        """Does it allow something to be inserted into it? (no, raises ActionRefused)"""
        raise ActionRefused("You can't put things in there.")

    def open(self, item, actor):
        raise ActionRefused("You can't open that.")

    def close(self, item, actor):
        raise ActionRefused("You can't close that.")

    def lock(self, item, actor):
        raise ActionRefused("You can't lock that.")

    def unlock(self, item, actor):
        raise ActionRefused("You can't unlock that.")


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


class Location(MudObject):
    """
    A location in the mud world. Livings and Items are in it.
    Has connections ('exits') to other Locations.
    You can test for containment with 'in': item in loc, npc in loc
    """
    def __init__(self, name, description=None):
        super(Location, self).__init__(name, description=description)
        self.livings = set()  # set of livings in this location
        self.items = set()  # set of all items in the room
        self.exits = {}       # dictionary of all exits: exit_direction -> Exit object with target & descr
        self.wiretaps = weakref.WeakSet()     # wizard wiretaps for this location

    def __contains__(self, obj):
        return obj in self.livings or obj in self.items

    def destroy(self, ctx):
        for living in self.livings:
            if living.location is self:
                living.location = _Limbo
        self.livings.clear()
        self.items.clear()
        self.exits.clear()
        self.wiretaps.clear()

    def add_exits(self, exits):
        """
        Adds every exit from the sequence as an exit to this room.
        It is required that the exits have their direction attribute set.
        """
        for exit in exits:
            if exit.direction:
                self.exits[exit.direction] = exit
            else:
                raise ValueError("exit.direction must be specified: " + str(exit))

    def tell(self, room_msg, exclude_living=None, specific_targets=None, specific_target_msg=""):
        """
        Tells something to the livings in the room (excluding the living from exclude_living).
        This is just the message string! If you want to react on events, consider not doing
        that based on this message string. That will make it quite hard because you need to
        parse the string again to figure out what happened...
        """
        specific_targets = specific_targets or set()
        for living in self.livings:
            if living == exclude_living:
                continue
            if living in specific_targets:
                living.tell(specific_target_msg)
            else:
                living.tell(room_msg)
        if room_msg:
            for tap in self.wiretaps:
                tap.tell(room_msg)

    def look(self, exclude_living=None, short=False):
        """returns a string describing the surroundings, possibly excluding one living from the description list"""
        r = ["[" + self.name + "]"]
        if self.description:
            if not short:
                r.append(self.description)
        if self.exits:
            # r.append("You can see the following exits:")
            if short:
                r.append("Exits: " + ", ".join(sorted(set(self.exits.keys()))))
            else:
                exits_seen = set()
                for exit_name in sorted(self.exits):
                    exit = self.exits[exit_name]
                    if exit not in exits_seen:
                        exits_seen.add(exit)
                        r.append(exit.description)
        if self.items:
            if short:
                item_names = sorted(item.name for item in self.items)
                r.append("You see: " + ", ".join(item_names))
            else:
                titles = sorted(item.title for item in self.items)
                titles = [lang.a(title) for title in titles]
                r.append("You see " + lang.join(titles) + ".")
        if self.livings:
            if short:
                living_names = sorted(living.name for living in self.livings if living != exclude_living)
                if living_names:
                    r.append("Present: " + ", ".join(living_names))
            else:
                titles = sorted(living.title for living in self.livings if living != exclude_living)
                if titles:
                    titles_str = lang.join(titles)
                    if len(titles) > 1:
                        titles_str += " are here."
                    else:
                        titles_str += " is here."
                    r.append(lang.capital(titles_str))
        return "\n".join(r)

    def search_living(self, name):
        """
        Search for a living in this location by its name (and title, if no names match)
        If there's more than one match, returns the first
        """
        name = name.lower()
        result = [living for living in self.livings if living.name == name]
        if not result:
            # try titles an aliases
            result = [living for living in self.livings if name in living.aliases or living.title.lower() == name]
        return result[0] if result else None

    def enter(self, obj, force_and_silent=False):
        """Add obj to the contents of the location (either a Living or an Item)"""
        if isinstance(obj, Living):
            self.livings.add(obj)
            obj.location = self
            if not force_and_silent:
                self.tell("%s arrives." % lang.capital(obj.title), exclude_living=obj)
        elif isinstance(obj, Item):
            self.items.add(obj)
        else:
            raise TypeError("can only contain Living and Item")

    def leave(self, obj, force_and_silent=False):
        """Remove obj from this location (either a Living or an Item)"""
        if obj in self.livings:
            self.livings.remove(obj)
            obj.location = None
            if not force_and_silent:
                self.tell("%s leaves." % lang.capital(obj.title), exclude_living=obj)
        elif obj in self.items:
            self.items.remove(obj)

    def allow_remove(self, item, actor):
        """Allow an item to be taken by an actor? (yes, ActionRefused not raised)"""
        assert item

    def allow_insert(self, item, actor):
        """Does this location allow something to be inserted into it? (yes, ActionRefused not raised)"""
        assert item


_Limbo = Location("Limbo",
                     """
                     The intermediate or transitional place or state. There's only nothingness.
                     Livings end up here if they're not inside a proper location yet.
                     """)


class Exit(object):
    """
    An 'exit' that connects one location to another.
    You can use a Location object as target, or a string designating the location
    (for instance "town.square" means the square location object in mudlib.rooms.town).
    If using a string, it will be retrieved and bound at runtime.
    Supplying a direction on the exit is optional. It is meant to make adding multiple
    exits on a location easier by using Location.add_exits().
    """
    def __init__(self, target_location, description, direction=None):
        assert target_location is not None
        assert isinstance(target_location, (Location, basestring_type)), "target must be a Location or a string"
        self.target = target_location
        self.description = description
        self.bound = isinstance(target_location, Location)
        self.direction = direction

    def __repr__(self):
        targetname = self.target.name if self.bound else self.target
        return "<baseobjects.Exit '%s'->'%s' @ 0x%x>" % (self.direction, targetname, id(self))

    def bind(self, target_location):
        """
        Binds the exit to the actual target_location object.
        Usually called by a movement action on a non-bound exit.
        """
        assert not self.bound and isinstance(target_location, Location)
        self.target = target_location
        self.bound = True

    def allow_move(self, actor):
        """Is the actor allowed to move through the exit? Raise ActionRefused if not"""
        assert self.bound

    def open(self, item, actor):
        raise ActionRefused("You can't open that.")

    def close(self, item, actor):
        raise ActionRefused("You can't close that.")

    def lock(self, item, actor):
        raise ActionRefused("You can't lock that.")

    def unlock(self, item, actor):
        raise ActionRefused("You can't unlock that.")


class Living(MudObject):
    """
    Root class of the living entities in the mud world.
    Livings tend to have a heart beat 'tick' that makes them interact with the world (or a callback).
    They are always inside a Location (Limbo when not specified yet).
    They also have an inventory object, and you can test for containment with item in living.
    """
    def __init__(self, name, gender, title=None, description=None, race=None):
        super(Living, self).__init__(name, title, description)
        self.gender = gender
        self.subjective = lang.SUBJECTIVE[self.gender]
        self.possessive = lang.POSSESSIVE[self.gender]
        self.objective = lang.OBJECTIVE[self.gender]
        self.location = _Limbo  # set transitional location
        self.aggressive = False
        self.race = None
        self.stats = {}
        if race:
            self.set_race(race)
        self.inventory = set()
        self.wiretaps = weakref.WeakSet()     # wizard wiretaps for this location
        self.cpr()

    def __contains__(self, item):
        return item in self.inventory

    def destroy(self, ctx):
        if self.location and self in self.location.livings:
            self.location.livings.remove(self)
        self.location = None
        self.inventory.clear()
        self.wiretaps.clear()
        # @todo: remove heartbeat, deferred, attack status, etc.

    def set_race(self, race):
        """set the race for this Living and copy the initial set of stats from that race"""
        self.race = race
        # Make a copy of the race stats, because they can change dynamically.
        # There's no need to copy the whole race data dict because it's available
        # from mudlib.races, look it up by the race name.
        self.stats = {}
        for stat_name, (stat_avg, stat_class) in races[race]["stats"].items():
            self.stats[stat_name] = stat_avg

    def cpr(self):
        """(re)start the living's heartbeat"""
        pass  # do nothing, for now

    def tell(self, *messages):
        """
        Every living thing in the mud can receive one or more action messages.
        For players this is usually printed to their screen, but for all other
        livings the default is to do nothing (only distribute the messages to any
        wiretaps that might be present).
        They could react on it but this is not advisable because you will need
        to parse the string again to figure out what happened...
        """
        for tap in self.wiretaps:
            tap.tell(*messages)

    def move(self, target_location, force_and_silent=False):
        """leave the current location, enter the new location"""
        if self.location:
            self.location.leave(self, force_and_silent)
        target_location.enter(self, force_and_silent)

    def search_item(self, name, include_inventory=True, include_location=True, include_containers_in_inventory=True):
        """
        Searches an item within the 'visible' world around the living including his inventory.
        If there's more than one hit, just return the first.
        This is exactly the same as locate_item except it doesn't return the containing object.
        """
        item, container = self.locate_item(name, include_inventory, include_location, include_containers_in_inventory)
        return item  # skip the container

    def locate_item(self, name, include_inventory=True, include_location=True, include_containers_in_inventory=True):
        """
        Searches an item within the 'visible' world around the living including his inventory.
        If there's more than one hit, just return the first.
        Returns (None,None) or (item, containing_object)
        """
        if not name:
            raise ValueError("name must be given")
        name = name.lower()
        matches = containing_object = None
        if include_inventory:
            containing_object = self
            matches = [item for item in self.inventory if item.name == name]
            if not matches:
                # try the aliases or titles
                matches = [item for item in self.inventory if name in item.aliases or item.title.lower() == name]
        if not matches and include_location:
            containing_object = self.location
            matches = [item for item in self.location.items if item.name == name]
            if not matches:
                # try the aliases or titles
                matches = [item for item in self.location.items if name in item.aliases or item.title.lower() == name]
        if not matches and include_containers_in_inventory:
            # check if an item in the inventory might contain it
            for container in self.inventory:
                containing_object = container
                matches = [item for item in container.inventory if item.name == name]
                if not matches:
                    # try the aliases or titles
                    matches = [item for item in container.inventory if name in item.aliases or item.title.lower() == name]
                if matches:
                    break
        return (matches[0], containing_object) if matches else (None, None)

    def start_attack(self, living):
        """Starts attacking the given living until death ensues on either side."""
        # @todo: I'm not yet sure if the combat/attack logic should go here (on Living), or that it should be split across NPC / Player...
        pass

    def allow_give(self, item, actor):
        """Does this creature allow the actor to give it an item?"""
        assert item
        raise ActionRefused("You can't do that.")

    def allow_remove(self, item, actor):
        """Does this creature allow the actor to remove something from its inventory?"""
        if actor is self:
            pass
        else:
            raise ActionRefused("You can't take %s from %s." % (item.title, self.title))


class Container(Item):
    """
    A bag-type container (i.e. an item that acts as a container)
    Allows insert and remove, and examine its contents, as opposed to an Item
    You can test for containment with 'in': item in bag
    """
    def __init__(self, name, title=None, description=None):
        super(Container, self).__init__(name, title, description)
        self.inventory = set()  # override the frozenset() from Item to allow true containment here

    def allow_examine_inventory(self, actor):
        """Does it allow someone to look inside its inventory/contents? (yes, no ActionRefused raised)"""
        pass

    def allow_remove(self, item, actor):
        assert item

    def allow_insert(self, item, actor):
        assert item


class Effect(object):
    """
    An abstract effect or alteration that is present on or in another object.
    This could be a curse or buff, or some other spell effect such as darkness.
    """
    def __init__(self, name, description=None):
        self.name = name
        self.description = description


class Door(Exit):
    """
    A special exit that connects one location to another but which can be closed or even locked.
    """
    def __init__(self, target_location, description, direction=None, locked=False, opened=True):
        super(Door, self).__init__(target_location, description, direction)
        self.locked = locked
        self.opened = opened

    def __repr__(self):
        target = self.target.name if self.bound else self.target
        locked = "locked" if self.locked else "open"
        return "<baseobjects.Door '%s'->'%s' (%s) @ 0x%x>" % (self.direction, target, locked, id(self))

    def allow_move(self, actor):
        """Is the actor allowed to move through this door?"""
        assert self.bound
        if not self.opened:
            raise ActionRefused("You can't go there; it's closed.")

    def open(self, item, actor):
        """Open the door with optional item"""
        if self.opened:
            raise ActionRefused("It's already open.")
        elif self.locked:
            raise ActionRefused("You can't open it; it's locked.")
        else:
            self.opened = True
            actor.tell("You opened it.")
            who = lang.capital(actor.title)
            if self.direction:
                actor.location.tell("%s opened the exit %s." % (who, self.direction))
            else:
                actor.location.tell("%s opened an exit." % who)

    def close(self, item, actor):
        """Close the door with optional item"""
        if not self.opened:
            raise ActionRefused("It's already closed.")
        self.opened = False
        actor.tell("You closed it.")
        who = lang.capital(actor.title)
        if self.direction:
            actor.location.tell("%s closed the exit %s." % (who, self.direction))
        else:
            actor.location.tell("%s closed an exit." % who)

    def lock(self, item, actor):
        """Lock the door with something, default is to not allow locking (override in subclass)"""
        if self.locked:
            raise ActionRefused("It's already locked.")
        else:
            raise ActionRefused("You can't lock it.")

    def unlock(self, item, actor):
        """Unlock the door with something, default is to not allow unlocking (override in subclass)"""
        if self.locked:
            raise ActionRefused("You can't unlock it.")
        else:
            raise ActionRefused("It's not locked.")
