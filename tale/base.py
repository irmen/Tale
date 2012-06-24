"""
Mudlib base objects.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division, unicode_literals
import weakref
import textwrap
from . import lang
from . import color
from .errors import ActionRefused
from .races import races
from .globalcontext import mud_context
from .util import basestring_type

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


Every object that can hold other objects does so in its "inventory" (a set).
You can't access it directly, object.inventory returns a frozenset copy of it.
Except Location: it separates the items and livings it contains internally.
Use its enter/leave methods instead.
"""


class MudObject(object):
    """
    Root class of all objects in the mud world
    All objects have an identifying short name,
    an optional short title (shown when listed in a room),
    and an optional longer description (shown when explicitly 'examined').
    The long description is 'dedented' first, which means you can put it between triple-quoted-strings easily.
    Short_description is optional, and is used in the text when a player 'looks' around.
    If it's not set, a generic 'look' message will be shown (something like "XYZ is here").
    """
    subjective = "it"
    possessive = "its"
    objective = "it"
    gender = "n"

    def __init__(self, name, title=None, description=None, short_description=None):
        self.name = name.lower()
        self.aliases = []
        self.verbs = []   # any custom verbs that need to be registered in the location or in the player
        if title:
            assert not title.startswith("the ") and not title.startswith("The "), "title must not start with 'the'"
        try:
            self.title = title or name
        except AttributeError:
            # this can occur if someone made title into a property
            self._title = title or name
        descr = textwrap.dedent(description).strip() if description else ""
        try:
            self.description = descr
        except AttributeError:
            # this can occur if someone made description into a property
            self._description = descr
        try:
            self.short_description = short_description
        except AttributeError:
            # this can occur if someone made short_description into a property
            self._short_description = short_description
        if getattr(self, "_register_heartbeat", False):
            # one way of setting this attribute is by using the @heartbeat decorator
            self.register_heartbeat()
        self.init()

    def init(self):
        """Secondary initialization/customization. You can easily override this in a subclass."""
        pass

    def __repr__(self):
        return "<%s '%s' @ 0x%x>" % (self.__class__.__name__, self.name, id(self))

    def destroy(self, ctx):
        self.unregister_heartbeat()
        mud_context.driver.remove_deferreds(self)

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
    You can test for containment with 'in': item in bag (but the containment
    is always empty and so it will always return False for a regular Item)
    """
    def init(self):
        self.contained_in = None
        self.default_verb = "examine"

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

    def move(self, target_container, actor, wizard_override=False):
        """
        Leave the container the item is currently in, enter the target container (transactional).
        Because items can move on various occasions, there's no message being printed.
        If wizard_override is True, it overrides certain allowance checks (but not all)
        """
        if not wizard_override or "wizard" not in actor.privileges:
            self.allow_move(actor)
        source_container = self.contained_in
        if source_container:
            source_container.remove(self, actor)
        try:
            target_container.insert(self, actor)
        except:
            # insert in target failed, put back in original location
            source_container.insert(self, actor)
            raise

    def allow_move(self, actor):
        """Does it allow to be moved by someone? (yes, no ActionRefused raised)"""
        pass

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
        self.wiretaps = weakref.WeakSet()     # wizard wiretaps for this location
        self.verbs = []       # custom verbs are added to this list when they're present in this location

    def __contains__(self, obj):
        return obj in self.livings or obj in self.items

    def __getstate__(self):
        # can't serialize the wiretaps because it's a weakset. Too bad, just skip them.
        state = dict(self.__dict__)
        del state["wiretaps"]
        return state

    def __setstate__(self, state):
        self.__dict__ = state
        # restore the wireteaps to an empty weakset
        self.wiretaps = weakref.WeakSet()

    def init_inventory(self, objects):
        """Set the location's initial item and livings 'inventory'"""
        assert len(self.items) == 0
        assert len(self.livings) == 0
        for obj in objects:
            self.insert(obj, self)

    def destroy(self, ctx):
        super(Location, self).destroy(ctx)
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
            for tap in self.wiretaps:
                tap.tell(room_msg)

    def look(self, exclude_living=None, short=False):
        """returns a list of paragraph strings describing the surroundings, possibly excluding one living from the description list"""
        paragraphs = [color.bright("[" + self.name + "]")]
        if short:
            if self.exits:
                paragraphs.append("Exits: " + ", ".join(sorted(set(self.exits.keys()))))
            if self.items:
                item_names = sorted(item.name for item in self.items)
                paragraphs.append("You see: " + ", ".join(item_names))
            if self.livings:
                living_names = sorted(living.name for living in self.livings if living != exclude_living)
                if living_names:
                    paragraphs.append("Present: " + ", ".join(living_names))
            return paragraphs
        # normal (long) output
        if self.description:
            paragraphs.append(self.description)
        if self.exits:
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
        if items_with_short_descr:
            for item in items_with_short_descr:
                items_and_livings.append(item.short_description)
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
        if livings_with_short_descr:
            for living in livings_with_short_descr:
                items_and_livings.append(living.short_description)
        if items_and_livings:
            paragraphs.append(" ".join(items_and_livings))
        return paragraphs

    def search_living(self, name):
        """
        Search for a living in this location by its name (and title, if no names match)
        If there's more than one match, returns the first
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
        self.verbs.extend(obj.verbs)    # register custom verbs

    def remove(self, obj, actor):
        """Remove obj from this location (either a Living or an Item)"""
        if obj in self.livings:
            self.livings.remove(obj)
        elif obj in self.items:
            self.items.remove(obj)
        else:
            return   # just ignore an object that wasn't present in the first place
        obj.location = None
        for verb in obj.verbs:
            self.verbs.remove(verb)     # unregister custom verbs

    def handle_verb(self, parsed, actor):
        """Handle a custom verb. Return True if handled, False if not handled."""
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


_Limbo = Location("Limbo",
                     """
                     The intermediate or transitional place or state. There's only nothingness.
                     Livings end up here if they're not inside a proper location yet.
                     """)


class Exit(object):
    """
    An 'exit' that connects one location to another.
    You can use a Location object as target, or a string designating the location
    (for instance "town.square" means the square location object in game.zones.town).
    If using a string, it will be retrieved and bound at runtime.
    Short_description will be shown when the player looks around the room.
    Long_description is optional and will be shown instead if the player examines the exit.
    Supplying a direction on the exit is optional. It is only required when adding multiple
    exits on a location by using Location.add_exits().
    """
    def __init__(self, target_location, short_description, long_description=None, direction=None):
        assert target_location is not None
        assert isinstance(target_location, (Location, basestring_type)), "target must be a Location or a string"
        self.target = target_location
        self.bound = isinstance(target_location, Location)
        self.direction = self.name = direction      # direction and name can be None! Don't depend on them!
        try:
            self.short_description = short_description
        except AttributeError:
            pass   # this can occur if someone made it into a property
        try:
            self.long_description = long_description or self.short_description
        except AttributeError:
            pass   # this can occur if someone made it into a property
        mud_context.driver.register_exit(self)

    def __repr__(self):
        targetname = self.target.name if self.bound else self.target
        return "<base.Exit to '%s' @ 0x%x>" % (targetname, id(self))

    def bind(self, game_zones_module):
        """
        Binds the exit to the actual target_location object.
        Usually called by the driver before it starts player interaction.
        The caller needs to pass in the root module of the game zones (to avoid circular import dependencies)
        """
        if not self.bound:
            target_module, target_object = self.target.rsplit(".", 1)
            module = game_zones_module
            for name in target_module.split("."):
                module = getattr(module, name)
            target = getattr(module, target_object)
            assert isinstance(target, Location)
            self.target = target
            self.bound = True

    def allow_passage(self, actor):
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

    def activate(self, actor):
        # see MudObject
        raise ActionRefused("You can't activate that.")

    def deactivate(self, actor):
        # see MudObject
        raise ActionRefused("You can't deactivate that.")

    def manipulate(self, verb, actor):
        # see MudObject
        raise ActionRefused("It makes no sense to %s in that direction." % verb)

    def read(self, actor):
        # see MudObject
        raise ActionRefused("There's nothing to read there.")

    def handle_verb(self, parsed, actor):
        """Handle a custom verb. Return True if handled, False if not handled."""
        return False

    def notify_action(self, parsed, actor):
        """Notify the exit of an action performed by someone."""
        pass


class Living(MudObject):
    """
    Root class of the living entities in the mud world.
    Livings sometimes have a heart beat 'tick' that makes them interact with the world.
    They are always inside a Location (Limbo when not specified yet).
    They also have an inventory object, and you can test for containment with item in living.
    """
    def __init__(self, name, gender, race, title=None, description=None, short_description=None):
        # override the language help attributes inherited from the base object:
        self.gender = gender
        self.subjective = lang.SUBJECTIVE[self.gender]
        self.possessive = lang.POSSESSIVE[self.gender]
        self.objective = lang.OBJECTIVE[self.gender]
        # other stuff:
        self.location = _Limbo  # set transitional location
        self.privileges = set()  # probably only used for Players though
        self.aggressive = False
        self.money = 0.0  # the currency is determined by util.MoneyFormatter set in the driver
        self.stats = {}
        self.default_verb = "examine"
        self.race = race
        # Make a copy of the race stats, because they can change dynamically.
        # There's no need to copy the whole race data dict because it's available
        # from tale.races, look it up by the race name.
        self.stats = {}
        for stat_name, (stat_avg, stat_class) in races[race]["stats"].items():
            self.stats[stat_name] = stat_avg
        self.__inventory = set()
        self.wiretaps = weakref.WeakSet()     # wizard wiretaps for this location
        super(Living, self).__init__(name, title, description, short_description)

    def __getstate__(self):
        # can't serialize the wiretaps because it's a weakset. Too bad, just skip them.
        state = dict(self.__dict__)
        del state["wiretaps"]
        return state

    def __setstate__(self, state):
        self.__dict__ = state
        # restore the wireteaps to an empty weakset
        self.wiretaps = weakref.WeakSet()

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
        if actor is self or actor is not None and "wizard" in actor.privileges:
            assert isinstance(item, Item)
            self.__inventory.add(item)
            item.contained_in = self
            self.location.verbs.extend(item.verbs)   # register custom verbs
        else:
            raise ActionRefused("You can't do that.")

    def remove(self, item, actor):
        """remove an item from the inventory"""
        if actor is self or actor is not None and "wizard" in actor.privileges:
            self.__inventory.remove(item)
            item.contained_in = None
            for verb in item.verbs:
                self.location.verbs.remove(verb)     # unregister custom verbs
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
        self.wiretaps.clear()
        # @todo: remove attack status, etc.

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

    def move(self, target_location, actor=None, silent=False, is_player=False):
        """
        Leave the current location, enter the new location (transactional).
        Messages are being printed to the locations if the move was successful.
        """
        actor = actor or self
        if self.location:
            original_location = self.location
            self.location.remove(self, actor)
            try:
                target_location.insert(self, actor)
                self.unregister_all_inventory_verbs(original_location)
                self.register_all_inventory_verbs(target_location)
            except:
                # insert in target failed, put back in original location
                original_location.insert(self, actor)
                raise
            if not silent:
                original_location.tell("%s leaves." % lang.capital(self.title), exclude_living=self)
            # queue event
            if is_player:
                mud_context.driver.after_player_action(original_location.notify_player_left, self, target_location)
            else:
                mud_context.driver.after_player_action(original_location.notify_npc_left, self, target_location)
        else:
            target_location.insert(self, actor)
        if not silent:
            target_location.tell("%s arrives." % lang.capital(self.title), exclude_living=self)
        # queue event
        if is_player:
            mud_context.driver.after_player_action(target_location.notify_player_arrived, self, original_location)
        else:
            mud_context.driver.after_player_action(target_location.notify_npc_arrived, self, original_location)

    def register_all_inventory_verbs(self, location):
        """When moving the living to a new location, register all inventory custom verbs"""
        for item in self.__inventory:
            location.verbs.extend(item.verbs)

    def unregister_all_inventory_verbs(self, location):
        """When removing the living from a location, unregister all inventory custom verbs"""
        for item in self.__inventory:
            for verb in item.verbs:
                location.verbs.remove(verb)

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
            matches = [item for item in self.__inventory if item.name == name]
            if not matches:
                # try the aliases or titles
                matches = [item for item in self.__inventory if name in item.aliases or item.title.lower() == name]
        if not matches and include_location:
            containing_object = self.location
            matches = [item for item in self.location.items if item.name == name]
            if not matches:
                # try the aliases or titles
                matches = [item for item in self.location.items if name in item.aliases or item.title.lower() == name]
        if not matches and include_containers_in_inventory:
            # check if an item in the inventory might contain it
            for container in self.__inventory:
                containing_object = container
                try:
                    inventory = container.inventory
                except ActionRefused:
                    continue    # no access to inventory, just skip this item silently
                else:
                    matches = [item for item in inventory if item.name == name]
                    if not matches:
                        # try the aliases or titles
                        matches = [item for item in inventory if name in item.aliases or item.title.lower() == name]
                    if matches:
                        break
        return (matches[0], containing_object) if matches else (None, None)

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
        Also checks inventory items. Don't override this one in a subclass,
        override handle_verb instead.
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


class Container(Item):
    """
    A bag-type container (i.e. an item that acts as a container)
    Allows insert and remove, and examine its contents, as opposed to an Item
    You can test for containment with 'in': item in bag
    """
    def init(self):
        super(Container, self).init()
        self.__inventory = set()  # override the frozenset() from Item to allow true containment here

    def init_inventory(self, items):
        """Set the container's initial inventory"""
        assert len(self.__inventory) == 0
        self.__inventory = set(items)
        for item in items:
            item.contained_in = self

    @property
    def title(self):
        if isinstance(self.contained_in, Living):
            if self.__inventory:
                return self._title + color.dim(" (containing things)")
            else:
                return self._title + color.dim(" (empty)")
        return self._title

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
    def __init__(self, target_location, short_description, long_description=None, direction=None, locked=False, opened=True):
        super(Door, self).__init__(target_location, short_description, long_description, direction)
        self.locked = locked
        self.opened = opened
        if locked and opened:
            raise ValueError("door cannot be both locked and opened")
        self.__long_description_prefix = long_description or short_description
        self.door_code = None   # you can set this to any code that a key must match to unlock the door

    @property
    def long_description(self):
        if self.opened:
            status = "It is open "
        else:
            status = "It is closed "
        if self.locked:
            status += "and locked."
        else:
            status += "and unlocked."
        return self.__long_description_prefix + " " + status

    def __repr__(self):
        target = self.target.name if self.bound else self.target
        locked = "locked" if self.locked else "open"
        return "<base.Door '%s'->'%s' (%s) @ 0x%x>" % (self.direction, target, locked, id(self))

    def allow_passage(self, actor):
        """Is the actor allowed to move through this door?"""
        assert self.bound
        if not self.opened:
            raise ActionRefused("You can't go there; it's closed.")

    def open(self, item, actor):
        """Open the door with optional item. Notifies actor and room of this event."""
        if self.opened:
            raise ActionRefused("It's already open.")
        elif self.locked:
            raise ActionRefused("You try to open it, but it's locked.")
        else:
            self.opened = True
            actor.tell("You opened it.")
            who = lang.capital(actor.title)
            if self.direction:
                actor.tell_others("{Title} opened the exit %s." % self.direction)
            else:
                actor.tell_others("{Title} opened an exit.")

    def close(self, item, actor):
        """Close the door with optional item. Notifies actor and room of this event."""
        if not self.opened:
            raise ActionRefused("It's already closed.")
        self.opened = False
        actor.tell("You closed it.")
        who = lang.capital(actor.title)
        if self.direction:
            actor.tell_others("{Title} closed the exit %s." % self.direction)
        else:
            actor.tell_others("{Title} closed an exit.")

    def lock(self, item, actor):
        """Lock the door with the proper key."""
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
                actor.tell(color.dim("(You use your %s; %s matches the lock.)" % (key.title, key.subjective)))
            else:
                raise ActionRefused("You don't seem to have the means to lock it.")
        self.locked = False
        actor.tell("Your %s fits, it is now locked." % key.title)
        if self.direction:
            what = "the exit %s" % self.direction
        else:
            what = "an exit"
        actor.tell_others("{Title} locked %s with %s." % (what, lang.a(key.title)))

    def unlock(self, item, actor):
        """Unlock the door with the proper key."""
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
                actor.tell(color.dim("(You use your %s; %s matches the lock.)" % (key.title, key.subjective)))
            else:
                raise ActionRefused("You don't seem to have the means to unlock it.")
        self.locked = False
        actor.tell("Your %s fits, it is now unlocked." % key.title)
        if self.direction:
            what = "the exit %s" % self.direction
        else:
            what = "an exit"
        actor.tell_others("{Title} unlocked %s with %s." % (what, lang.a(key.title)))

    def check_key(self, item):
        """Check if the item is a proper key for this door (based on door_code)"""
        door_code = getattr(item, "door_code", None)
        return door_code and door_code == self.door_code

    def search_key(self, actor):
        """Does the actor have a proper key? Return the item if so, otherwise return None."""
        for item in actor.inventory:
            if self.check_key(item):
                return item
        return None


def heartbeat(klass):
    """
    Decorator to use on a class to make it have a heartbeat.
    Use sparingly as it is less efficient than using a deferred, because the driver
    has to call all heartbeats every tick even though they do nothing yet.
    With deferreds, the driver only calls a deferred at the time it is needed.
    """
    klass._register_heartbeat = True
    return klass
