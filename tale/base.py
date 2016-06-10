# coding=utf-8
"""
Mudlib base objects.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)

object hierarchy::

    MudObject
      |
      +-- Location
      |
      +-- Item
      |     |
      |     +-- Weapon
      |     +-- Armour
      |     +-- Container
      |     +-- Key
      |
      +-- Living
      |     |
      |     +-- Player
      |     +-- NPC
      |          |
      |          +-- Shopkeeper
      |
      +-- Exit
            |
            +-- Door


Every object that can hold other objects does so in its "inventory" (a set).
You can't access it directly, object.inventory returns a frozenset copy of it.
Except Location: it separates the items and livings it contains internally.
Use its enter/leave methods instead.
"""

from __future__ import absolute_import, print_function, division, unicode_literals
from textwrap import dedent
from collections import defaultdict
import copy
import sys
from . import lang
from . import util
from . import pubsub
from . import mud_context
from . import soul
from . import races
from .errors import ActionRefused, ParseError, LocationIntegrityError


__all__ = ["MudObject", "Armour", 'Container', "Door", "Exit", "Item", "Living", "Stats", "Location", "Weapon", "Key", "heartbeat", "clone"]

pending_actions = pubsub.topic("driver-pending-actions")
pending_tells = pubsub.topic("driver-pending-tells")
async_dialogs = pubsub.topic("driver-async-dialogs")


def heartbeat(klass):
    """
    Decorator to use on a class to make it have a heartbeat.
    Use sparingly as it is less efficient than using a deferred, because the driver
    has to call all heartbeats every tick even though they do nothing yet.
    With deferreds, the driver only calls a deferred at the time it is needed.
    """
    klass._register_heartbeat = True
    return klass


def clone(obj):
    """Create a copy of an existing (Mud)Object. Only when it has an empty inventory (to avoid problems)"""
    if isinstance(obj, MudObject):
        try:
            if obj.inventory_size > 0:
                raise ValueError("can't clone something that has other stuff in it")
        except ActionRefused:
            pass
        if obj.location:
            # avoid deepcopying the location
            location, obj.location = obj.location, None
            duplicate = copy.deepcopy(obj)
            obj.location = duplicate.location = location
            return duplicate
    return copy.deepcopy(obj)


class MudObject(object):
    """
    Root class of all objects in the mud world
    All objects have an identifying short name (will be lowercased),
    an optional short title (shown when listed in a room),
    and an optional longer description (shown when explicitly 'examined').
    The long description is 'dedented' first, which means you can put it between triple-quoted-strings easily.
    Short_description is also optional, and is used in the text when a player 'looks' around.
    If it's not set, a generic 'look' message will be shown (something like "XYZ is here").

    Extra descriptions (extra_desc) are used to make stuff more interesting and interactive
    Extra descriptions are accessed by players when they type ``look at <thing>``
    where <thing> is any keyword you choose.  For example, you might write a room description which
    includes the tantalizing sentence, ``The wall looks strange here.``
    Using extra descriptions, players could then see additional detail by typing
    ``look at wall.``  There can be an unlimited number of Extra Descriptions.
    """
    subjective = "it"
    possessive = "its"
    objective = "it"
    gender = "n"

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def short_description(self):
        return self._short_description

    @short_description.setter
    def short_description(self, value):
        self._short_description = value

    @property
    def extra_desc(self):
        return self._extradesc

    @extra_desc.setter
    def extra_desc(self, value):
        self._extradesc = value

    def __init__(self, name, title=None, description=None, short_description=None):
        self.name = self._description = self._title = self._short_description = None
        self.init_names(name, title, description, short_description)
        self.aliases = set()
        self.verbs = {}   # any custom verbs that need to be recognised (verb->docstring mapping. Verb handling is done via handle_verb() callbacks)
        if getattr(self, "_register_heartbeat", False):
            # one way of setting this attribute is by using the @heartbeat decorator
            self.register_heartbeat()
        self.init()

    def init(self):
        """
        Secondary initialization/customization. Invoked after all required initialization has been done.
        You can easily override this in a subclass.
        """
        pass

    def init_names(self, name, title, description, short_description):
        """(re)set the name and description attributes"""
        self.name = name.lower()
        if title:
            assert not title.startswith("the ") and not title.startswith("The "), "title must not start with 'the'"
            assert not title.startswith("a ") and not title.startswith("A "), "title must not start with 'a'"
        self._title = title or name
        self._description = dedent(description).strip() if description else ""
        self._short_description = short_description
        self._extradesc = {}   # maps keyword to description

    def add_extradesc(self, keywords, description):
        """For the list of keywords, add the extra description text"""
        assert isinstance(keywords, (set, tuple, list))
        for keyword in keywords:
            self._extradesc[keyword] = description

    def __repr__(self):
        return "<%s '%s' @ 0x%x>" % (self.__class__.__name__, self.name, id(self))

    def destroy(self, ctx):
        """Common cleanup code that needs to be called when the object is destroyed"""
        assert isinstance(ctx, util.Context)
        self.unregister_heartbeat()
        mud_context.driver.remove_deferreds(self)

    def wiz_clone(self, actor):
        """clone the thing (performed by a wizard)"""
        raise ActionRefused("Can't clone " + lang.a(self.__class__.__name__))

    def wiz_destroy(self, actor, ctx):
        """destroy the thing (performed by a wizard)"""
        raise ActionRefused("Can't destroy " + lang.a(self.__class__.__name__))

    def show_inventory(self, actor, ctx):
        """show the object's inventory to the actor"""
        raise ActionRefused("You can't look inside of that.")

    def register_heartbeat(self):
        """register this object with the driver to receive heartbeats"""
        mud_context.driver.register_heartbeat(self)

    def unregister_heartbeat(self):
        """tell the driver to forget about this object for heartbeats"""
        mud_context.driver.unregister_heartbeat(self)

    def heartbeat(self, ctx):
        # not automatically called, only if your object registered with the driver
        pass

    def activate(self, actor):
        # called from the activate command, override if your object needs to act on this.
        raise ActionRefused("You can't activate that.")

    def deactivate(self, actor):
        # called from the deactivate command, override if your object needs to act on this.
        raise ActionRefused("You can't deactivate that.")

    def manipulate(self, verb, actor):
        # called from the various manipulate commands, override if your object needs to act on this.
        # verb: move, shove, swivel, shift, manipulate, rotate, press, poke, push, turn
        raise ActionRefused("You can't %s that." % verb)

    def move(self, target, actor=None, silent=False, is_player=False, verb="move"):
        # move the MudObject to a different place (location, container, living).
        raise ActionRefused("You can't %s that." % verb)

    def combine(self, other, actor):
        # combine the other item with us
        raise ActionRefused("You can't combine these.")

    def read(self, actor):
        # called from the read command, override if your object needs to act on this.
        raise ActionRefused("There's nothing to read.")

    def handle_verb(self, parsed, actor):
        """Handle a custom verb. Return True if handled, False if not handled."""
        return False

    def notify_action(self, parsed, actor):
        """Notify the object of an action performed by someone. This can be any verb, command, soul emote, custom verb."""
        pass


class Item(MudObject):
    """
    Root class of all Items in the mud world. Items are physical objects.
    Items can usually be moved, carried, or put inside other items.
    They have a name and optional short and longer descriptions.
    Regular items cannot contain other things, so it makes to sense
    to check containment.
    """
    def init(self):
        self.contained_in = None
        self.default_verb = "examine"
        self.value = 0.0   # what the item is worth
        self.rent = 0.0    # price to keep in store / day
        self.weight = 0.0  # some abstract unit

    def __contains__(self, item):
        raise ActionRefused("You can't look inside of that.")

    @property
    def location(self):
        if not self.contained_in:
            return None
        if isinstance(self.contained_in, Location):
            return self.contained_in
        return self.contained_in.location

    @location.setter
    def location(self, value):
        if value is None or isinstance(value, Location):
            self.contained_in = value
        else:
            raise TypeError("can only set item's location to a Location, for other container types use item.contained_in")

    @property
    def inventory(self):
        raise ActionRefused("You can't look inside of that.")

    @property
    def inventory_size(self):
        raise ActionRefused("You can't look inside of that.")

    def insert(self, item, actor):
        raise ActionRefused("You can't put things in there.")

    def remove(self, item, actor):
        raise ActionRefused("You can't take things from there.")

    def move(self, target, actor=None, silent=False, is_player=False, verb="move"):
        """
        Leave the container the item is currently in, enter the target container (transactional).
        Because items can move on various occasions, there's no message being printed.
        The silent and is_player arguments are not used when moving items -- they're used
        for the movement of livings.
        """
        actor = actor or self
        self.allow_item_move(actor, verb)
        source_container = self.contained_in
        if source_container:
            source_container.remove(self, actor)
        try:
            target.insert(self, actor)
            self.notify_moved(source_container, target, actor)
        except:
            # insert in target failed, put back in original location
            source_container.insert(self, actor)
            raise

    def notify_moved(self, source_container, target_container, actor):
        """Called when the item has been moved from one place to another"""
        pass

    def allow_item_move(self, actor, verb="move"):
        """Does the item allow to be moved by someone? (yes; no ActionRefused is raised)"""
        pass

    def open(self, actor, item=None):
        raise ActionRefused("You can't open that.")

    def close(self, actor, item=None):
        raise ActionRefused("You can't close that.")

    def lock(self, actor, item=None):
        raise ActionRefused("You can't lock that.")

    def unlock(self, actor, item=None):
        raise ActionRefused("You can't unlock that.")

    @util.authorized("wizard")
    def wiz_clone(self, actor):
        item = clone(self)
        actor.insert(item, actor)
        actor.tell("Cloned into: " + repr(item))
        actor.tell_others("{Title} conjures up %s, and quickly pockets it." % lang.a(item.title))
        return item

    @util.authorized("wizard")
    def wiz_destroy(self, actor, ctx):
        if self in actor:
            actor.remove(self, actor)
        else:
            actor.location.remove(self, actor)
        self.destroy(ctx)

    def show_inventory(self, actor, ctx):
        """show the object's contents to the actor"""
        if self.inventory:
            actor.tell("It contains:", end=True)
            for item in self.inventory:
                actor.tell("  " + item.title, format=False)
        else:
            actor.tell("It's empty.")


class Weapon(Item):
    """
    An item that can be wielded by a Living (i.e. present in a weapon itemslot),
    and that can be used to attack another Living.
    """
    pass


class Armour(Item):
    """
    An item that can be worn by a Living (i.e. present in an armour itemslot)
    """
    pass


class Location(MudObject):
    """
    A location in the mud world. Livings and Items are in it.
    Has connections ('exits') to other Locations.
    You can test for containment with 'in': item in loc, npc in loc
    """
    def __init__(self, name, description=None):
        super(Location, self).__init__(name, description=description)
        self.name = name      # make sure we preserve the case; base object stores it lowercase
        self.livings = set()  # set of livings in this location
        self.items = set()    # set of all items in the room
        self.exits = {}       # dictionary of all exits: exit_direction -> Exit object with target & descr

    def __contains__(self, obj):
        return obj in self.livings or obj in self.items

    def __getstate__(self):
        state = dict(self.__dict__)
        return state

    def __setstate__(self, state):
        self.__dict__ = state

    def init_inventory(self, objects):
        """Set the location's initial item and livings 'inventory'"""
        if len(self.items) > 0 or len(self.livings) > 0:
            raise LocationIntegrityError("clobbering existing inventory", None, None, self)
        for obj in objects:
            self.insert(obj, self)

    def destroy(self, ctx):
        super(Location, self).destroy(ctx)
        for living in self.livings:
            if living.location is self:
                living.location = _limbo
        self.livings.clear()
        self.items.clear()
        self.exits.clear()

    def add_exits(self, exits):
        """Adds every exit from the sequence as an exit to this room."""
        for exit in exits:
            exit.bind(self)
            # note: we're not simply adding it to the .exits dict here, because
            # the exit may have aliases defined that it wants to be known as also.

    def get_wiretap(self):
        """get a wiretap for this location"""
        return pubsub.topic(("wiretap-location", self.name))

    def tell(self, room_msg, exclude_living=None, specific_targets=None, specific_target_msg=""):
        """
        Tells something to the livings in the room (excluding the living from exclude_living).
        This is just the message string! If you want to react on events, consider not doing
        that based on this message string. That will make it quite hard because you need to
        parse the string again to figure out what happened... Use handle_verb / notify_action instead.
        """
        specific_targets = specific_targets or set()
        assert isinstance(specific_targets, (frozenset, set, list, tuple))
        if exclude_living:
            assert isinstance(exclude_living, Living)
        for living in self.livings:
            if living == exclude_living:
                continue
            if living in specific_targets:
                living.tell(specific_target_msg)
            else:
                living.tell(room_msg)
        if room_msg:
            tap = self.get_wiretap()
            tap.send((self.name, room_msg))

    def message_nearby_locations(self, message):
        """
        Tells a message to adjacent locations, where adjacent is defined by being connected via an exit.
        If the adjacent location has an obvious returning exit to the source location (via one of the
        most obvious routes n/e/s/w/up/down/etc.), it hen also get information on what direction
        the sound originated from.  This is used for loud noises such as yells!
        """
        if self.exits:
            yelled_locations = set()
            for exit in self.exits.values():
                if exit.target in yelled_locations:
                    continue   # skip double locations (possible because there can be multiple exits to the same location)
                if exit.target is not self:
                    exit.target.tell(message)
                    yelled_locations.add(exit.target)
                    for direction, return_exit in exit.target.exits.items():
                        if return_exit.target is self:
                            if direction in {"north", "east", "south", "west", "northeast", "northwest", "southeast",
                                             "southwest", "left", "right", "front", "back"}:
                                direction = "the " + direction
                            elif direction in {"up", "above", "upstairs"}:
                                direction = "above"
                            elif direction in {"down", "below", "downstairs"}:
                                direction = "below"
                            else:
                                continue  # no direction description possible for this exit
                            exit.target.tell("The sound is coming from %s." % direction)
                            break
                    else:
                        exit.target.tell("You can't hear where the sound is coming from.")

    def nearby(self, no_traps=True):
        """
        Returns an iterable of all adjacent locations, normally avoiding 'traps' (locations without a way back).
        (this may be expanded in the future with a way to search further than just 1 step away)
        """
        if no_traps:
            return (e.target for e in self.exits.values() if e.target.exits)
        return (e.target for e in self.exits.values())

    def look(self, exclude_living=None, short=False):
        """returns a list of paragraph strings describing the surroundings, possibly excluding one living from the description list"""
        paragraphs = ["<location>[" + self.name + "]</>"]
        if short:
            if self.exits and mud_context.config.show_exits_in_look:
                paragraphs.append("<exit>Exits</>: " + ", ".join(sorted(set(self.exits.keys()))))
            if self.items:
                item_names = sorted(item.name for item in self.items)
                paragraphs.append("<item>You see</>: " + lang.join(item_names))
            if self.livings:
                living_names = sorted(living.name for living in self.livings if living != exclude_living)
                if living_names:
                    paragraphs.append("<living>Present</>: " + lang.join(living_names))
            return paragraphs
        # normal (long) output
        if self.description:
            paragraphs.append(self.description)
        if self.exits and mud_context.config.show_exits_in_look:
            exits_seen = set()
            exit_paragraph = []
            for exit_name in sorted(self.exits):
                exit = self.exits[exit_name]
                if exit not in exits_seen:
                    exits_seen.add(exit)
                    exit_paragraph.append(exit.short_description)
            paragraphs.append(" ".join(exit_paragraph))
        items_and_livings = []
        items_with_short_descr = [item for item in self.items if item.short_description]
        items_without_short_descr = [item for item in self.items if not item.short_description]
        uniq_descriptions = set()
        if items_with_short_descr:
            for item in items_with_short_descr:
                uniq_descriptions.add(item.short_description)
        items_and_livings.extend(uniq_descriptions)
        if items_without_short_descr:
            titles = sorted([lang.a(item.title) for item in items_without_short_descr])
            items_and_livings.append("You see " + lang.join(titles) + ".")
        livings_with_short_descr = [living for living in self.livings if living != exclude_living and living.short_description]
        livings_without_short_descr = [living for living in self.livings if living != exclude_living and not living.short_description]
        if livings_without_short_descr:
            titles = sorted(living.title for living in livings_without_short_descr)
            if titles:
                titles_str = lang.join(titles)
                if len(titles) > 1:
                    titles_str += " are here."
                else:
                    titles_str += " is here."
                items_and_livings.append(lang.capital(titles_str))
        uniq_descriptions = set()
        if livings_with_short_descr:
            for living in livings_with_short_descr:
                uniq_descriptions.add(living.short_description)
        items_and_livings.extend(uniq_descriptions)
        if items_and_livings:
            paragraphs.append(" ".join(items_and_livings))
        return paragraphs

    def search_living(self, name):
        """
        Search for a living in this location by its name (and title, if no names match).
        Is alias-aware. If there's more than one match, returns the first.
        """
        name = name.lower()
        result = [living for living in self.livings if living.name == name]
        if not result:
            # try titles and aliases
            result = [living for living in self.livings if name in living.aliases or living.title.lower() == name]
        return result[0] if result else None

    def insert(self, obj, actor):
        """Add obj to the contents of the location (either a Living or an Item)"""
        if isinstance(obj, Living):
            self.livings.add(obj)
        elif isinstance(obj, Item):
            self.items.add(obj)
        else:
            raise TypeError("can only add Living or Item")
        obj.location = self

    def remove(self, obj, actor):
        """Remove obj from this location (either a Living or an Item)"""
        if obj in self.livings:
            self.livings.remove(obj)
        elif obj in self.items:
            self.items.remove(obj)
        else:
            return   # just ignore an object that wasn't present in the first place
        obj.location = None

    def handle_verb(self, parsed, actor):
        """Handle a custom verb. Return True if handled, False if not handled."""
        # this code cannot deal with yields directly but you can raise AsyncDialog exception,
        # that indicates to the driver that it should initiate the given async dialog when continuing.
        handled = any(living._handle_verb_base(parsed, actor) for living in self.livings)
        if not handled:
            handled = any(item.handle_verb(parsed, actor) for item in self.items)
            if not handled:
                handled = any(exit.handle_verb(parsed, actor) for exit in set(self.exits.values()))
        return handled

    def notify_action(self, parsed, actor):
        """Notify the room, its livings and items of an action performed by someone."""
        # Notice that this notification event is invoked by the driver after all
        # actions concerning player input have been handled, so we don't have to
        # queue the delegated calls.
        for living in self.livings:
            living._notify_action_base(parsed, actor)
        for item in self.items:
            item.notify_action(parsed, actor)
        for exit in set(self.exits.values()):
            exit.notify_action(parsed, actor)

    def notify_npc_arrived(self, npc, previous_location):
        """a NPC has arrived in this location."""
        pass

    def notify_npc_left(self, npc, target_location):
        """a NPC has left the location."""
        pass

    def notify_player_arrived(self, player, previous_location):
        """a player has arrived in this location."""
        pass

    def notify_player_left(self, player, target_location):
        """a player has left this location."""
        pass


_limbo = Location("Limbo",
                  """
                  The intermediate or transitional place or state. There's only nothingness.
                  Living beings end up here if they're not in a proper location yet.
                  """)


class Exit(MudObject):
    """
    An 'exit' that connects one location to another. It is strictly one-way.
    Directions can be a single string or a sequence of directions (all meaning the same exit).
    You can use a Location object as target, or a string designating the location
    (for instance "town.square" means the square location object in game.zones.town).
    If using a string, it will be retrieved and bound at runtime.
    Short_description will be shown when the player looks around the room.
    Long_description is optional and will be shown instead if the player examines the exit.
    The exit's direction is stored as its name attribute (if more than one, the rest are aliases).
    Note that the exit's origin is not stored in the exit object.
    """
    def __init__(self, directions, target_location, short_description, long_description=None):
        assert isinstance(target_location, (Location, util.basestring_type)), "target must be a Location or a string"
        if isinstance(directions, util.basestring_type):
            direction = directions
            aliases = frozenset()
        else:
            direction = directions[0]
            aliases = frozenset(directions[1:])
        self.target = target_location
        self.bound = isinstance(target_location, Location)
        if self.bound:
            title = "Exit to " + self.target.title
        else:
            title = "Exit to <unbound:%s>" % self.target
        long_description = long_description or short_description
        super(Exit, self).__init__(direction, title=title, description=long_description, short_description=short_description)
        self.aliases = aliases
        # The driver needs to know about all exits,
        # it will hook them all up once initialization is complete.
        mud_context.driver.register_exit(self)

    def __repr__(self):
        targetname = self.target.name if self.bound else self.target
        return "<base.Exit to '%s' @ 0x%x>" % (targetname, id(self))

    def bind(self, location):
        """Binds the exit to a location."""
        assert isinstance(location, Location)
        directions = self.aliases | {self.name}
        for direction in directions:
            if direction in location.exits:
                raise LocationIntegrityError("exit already exists: '%s' in %s" % (direction, location), direction, self, location)
            location.exits[direction] = self

    def _bind_target(self, game_zones_module):
        """
        Binds the exit to the actual target_location object.
        Usually called by the driver before it starts player interaction.
        The caller needs to pass in the root module of the game zones (to avoid circular import dependencies)
        """
        if not self.bound:
            target_module, target_object = self.target.rsplit(".", 1)
            module = game_zones_module
            try:
                for name in target_module.split("."):
                    module = getattr(module, name)
                target = getattr(module, target_object)
            except AttributeError:
                raise AttributeError("exit target error, cannot find target: '%s.%s' in exit: '%s'" % (target_module, target_object, self.short_description))
            assert isinstance(target, Location)
            self.target = target
            self.title = "Exit to " + target.title
            self.name = self.title.lower()
            self.bound = True

    def allow_passage(self, actor):
        """Is the actor allowed to move through the exit? Raise ActionRefused if not"""
        if not self.bound:
            raise LocationIntegrityError("exit not bound", None, self, None)

    def open(self, actor, item=None):
        raise ActionRefused("You can't open that.")

    def close(self, actor, item=None):
        raise ActionRefused("You can't close that.")

    def lock(self, actor, item=None):
        raise ActionRefused("You can't lock that.")

    def unlock(self, actor, item=None):
        raise ActionRefused("You can't unlock that.")

    def manipulate(self, verb, actor):
        # override from base to print a special error message
        raise ActionRefused("It makes no sense to %s in that direction." % verb)


class Stats(object):
    def __init__(self):
        self.level = 0
        self.xp = 0
        self.hp = 0
        self.maxhp_dice = None
        self.ac = 0
        self.attack_dice = None     # damage roll when attacking without a weapon
        self.agi = 0
        self.cha = 0
        self.int = 0
        self.lck = 0
        self.spd = 0
        self.sta = 0
        self.str = 0
        self.wis = 0
        self.stat_prios = None      # per agi/cha/etc stat, priority level of it (see races.py)
        self.alignment = 0   # -1000 (evil) to +1000 (good), neutral=[-349..349]
        self.bodytype = None
        self.language = None
        self.weight = 0
        self.size = 0
        self.race = None    # optional, can use the stats template from races

    def __repr__(self):
        return "<Stats: %s>" % vars(self)

    @classmethod
    def from_race(cls, race):
        r = races.races[race]
        s = cls()
        s.race = race
        s.bodytype = r["bodytype"]
        s.language = r["language"]
        s.weight = r["mass"]
        s.size = r["size"]
        rs = r["stats"]
        s.agi = rs["agi"][0]
        s.cha = rs["cha"][0]
        s.int = rs["int"][0]
        s.lck = rs["lck"][0]
        s.spd = rs["spd"][0]
        s.sta = rs["sta"][0]
        s.str = rs["str"][0]
        s.wis = rs["wis"][0]
        s.stat_prios = defaultdict(list)
        for stat, (_, prio) in r["stats"].items():
            s.stat_prios[prio].append(stat)
        # @todo initialize xp, hp, maxhp, ac, attack, alignment, level. Current race defs don't include this data
        return s


class Living(MudObject):
    """
    Root class of the living entities in the mud world.
    Livings sometimes have a heart beat 'tick' that makes them interact with the world.
    They are always inside a Location (Limbo when not specified yet).
    They also have an inventory object, and you can test for containment with item in living.
    """
    def __init__(self, name, gender, race=None, title=None, description=None, short_description=None):
        self.init_gender(gender)
        self.soul = soul.Soul()
        self.location = _limbo  # set transitional location
        self.privileges = set()  # probably only used for Players though
        self.aggressive = False
        self.money = 0.0  # the currency is determined by util.MoneyFormatter set in the driver
        if race:
            self.stats = Stats.from_race(race)
        else:
            self.stats = Stats()
        self.default_verb = "examine"
        self.__inventory = set()
        self.previous_commandline = None
        self._previous_parsed = None
        super(Living, self).__init__(name, title, description, short_description)

    def init_gender(self, gender):
        """(re)set gender attributes"""
        self.gender = gender
        self.subjective = lang.SUBJECTIVE[self.gender]
        self.possessive = lang.POSSESSIVE[self.gender]
        self.objective = lang.OBJECTIVE[self.gender]

    def init_inventory(self, items):
        """Set the living's initial inventory"""
        assert len(self.__inventory) == 0
        for item in items:
            self.insert(item, self)

    def __getstate__(self):
        state = dict(self.__dict__)
        return state

    def __setstate__(self, state):
        self.__dict__ = state

    def __contains__(self, item):
        return item in self.__inventory

    @property
    def inventory_size(self):
        return len(self.__inventory)

    @property
    def inventory(self):
        return frozenset(self.__inventory)

    def insert(self, item, actor):
        """Add an item to the inventory."""
        if isinstance(item, Item) and (actor is self or actor is not None and "wizard" in actor.privileges):
            self.__inventory.add(item)
            item.contained_in = self
        else:
            raise ActionRefused("You can't do that.")

    def remove(self, item, actor):
        """remove an item from the inventory"""
        if actor is self or actor is not None and "wizard" in actor.privileges:
            self.__inventory.remove(item)
            item.contained_in = None
        else:
            raise ActionRefused("You can't take %s from %s." % (item.title, self.title))

    def destroy(self, ctx):
        super(Living, self).destroy(ctx)
        if self.location and self in self.location.livings:
            self.location.livings.remove(self)
        self.location = None
        for item in self.__inventory:
            item.destroy(ctx)
        self.__inventory.clear()
        # @todo: remove attack status, etc.
        self.soul = None   # truly die ;-)

    @util.authorized("wizard")
    def wiz_clone(self, actor):
        duplicate = clone(self)
        actor.tell("Cloned into: " + repr(duplicate))
        actor.tell_others("{Title} summons %s..." % lang.a(duplicate.title))
        actor.location.insert(duplicate, actor)
        actor.location.tell("%s appears." % lang.capital(duplicate.title))
        return duplicate

    @util.authorized("wizard")
    def wiz_destroy(self, actor, ctx):
        if self is actor:
            raise ActionRefused("You can't destroy yourself, are you insane?!")
        self.tell("%s creates a black hole that sucks you up. You're utterly destroyed." % lang.capital(actor.title))
        self.destroy(ctx)

    def show_inventory(self, actor, ctx):
        """show the living's inventory to the actor"""
        name = lang.capital(self.title)
        if self.inventory:
            actor.tell(name, "is carrying:", end=True)
            for item in self.inventory:
                actor.tell("  " + item.title, format=False)
        else:
            actor.tell(name, "is carrying nothing.")
        if ctx.config.money_type:
            actor.tell("Money in possession: %s." % ctx.driver.moneyfmt.display(self.money))

    def get_wiretap(self):
        """get a wiretap for this living"""
        return pubsub.topic(("wiretap-living", self.name))

    def tell(self, *messages, **kwargs):
        """
        Every living thing in the mud can receive one or more action messages.
        For players this is usually printed to their screen, but for all other
        livings the default is to do nothing.
        They could react on it but this is not advisable because you will need
        to parse the string again to figure out what happened...
        kwargs is ignored for Livings.
        """
        if sys.version_info < (3, 0):
            msg = u" ".join(unicode(msg) for msg in messages)
        else:
            msg = " ".join(str(msg) for msg in messages)
        tap = self.get_wiretap()
        tap.send((self.name, msg))

    def tell_later(self, *messages, **kwargs):
        """Tell something to this actor, but do it after other messages."""
        pending_tells.send(lambda: self.tell(*messages, **kwargs))

    def tell_others(self, *messages):
        """
        Message(s) sent to the other livings in the location, but not to self.
        There are a few formatting strings for easy shorthands:
        {title}/{Title} = the living's title, and the title with a capital letter.
        If you need even more tweaks with telling stuff, use living.location.tell directly.
        """
        formats = {"title": self.title, "Title": lang.capital(self.title)}
        for msg in messages:
            msg = msg.format(**formats)
            self.location.tell(msg, exclude_living=self)

    def parse(self, commandline, external_verbs=frozenset()):
        """Parse the commandline into something that can be processed by the soul (soul.ParseResult)"""
        if commandline == "again":
            # special case, repeat previous command
            if self.previous_commandline:
                commandline = self.previous_commandline
                self.tell("<dim>(repeat: %s)</>" % commandline, end=True)
            else:
                raise ActionRefused("Can't repeat your previous action.")
        self.previous_commandline = commandline
        parsed = self.soul.parse(self, commandline, external_verbs)
        self._previous_parsed = parsed
        if external_verbs and parsed.verb in external_verbs:
            raise soul.NonSoulVerb(parsed)
        if parsed.verb not in soul.NONLIVING_OK_VERBS:
            # check if any of the targeted objects is a non-living
            if not all(isinstance(who, Living) for who in parsed.who_order):
                raise soul.NonSoulVerb(parsed)
        self.validate_socialize_targets(parsed)
        return parsed

    def validate_socialize_targets(self, parsed):
        """check if any of the targeted objects is an exit"""
        if any(isinstance(w, Exit) for w in parsed.who_info):
            raise ParseError("That doesn't make much sense.")

    def remember_parsed(self):
        """remember the previously parsed data, soul uses this to reference back to earlier items/livings"""
        self.soul.previously_parsed = self._previous_parsed

    def do_socialize(self, cmdline, external_verbs=frozenset()):
        """perform a command line with a socialize/soul verb on the living's behalf"""
        try:
            parsed = self.parse(cmdline, external_verbs=external_verbs)
            self.do_socialize_cmd(parsed)
        except soul.UnknownVerbException as ex:
            if ex.verb == "say":
                # emulate the say command (which is not an emote, but it's convenient to be able to use it as such)
                verb, _, rest = cmdline.partition(u" ")
                rest = rest.strip()
                self.tell_others("{Title} says: "+rest)
            else:
                raise

    def do_socialize_cmd(self, parsed):
        """
        A soul verb such as 'ponder' was entered. Socialize with the environment to handle this.
        Some verbs may trigger a response or action from something or someone else.
        """
        who, actor_message, room_message, target_message = self.soul.process_verb_parsed(self, parsed)
        self.tell(actor_message)
        self.location.tell(room_message, self, who, target_message)
        pending_actions.send(lambda actor=self: actor.location.notify_action(parsed, actor))
        if parsed.verb in soul.AGGRESSIVE_VERBS:
            # usually monsters immediately attack,
            # other npcs may choose to attack or to ignore it
            # We need to check the verb qualifier, it might void the actual action :)
            if parsed.qualifier not in soul.NEGATING_QUALIFIERS:
                for living in who:
                    if getattr(living, "aggressive", False):
                        pending_actions.send(lambda victim=self: living.start_attack(victim))

    @util.authorized("wizard")
    def do_forced_cmd(self, actor, parsed, ctx):
        """
        Perform a (pre-parsed) command because the actor forced us to do it.

        This code is fairly similar to the __process_player_command from the driver
        but it doesn't deal with as many error situations, and just bails out if it gets confused.
        It does try its best to support the following:
        - custom location verbs (such as 'sell' in a shop)
        - exit handling
        - built-in cmds (such as 'drop'/'take')
        Note that soul emotes are handled by do_socialize_cmd instead.
        """
        try:
            if parsed.qualifier:
                raise ParseError("That action doesn't support qualifiers.")  # for now, qualifiers are only supported on soul-verbs (emotes).
            custom_verbs = set(ctx.driver.current_custom_verbs(self))
            if parsed.verb in custom_verbs:
                if self.location.handle_verb(parsed, self):       # note: can't deal with async dialogs
                    pending_actions.send(lambda actor=self: actor.location.notify_action(parsed, actor))
                    return
                else:
                    raise ParseError("That custom verb is not understood by the environment.")
            if parsed.verb in self.location.exits:
                ctx.driver._go_through_exit(self, parsed.verb)
                return
            command_verbs = set(ctx.driver.current_verbs(self))
            if parsed.verb in command_verbs:
                # Here, one of the commands as annotated with @cmd (or @wizcmd) is executed
                func = ctx.driver.commands.get(self.privileges)[parsed.verb]
                if getattr(func, "is_generator", False):
                    dialog = func(self, parsed, ctx)
                    async_dialogs.send((ctx.conn, dialog))    # enqueue as async, and continue
                    return
                func(self, parsed, ctx)
                if func.enable_notify_action:
                    pending_actions.send(lambda actor=self: actor.location.notify_action(parsed, actor))
                return
            raise ParseError("Command not understood.")
        except Exception as x:
            actor.tell("Error result from forced cmd: " + str(x))

    def move(self, target, actor=None, silent=False, is_player=False, verb="move"):
        """
        Leave the current location, enter the new location (transactional).
        Messages are being printed to the locations if the move was successful.
        """
        actor = actor or self
        original_location = None
        if self.location:
            original_location = self.location
            self.location.remove(self, actor)
            try:
                target.insert(self, actor)
            except:
                # insert in target failed, put back in original location
                original_location.insert(self, actor)
                raise
            if not silent:
                original_location.tell("%s leaves." % lang.capital(self.title), exclude_living=self)
            # queue event
            if is_player:
                pending_actions.send(lambda who=self, where=target: original_location.notify_player_left(who, where))
            else:
                pending_actions.send(lambda who=self, where=target: original_location.notify_npc_left(who, where))
        else:
            target.insert(self, actor)
        if not silent:
            target.tell("%s arrives." % lang.capital(self.title), exclude_living=self)
        # queue event
        if is_player:
            pending_actions.send(lambda who=self, where=original_location: target.notify_player_arrived(who, where))
        else:
            pending_actions.send(lambda who=self, where=original_location: target.notify_npc_arrived(who, where))

    def search_item(self, name, include_inventory=True, include_location=True, include_containers_in_inventory=True):
        """The same as locate_item except it only returns the item, or None."""
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
        found = containing_object = None
        if include_inventory:
            containing_object = self
            found = util.search_item(name, self.__inventory)
        if not found and include_location:
            containing_object = self.location
            found = util.search_item(name, self.location.items)
        if not found and include_containers_in_inventory:
            # check if an item in the inventory might contain it
            for container in self.__inventory:
                containing_object = container
                try:
                    inventory = container.inventory
                except ActionRefused:
                    continue    # no access to inventory, just skip this item silently
                else:
                    found = util.search_item(name, inventory)
                    if found:
                        break
        return (found, containing_object) if found else (None, None)

    def start_attack(self, living):
        """Starts attacking the given living until death ensues on either side."""
        # @todo: I'm not yet sure if the combat/attack logic should go here (on Living), or that it should be split across NPC / Player...
        pass

    def allow_give_money(self, actor, amount):
        """Do we accept money? Raise ActionRefused if not."""
        raise ActionRefused("You can't do that.")

    def _handle_verb_base(self, parsed, actor):
        """
        Handle a custom verb. Return True if handled, False if not handled.
        Also checks inventory items. (Don't override this in a subclass,
        override handle_verb instead)
        """
        if self.handle_verb(parsed, actor):
            return True
        return any(item.handle_verb(parsed, actor) for item in self.__inventory)

    def handle_verb(self, parsed, actor):
        """Handle a custom verb. Return True if handled, False if not handled."""
        return False

    def _notify_action_base(self, parsed, actor):
        """
        Notify the living of an action performed by someone.
        Also calls inventory items. Don't override this one in a subclass,
        override notify_action instead.
        """
        self.notify_action(parsed, actor)
        for item in self.__inventory:
            item.notify_action(parsed, actor)

    def notify_action(self, parsed, actor):
        """Notify the living of an action performed by someone."""
        pass

    def look(self, short=None):
        """look around in your surroundings. Dummy for base livings."""
        pass


class Container(Item):
    """
    A bag-type container (i.e. an item that acts as a container)
    Allows insert and remove, and examine its contents, as opposed to an Item
    You can test for containment with 'in': item in bag
    """
    def init(self):
        super(Container, self).init()
        self.__inventory = set()

    def init_inventory(self, items):
        """Set the container's initial inventory"""
        assert len(self.__inventory) == 0
        self.__inventory = set(items)
        for item in items:
            item.contained_in = self

    @property
    def inventory(self):
        return frozenset(self.__inventory)

    @property
    def inventory_size(self):
        return len(self.__inventory)

    def __contains__(self, item):
        return item in self.__inventory

    def destroy(self, ctx):
        super(Container, self).destroy(ctx)
        for item in self.__inventory:
            item.destroy(ctx)
        self.__inventory.clear()

    def insert(self, item, actor):
        assert isinstance(item, MudObject)
        self.__inventory.add(item)
        item.contained_in = self
        return self

    def remove(self, item, actor):
        self.__inventory.remove(item)
        item.contained_in = None
        return self


class Door(Exit):
    """
    A special exit that connects one location to another but which can be closed or even locked.
    """
    def __init__(self, directions, target_location, short_description, long_description=None, locked=False, opened=True):
        self.locked = locked
        self.opened = opened
        self.__description_prefix = long_description or short_description
        self.key_code = None   # you can optionally set this to any code that a key must match to unlock the door
        super(Door, self).__init__(directions, target_location, short_description, long_description)
        if locked and opened:
            raise ValueError("door cannot be both locked and opened")
        self.linked_door = None

    class DoorPairLink(object):
        def __init__(self, other_door, other_open_msg=None, other_close_msg=None):
            self.door = other_door
            self.open_msg = other_open_msg
            self.close_msg = other_close_msg

    def reverse_door(self, directions, returning_location, short_description, long_description=None,
                     reverse_open_msg=None, reverse_close_msg=None, this_open_msg=None, this_close_msg=None):
        """
        Set up a second door in the other location that is paired with this door.
        Opening this door will also open the other door etc.    Returns the new door object.
        """
        other_door = Door(directions, returning_location, short_description, long_description, locked=self.locked, opened=self.opened)
        self.linked_door = Door.DoorPairLink(other_door, this_open_msg, this_close_msg)
        other_door.linked_door = Door.DoorPairLink(self, reverse_open_msg, reverse_close_msg)
        other_door.key_code = self.key_code
        return other_door

    @property
    def description(self):
        if self.opened:
            status = "It is open "
        else:
            status = "It is closed "
        if self.locked:
            status += "and locked."
        else:
            status += "and unlocked."
        return self.__description_prefix + " " + status

    def __repr__(self):
        target = self.target.name if self.bound else self.target
        locked = "locked" if self.locked else "open"
        return "<base.Door '%s'->'%s' (%s) @ 0x%x>" % (self.name, target, locked, id(self))

    def allow_passage(self, actor):
        """Is the actor allowed to move through this door?"""
        if not self.bound:
            raise LocationIntegrityError("door not bound", None, self, None)
        if not self.opened:
            raise ActionRefused("You can't go there; it's closed.")

    def open(self, actor, item=None):
        """Open the door with optional item. Notifies actor and room of this event."""
        if self.opened:
            raise ActionRefused("It's already open.")
        elif self.locked:
            raise ActionRefused("You try to open it, but it's locked.")
        else:
            self.opened = True
            actor.tell("You opened it.")
            actor.tell_others("{Title} opened the %s." % self.name)
            if self.linked_door:
                self.linked_door.door.opened = True
                if self.linked_door.open_msg:
                    self.target.tell(self.linked_door.open_msg)

    def close(self, actor, item=None):
        """Close the door with optional item. Notifies actor and room of this event."""
        if not self.opened:
            raise ActionRefused("It's already closed.")
        self.opened = False
        actor.tell("You closed it.")
        actor.tell_others("{Title} closed the %s." % self.name)
        if self.linked_door:
            self.linked_door.door.opened = False
            if self.linked_door.close_msg:
                self.target.tell(self.linked_door.close_msg)

    def lock(self, actor, item=None):
        """Lock the door with the proper key (optional)."""
        if self.locked:
            raise ActionRefused("It's already locked.")
        if item:
            if self.check_key(item):
                key = item
            else:
                raise ActionRefused("You can't use that to lock it.")
        else:
            key = self.search_key(actor)
            if key:
                actor.tell("<dim>(You use your %s; %s matches the lock.)</>" % (key.title, key.subjective))
            else:
                raise ActionRefused("You don't seem to have the means to lock it.")
        self.locked = True
        actor.tell("Your %s fits, it is now locked." % key.title)
        actor.tell_others("{Title} locked the %s with %s." % (self.name, lang.a(key.title)))
        if self.linked_door:
            self.linked_door.door.locked = True

    def unlock(self, actor, item=None):
        """Unlock the door with the proper key (optional)."""
        if not self.locked:
            raise ActionRefused("It's not locked.")
        if item:
            if self.check_key(item):
                key = item
            else:
                raise ActionRefused("You can't use that to unlock it.")
        else:
            key = self.search_key(actor)
            if key:
                actor.tell("<dim>(You use your %s; %s matches the lock.)</>" % (key.title, key.subjective))
            else:
                raise ActionRefused("You don't seem to have the means to unlock it.")
        self.locked = False
        actor.tell("Your %s fits, it is now unlocked." % key.title)
        actor.tell_others("{Title} unlocked the %s with %s." % (self.name, lang.a(key.title)))
        if self.linked_door:
            self.linked_door.door.locked = False

    def check_key(self, item):
        """Check if the item is a proper key for this door (based on key_code)"""
        key_code = getattr(item, "key_code", None)
        if self.linked_door:
            # if this door has a linked door, it could be that the key_code was set on the other door.
            # in that case, copy the key code from the other door.
            other_code = self.linked_door.door.key_code
            if self.key_code is None:
                self.key_code = other_code
            else:
                assert self.key_code == other_code, "door key codes must match"
        return key_code and key_code == self.key_code

    def search_key(self, actor):
        """Does the actor have a proper key? Return the item if so, otherwise return None."""
        for item in actor.inventory:
            if self.check_key(item):
                return item
        return None

    def insert(self, item, actor):
        """used when the player tries to put a key into the door, for instance."""
        if self.check_key(item):
            if self.locked:
                raise ActionRefused("You could try to unlock the door with it instead.")
            else:
                raise ActionRefused("You could try to lock the door with it instead.")
        raise ActionRefused("The %s doesn't fit." % item.title)


class Key(Item):
    """A key which has a unique code. It can be used to open the matching Door."""
    def init(self):
        super(Key, self).init()
        self.key_code = None

    def key_for(self, door=None, code=None):
        """Makes this key a key for the given door. (basically just copies the door's key_code)"""
        if code:
            assert door is None
            self.key_code = code
        else:
            self.key_code = door.key_code
            if not self.key_code:
                raise LocationIntegrityError("door has no key_code set", None, door, door.target)
