import datetime
import importlib
import gzip
from typing import Any, Tuple, List, Optional, Dict, Type, Sequence, Union

from .base import Item, Location, Living, Exit, Door, MudObject, MudObjRegistry, Stats, _limbo
from .story import StoryConfig, MoneyType, GameMode, TickMethod
from .player import Player
from .errors import TaleError, ActionRefused
from .driver import Deferred
from .util import GameDateTime
from .shop import ShopBehavior, Shopkeeper
import serpent


def mudobj_ref(mudobj: MudObject) -> Optional[Tuple[int, str, str, str]]:
    """generate a serializable reference (vnum, name, classname, baseclassname) for a MudObject"""
    if mudobj:
        return mudobj.vnum, mudobj.name, qual_classname(mudobj), qual_baseclassname(mudobj)
    return None


def qual_classname(obj: Any, cls: bool=False) -> str:
    if not cls:
        obj = obj.__class__
    return obj.__module__ + "." + obj.__name__


def qual_baseclassname(obj: MudObject) -> str:
    mro = obj.__class__.__mro__
    if Location in mro:
        return qual_classname(Location, cls=True)
    elif Exit in mro:
        return qual_classname(Exit, cls=True)
    elif Player in mro:
        return qual_classname(Player, cls=True)
    elif Living in mro:
        return qual_classname(Living, cls=True)
    elif Item in mro:
        return qual_classname(Item, cls=True)
    else:
        raise ValueError("cannot determine Tale base class", obj)


class TaleSerializer:
    xor_key = 0x5c    # please do not hack the save files

    def __init__(self):
        serpent.register_class(Player, self.serialize_player)
        serpent.register_class(ShopBehavior, self.serialize_shopbehavior)
        serpent.register_class(Location, self.serialize_location)
        serpent.register_class(Stats, self.serialize_stats)
        serpent.register_class(Item, self.serialize_item)
        serpent.register_class(Living, self.serialize_living)
        serpent.register_class(Exit, self.serialize_exit)
        serpent.register_class(Deferred, self.serialize_deferred)
        self.serializer = serpent.Serializer(indent=True, module_in_classname=True)

    def serialize(self, story: StoryConfig, player: Player, items: Sequence[Item], livings: Sequence[Living],
                  locations: Sequence[Location], exits: Sequence[Exit],
                  deferreds: Sequence[Deferred], clock: GameDateTime):
        livings = [l for l in livings if l is not player]
        if _limbo not in locations:
            locations = list(locations)
            locations.append(_limbo)
        if any(i not in items for i in player.inventory):
            raise ValueError("missing item (from player inventory)")
        if any(i not in items for living in livings for i in living.inventory):
            raise ValueError("missing item (from living inventory)")
        if any(i not in items for loc in locations for i in loc.items):
            raise ValueError("missing item (from locations)")
        if any(l is not player and l not in livings for loc in locations for l in loc.livings):
            raise ValueError("missing living (from locations)")
        if any(living.location is not None and living.location not in locations for living in livings):
            raise ValueError("missing location (from livings)")
        if player.location is not None and player.location not in locations:
            raise ValueError("missing location (from player)")
        if any(e not in exits for loc in locations for e in loc.exits.values()):
            raise ValueError("missing exit (from location)")
        data = {
            # "story_version": story.version,
            # "tale_version_required": story.requires_tale,
            "story_config": story,
            "clock": clock,
            "items": items,
            "livings": livings,
            "locations": locations,
            "exits": exits,
            "deferreds": deferreds,
            "player": player,
        }
        serialized = self.serializer.serialize(data)
        return self.obfuscate(serialized)

    def obfuscate(self, data: bytes) -> bytes:
        data = gzip.compress(data)
        return b"TALESAVE1" + bytes(b ^ self.xor_key for b in data)

    def add_basic_properties(self, state: Dict[str, Any], obj: MudObject) -> None:
        state["__class__"] = qual_classname(obj)
        state["__base_class__"] = qual_baseclassname(obj)
        state["title"] = obj.title
        state["descr"] = obj.description
        state["short_descr"] = obj.short_description
        state["extra_desc"] = obj.extra_desc

    def add_inventory_property(self, state: Dict[str, Any], obj: MudObject) -> None:
        try:
            inv = obj.inventory     # type: ignore
        except (AttributeError, ActionRefused):
            pass   # this thing doesn't have inventory
        else:
            state["inventory"] = {mudobj_ref(m) for m in inv}

    def serialize_shopbehavior(self, obj: ShopBehavior, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
        state = dict(vars(obj))
        state["__class__"] = qual_classname(obj)
        state["forsale"] = {mudobj_ref(i) for i in state["forsale"]}
        ser._serialize(state, out, indentlevel)

    def serialize_deferred(self, obj: Deferred, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
        state = dict(vars(obj))
        state["__class__"] = qual_classname(obj)
        if not isinstance(state["owner"], str):
            try:
                state["owner"] = mudobj_ref(state["owner"])
            except Exception:
                # owner is not a regular mudobj
                state["owner"] = "class:" + qual_classname(state["owner"])
        ser._serialize(state, out, indentlevel)

    def serialize_stats(self, obj: Stats, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
        state = {
            "__class__": qual_classname(obj),
            "race": obj.race,
            "gender": obj.gender,
            "level": obj.level,
            "xp": obj.xp,
            "hp": obj.hp,
            "maxhp_dice": obj.maxhp_dice,
            "ac": obj.ac,
            "attack_dice": obj.attack_dice,
            "alignment": obj.alignment
            # the other attributes are re-initialized from the races table
        }
        ser._serialize(state, out, indentlevel)

    def serialize_player(self, obj: Player, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
        state = dict(vars(obj))
        # remove stuff we don't want to serialize at all
        unserialized_attrs = {"subjective", "possessive", "objective", "teleported_from", "soul",
                              "input_is_available", "transcript", "last_input_time", "previous_commandline"}
        skipped_attrs = set()
        for name in list(state):
            if name.startswith("_"):
                del state[name]
            elif name in unserialized_attrs:
                del state[name]
                skipped_attrs.add(name)
        if skipped_attrs != unserialized_attrs:
            raise TaleError("player unserialized_attrs inconsistency")

        # basic properties:
        self.add_basic_properties(state, obj)
        # attrs that are treated in a special way:
        state["race"] = obj.stats.race
        state["known_locations"] = {mudobj_ref(loc) for loc in state["known_locations"]}
        state["location"] = mudobj_ref(state["location"])
        state["inventory"] = {mudobj_ref(thing) for thing in obj.inventory}
        state["following"] = mudobj_ref(state["following"])
        ser._serialize(state, out, indentlevel)

    def serialize_item(self, obj: Item, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
        if obj.contained_in and obj not in obj.contained_in:
            raise TaleError("item {} containment inconsistency".format(obj))
        state = dict(vars(obj))
        # remove stuff we don't want to serialize at all
        for name in list(state):
            if name.startswith("_"):
                del state[name]
            elif name == "contained_in":  # where the item is located, is referenced from that container/living/location later.
                del state[name]
        self.add_basic_properties(state, obj)  # basic properties
        self.add_inventory_property(state, obj)  # inventory (of Container subtype)
        ser._serialize(state, out, indentlevel)

    def serialize_living(self, obj: Living, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
        if obj.location and obj.location is not _limbo and obj not in obj.location:
            raise TaleError("living {} location inconsistency".format(obj))
        state = dict(vars(obj))
        # remove stuff we don't want to serialize at all
        unserialized_attrs = {"subjective", "possessive", "objective", "teleported_from", "soul", "previous_commandline"}
        skipped_attrs = set()
        for name in list(state):
            if name.startswith("_"):
                del state[name]
            elif name in unserialized_attrs:
                del state[name]
                skipped_attrs.add(name)
        if skipped_attrs != unserialized_attrs:
            raise TaleError("living unserialized_attrs inconsistency")
        self.add_basic_properties(state, obj)  # basic properties
        # attrs that are treated in a special way:
        state["race"] = obj.stats.race
        state["location"] = mudobj_ref(state["location"])
        state["inventory"] = {mudobj_ref(thing) for thing in obj.inventory}
        state["following"] = mudobj_ref(state["following"])
        ser._serialize(state, out, indentlevel)

    def serialize_exit(self, obj: Exit, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
        state = dict(vars(obj))
        # remove stuff we don't want to serialize at all
        for name in list(state):
            if name.startswith("_") and name != "_target_str":
                del state[name]
        self.add_basic_properties(state, obj)
        state["target"] = mudobj_ref(state["target"])
        if "linked_door" in state:
            # it's probably a Door, and linked_door referes to another door (cyclic)
            state["linked_door"] = mudobj_ref(state["linked_door"])
        ser._serialize(state, out, indentlevel)

    def serialize_location(self, obj: Location, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
        state = dict(vars(obj))
        # remove stuff we don't want to serialize at all
        for name in list(state):
            if name.startswith("_"):
                del state[name]
        self.add_basic_properties(state, obj)
        # livings and items, and the exits, present in this location:
        state["livings"] = {mudobj_ref(l) for l in state["livings"]}
        state["items"] = {mudobj_ref(i) for i in state["items"]}
        state["exits"] = {mudobj_ref(e) for e in state["exits"].values()}
        ser._serialize(state, out, indentlevel)


class TaleDeserializer:
    def deserialize(self, data):
        return serpent.loads(self.deobfuscate(data))

    def deobfuscate(self, data: bytes) -> bytes:
        if not data.startswith(b"TALESAVE1"):
            return data
        return gzip.decompress(bytes(b ^ TaleSerializer.xor_key for b in data[9:]))

    def recreate_classes(self, literal, existing_object_lookup):
        t = type(literal)
        if t is set:
            return {self.recreate_classes(x, existing_object_lookup) for x in literal}
        if t is list:
            return [self.recreate_classes(x, existing_object_lookup) for x in literal]
        if t is tuple:
            return tuple(self.recreate_classes(x, existing_object_lookup) for x in literal)
        if t is dict:
            if "__class__" in literal:
                success, result = self.dict_to_class(literal, existing_object_lookup)
                if success:
                    if hasattr(result, "vnum"):
                        assert result.vnum == literal["vnum"]
                    return result
            result = {}
            for key, value in literal.items():
                result[key] = self.recreate_classes(value, existing_object_lookup)
            return result
        return literal

    def dict_to_class(self, d, existing_object_lookup) -> Tuple[bool, Any]:
        clz = d.get("__base_class__", None)
        if clz == "tale.player.Player":
            return True, self.make_Player(d)
        elif clz == "tale.base.Item":
            if d.get("__class__", None) == "tale.items.basic.Money":
                return True, self.make_Money(d, existing_object_lookup)
            return True, self.make_Item(d, existing_object_lookup)
        elif clz == "tale.base.Living":
            return True, self.make_Living(d, existing_object_lookup)
        elif clz == "tale.base.Exit":
            return True, self.make_Exit(d, existing_object_lookup)
        elif clz == "tale.base.Location":
            return True, self.make_Location(d, existing_object_lookup)
        # @todo add remaining classes here, if special serialization needs arise
        else:
            clz = d.get("__class__", None)
            if clz == "float":
                return True, float(d["value"])  # serpent encodes a float nan as a special class dict like this
            elif clz == "tale.base.Stats":
                return True, self.make_Stats(d)
            elif clz == "tale.driver.Deferred":
                return True, self.make_Deferred(d, existing_object_lookup)
            elif clz == "tale.util.GameDateTime":
                return True, self.make_GameDateTime(d)
            elif clz == "tale.story.StoryConfig":
                return True, self.make_StoryConfig(d)
            elif clz == "tale.shop.ShopBehavior":
                return True, self.make_ShopBehavior(d)
            else:
                return False, None

    def lookup_class(self, classname: str) -> Type:
        modulename, classname = classname.rsplit(".", 1)
        clazz = getattr(importlib.import_module(modulename), classname)
        return clazz

    def make_Player(self, data: Dict) -> Dict[str, Any]:
        p = Player(data.pop("name"), data.pop("gender"),
                   race=data.pop("race"), descr=data.pop("descr"), short_descr=data.pop("short_descr"))
        p.privileges = set(data.pop("privileges"))
        p.aliases = set(data.pop("aliases"))
        inv = data.pop("inventory")
        loc = data.pop("location")
        known_locs = data.pop("known_locations")
        p.stats = self.recreate_classes(data.pop("stats"), None)
        assert p.title == data.pop("title")
        following = data.pop("following")
        self.apply_attributes(p, data)
        p.init_nonserializables()
        return {
            "player": p,
            "inventory": inv,
            "location": loc,
            "known_locs": known_locs,
            "following": following
        }

    def make_Item(self, data: Dict, existing_object_lookup) -> Dict[str, Any]:
        try:
            item = existing_object_lookup.resolve_item_ref(data["vnum"], data["name"], data["__class__"], data["__base_class__"])
            if item.contained_in:
                wizard = Living("wizard", "m")
                wizard.privileges.add("wizard")
                item.contained_in.remove(item, wizard)   # will be hooked up later again
                assert item.contained_in is None
        except LookupError:
            # create new item
            itemclass = self.lookup_class(data["__class__"])
            item = MudObjRegistry.create_object(itemclass, data.pop("name"), title=data.pop("title"), descr=data.pop("descr"),
                                                short_descr=data.pop("short_descr"), vnum=data["vnum"])
        else:
            # re-init existing
            item.init_names(data.pop("name"), title=data.pop("title"), descr=data.pop("descr"), short_descr=data.pop("short_descr"))
        del data["vnum"]
        inv = data.pop("inventory", None)
        item.aliases = set(data.pop("aliases"))
        self.apply_attributes(item, data)
        return {
            "item": item,
            "contains": inv
        }

    def make_Money(self, data: Dict, existing_object_lookup) -> Dict[str, Any]:
        # Money has no constructor taking descr argument, but it takes a value argument
        try:
            money = existing_object_lookup.resolve_item_ref(data["vnum"], data["name"], data["__class__"], data["__base_class__"])
            if money.contained_in:
                wizard = Living("wizard", "m")
                wizard.privileges.add("wizard")
                money.contained_in.remove(money, wizard)   # will be hooked up later again
                assert money.contained_in is None
        except LookupError:
            # create new money item
            itemclass = self.lookup_class(data["__class__"])
            money = MudObjRegistry.create_object(itemclass, data.pop("name"), value=data.pop("value"), title=data.pop("title"),
                                                 short_descr=data.pop("short_descr"), vnum=data["vnum"])
        else:
            # re-init existing
            money.init_names(data.pop("name"), title=data.pop("title"), descr=data["descr"], short_descr=data.pop("short_descr"))
            money.value = data.pop("value")
        del data["vnum"]
        del data["descr"]
        money.aliases = set(data.pop("aliases"))
        self.apply_attributes(money, data)
        return {
            "item": money,
            "contains": None
        }

    def make_Living(self, data: Dict, existing_object_lookup) -> Dict[str, Any]:
        try:
            living = existing_object_lookup.resolve_living_ref(data["vnum"], data["name"], data["__class__"], data["__base_class__"])
        except LookupError:
            # create new living
            livingclass = self.lookup_class(data["__class__"])
            living = MudObjRegistry.create_object(livingclass, data.pop("name"), data.pop("gender"), race=data.pop("race"),
                                                  title=data.pop("title"), descr=data.pop("descr"), short_descr=data.pop("short_descr"),
                                                  vnum=data.pop("vnum"))
        else:
            # overwrite existing attributes
            living.init_gender(data.pop("gender"))
            living.init_names(data.pop("name"), title=data.pop("title"), descr=data.pop("descr"), short_descr=data.pop("short_descr"))
            del data["race"]
        living.aliases = set(data.pop("aliases"))
        living.privileges = set(data.pop("privileges"))
        inv = data.pop("inventory")
        loc = data.pop("location")
        following = data.pop("following")
        living.stats = self.recreate_classes(data.pop("stats"), None)
        if isinstance(living, Shopkeeper):
            # special handling of Shopkeepers
            self.shop = self.make_ShopBehavior(data.pop("shop"))
        self.apply_attributes(living, data)
        return {
            "living": living,
            "inventory": inv,
            "location": loc,
            "following": following
        }

    def make_StoryConfig(self, data: Dict) -> StoryConfig:
        conf = StoryConfig()
        epoch = data.pop("epoch")
        conf.epoch = self.parse_datestr(epoch) if epoch else None
        conf.money_type = MoneyType(data.pop("money_type"))
        conf.server_mode = GameMode(data.pop("server_mode"))
        conf.supported_modes = {GameMode(m) for m in data.pop("supported_modes")}
        conf.server_tick_method = TickMethod(data.pop("server_tick_method"))
        self.apply_attributes(conf, data)
        return conf

    def make_GameDateTime(self, data: Dict) -> GameDateTime:
        return GameDateTime(self.parse_datestr(data["clock"]), data["times_realtime"])

    def make_ShopBehavior(self, data: Dict) -> ShopBehavior:
        shop = ShopBehavior()
        shop.willbuy = set(data.pop("willbuy"))
        shop.wontdealwith = set(data.pop("wontdealwith"))
        self.apply_attributes(shop, data)
        return shop

    def make_Stats(self, data: Dict) -> Stats:
        if data["race"]:
            stats = Stats.from_race(data["race"], gender=data["gender"])
        else:
            stats = Stats()
        self.apply_attributes(stats, data)
        return stats

    def make_Deferred(self, data: Dict, existing_object_lookup) -> Deferred:
        due = self.parse_datestr(data["due_gametime"])
        d = Deferred(due, qual_classname, data["vargs"], data["kwargs"], periodical=data["periodical"])   # create for dummy action
        d.action = data["action"]
        d.owner = existing_object_lookup.resolve_ref(*data["owner"])
        return d

    def make_Exit(self, data: Dict, existing_object_lookup) -> Union[Exit, Door]:
        exit = existing_object_lookup.resolve_exit(data["vnum"], data["name"], data["__class__"], data["__base_class__"])
        target_loc = existing_object_lookup.resolve_location_ref(*data["target"])
        if exit.target is not target_loc:
            raise TaleError("exit target location changed, exit vnum " + str(exit.vnum))
        # we only load a few things from the save game data, and we assume the description texts don't change
        exit.name = data["name"]
        exit.aliases = set(data.pop("aliases"))
        exit.verbs = data["verbs"]
        exit.story_data = data["story_data"]
        exit._target_str = data.get("_target_str")
        if isinstance(exit, Door):
            exit.locked = data["locked"]
            exit.opened = data["opened"]
            exit.key_code = data["key_code"]
            if data["linked_door"]:
                linked_door = existing_object_lookup.resolve_exit(*data["linked_door"])
                if exit.linked_door is not linked_door:
                    raise TaleError("door linked door changed, door vnum " + str(exit.vnum))
        return exit

    def make_Location(self, data: Dict, existing_object_lookup) -> Location:
        # for now, we only support a static configuration of locs.
        # this means we won't create new locs, only update existing locs.
        loc = existing_object_lookup.resolve_location_ref(data["vnum"], data["name"], data["__class__"], data["__base_class__"])
        saved_exit_vnums = set(x[0] for x in data["exits"])
        if saved_exit_vnums != set(x.vnum for x in loc.exits.values()):
            raise TaleError("exits mismatch for location vnum " + str(loc.vnum))
        # we only set a few things from the saved game data for a location
        # most importantly: the items in here, and the livings walking around here
        # a requirement is that the exits don't change so we don't have to hook those up here as well.
        loc.name = data["name"]
        loc.aliases = set(data["aliases"])
        loc.verbs = data["verbs"]
        loc.story_data = data["story_data"]
        loc.items = {existing_object_lookup.resolve_item_ref(*ref) for ref in data["items"]}
        for thing in loc.items:
            if thing.contained_in and thing.contained_in is not loc:
                # remove the item from its original location, it was moved here
                thing.contained_in.remove(thing, None)
            thing.contained_in = loc
        # livings are moved in the correct location when they're created elsewhere.
        return loc

    def parse_datestr(self, datestr: str) -> datetime.datetime:
        if '.' not in datestr:
            datestr += ".0"
        return datetime.datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S.%f")

    def apply_attributes(self, obj: Any, data: Dict) -> None:
        for name, value in data.items():
            if name.startswith("__"):
                continue
            if not hasattr(obj, name):
                raise AttributeError("{}.{} doesn't exist".format(obj.__class__, name))
            atype = type(getattr(obj, name))
            if type(value) is not atype:
                if type(value) is int and atype is float:
                    # special case for int vs float (accept ints if type is float)
                    value = float(value)
                else:
                    raise TypeError("{}.{} has different type".format(obj.__class__, name))
            setattr(obj, name, value)
