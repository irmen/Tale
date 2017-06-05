import codecs
import hmac
import importlib
import pprint
from typing import Any, Tuple, List, Optional, Dict, Set, FrozenSet, Type, ByteString

from .base import Item, Location, Living, Exit, MudObject, Stats, _limbo
from .items.basic import Drink, GameClock
from .story import StoryConfig
from .player import Player
from .errors import TaleError
from .hints import HintSystem
from .driver import Deferred
import serpent


def mudobj_ref(mudobj: MudObject) -> Optional[Tuple[int, str, str]]:
    """generate a serializable reference (vnum, name, classname) for a MudObject"""
    if mudobj:
        return mudobj.vnum, mudobj.name, qual_classname(mudobj)
    return None


def qual_classname(obj: Any, cls: bool=False) -> str:
    if not cls:
        obj = obj.__class__
    return obj.__module__ + "." + obj.__name__


class TaleSerializer:
    xor_key = 0x5c
    hmac_key = b"please do not hack the save files"

    def __init__(self):
        self.serializer = serpent.Serializer(indent=True, module_in_classname=True)

    def serialize(self, story: StoryConfig, player: Player, items: FrozenSet[Item], livings: FrozenSet[Living],
                  locations: FrozenSet[Location], exits: FrozenSet[Exit],
                  deferreds: FrozenSet[Deferred], clock: GameClock):
        livings -= {player}
        locations |= {_limbo}
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
            "player": player,
            "items": list(items),
            "livings": list(livings),
            "locations": list(locations),
            "exits": list(exits),
            "deferreds": list(deferreds),
        }
        serialized = self.serializer.serialize(data)
        return self.encrypt(serialized)

    def encrypt(self, data: ByteString) -> ByteString:
        digest = hmac.HMAC(key=self.hmac_key, msg=data, digestmod="sha").hexdigest()
        data = b"digest=" + digest.encode("ascii") + b"\n" + data
        return b"TALESAVE" + bytes(b ^ self.xor_key for b in data)

    def decrypt(self, data: ByteString) -> ByteString:
        if not data.startswith(b"TALESAVE"):
            return data
        data = bytes(b ^ self.xor_key for b in data[8:])
        digest, data = data.split(maxsplit=1)
        if not digest.startswith(b"digest="):
            raise TaleError("corrupt or hacked save game file")
        check = digest.split(b"=")[1].decode("ascii")
        calculated = hmac.HMAC(key=self.hmac_key, msg=data, digestmod="sha").hexdigest()
        if check != calculated:
            raise IOError("corrupt or hacked save game file")
        return data

    @staticmethod
    def add_basic_properties(state: Dict[str, Any], obj: MudObject) -> None:
        state["__class__"] = qual_classname(obj)
        mro = obj.__class__.__mro__
        if Location in mro:
            state["__base_class__"] = qual_classname(Location, cls=True)
        elif Exit in mro:
            state["__base_class__"] = qual_classname(Exit, cls=True)
        elif Player in mro:
            state["__base_class__"] = qual_classname(Player, cls=True)
        elif Living in mro:
            state["__base_class__"] = qual_classname(Living, cls=True)
        elif Item in mro:
            state["__base_class__"] = qual_classname(Item, cls=True)
        else:
            raise ValueError("cannot determine Tale base class", obj)
        state["title"] = obj.title
        state["descr"] = obj.description
        state["short_descr"] = obj.short_description
        state["extra_desc"] = obj.extra_desc

    @staticmethod
    def serialize_stats(obj: Stats, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
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

    @staticmethod
    def serialize_player(obj: Player, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
        state = dict(vars(obj))
        # remove stuff we don't want to serialize at all
        unserialized_attrs = {"subjective", "possessive", "objective", "teleported_from", "soul",
                              "input_is_available", "transcript", "previous_commandline", "last_input_time"}
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
        TaleSerializer.add_basic_properties(state, obj)
        # attrs that are treated in a special way:
        state["race"] = obj.stats.race
        state["known_locations"] = {mudobj_ref(loc) for loc in state["known_locations"]}
        state["location"] = mudobj_ref(state["location"])
        state["inventory"] = {mudobj_ref(thing) for thing in obj.inventory}
        ser._serialize(state, out, indentlevel)

    @staticmethod
    def serialize_item(obj: Item, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
        if obj.contained_in and obj not in obj.contained_in:
            raise TaleError("item {} containment inconsistency".format(obj))
        state = dict(vars(obj))
        # remove stuff we don't want to serialize at all
        for name in list(state):
            if name.startswith("_"):
                del state[name]
            elif name in ["contained_in"]:
                del state[name]
        # basic properties:
        TaleSerializer.add_basic_properties(state, obj)
        ser._serialize(state, out, indentlevel)

    @staticmethod
    def serialize_living(obj: Living, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
        if obj.location and obj.location is not _limbo and obj not in obj.location:
            raise TaleError("living {} location inconsistency".format(obj))
        state = dict(vars(obj))
        # remove stuff we don't want to serialize at all
        unserialized_attrs = {"subjective", "possessive", "objective", "teleported_from", "soul"}
        skipped_attrs = set()
        for name in list(state):
            if name.startswith("_"):
                del state[name]
            elif name in unserialized_attrs:
                del state[name]
                skipped_attrs.add(name)
        if skipped_attrs != unserialized_attrs:
            raise TaleError("living unserialized_attrs inconsistency")
        # basic properties:
        TaleSerializer.add_basic_properties(state, obj)
        # attrs that are treated in a special way:
        state["race"] = obj.stats.race
        state["location"] = mudobj_ref(state["location"])
        state["inventory"] = {mudobj_ref(thing) for thing in obj.inventory}
        ser._serialize(state, out, indentlevel)

    def deserialize(self, data):
        return serpent.loads(self.decrypt(data))

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
            return True, self.make_Item(d, existing_object_lookup)
        elif clz == "tale.base.Living":
            return True, self.make_Living(d, existing_object_lookup)
        else:
            clz = d.get("__class__", None)
            if clz == "float":
                return True, float(d["value"])  # serpent encodes a float nan as a special class dict like this
            elif clz == "tale.base.Stats":
                return True, self.make_Stats(d)
            elif clz == "tale.hints.HintSystem":
                return True, self.make_HintSystem(d)
            else:
                return False, None

    def make_Player(self, data: Dict) -> Dict[str, Any]:
        p = Player(data.pop("name"), data.pop("gender"),
                   race=data.pop("race"), descr=data.pop("descr"), short_descr=data.pop("short_descr"))
        p.privileges = set(data.pop("privileges"))
        p.aliases = set(data.pop("aliases"))
        inv = data.pop("inventory")
        loc = data.pop("location")
        known_locs = data.pop("known_locations")
        p.hints = self.recreate_classes(data.pop("hints"), None)
        p.stats = self.recreate_classes(data.pop("stats"), None)
        old_vnum = data.pop("vnum")
        assert p.title == data.pop("title")
        self.apply_attributes(p, data)
        p.init_nonserializables()
        return {
            "player": p,
            "inventory": inv,
            "location": loc,
            "known_locs": known_locs,
            "old_vnum": old_vnum
        }

    def lookup_class(self, classname: str) -> Type:
        modulename, classname = classname.rsplit(".", 1)
        clazz = getattr(importlib.import_module(modulename), classname)
        return clazz

    def make_Item(self, data: Dict, existing_object_lookup) -> Dict[str, Any]:
        old_vnum = data["vnum"]
        item = existing_object_lookup.item(data["vnum"], data["name"], data["__class__"])
        if item:
            # overwrite existing attributes
            item.init_names(data.pop("name"), title=data.pop("title"), descr=data.pop("descr"), short_descr=data.pop("short_descr"))
        else:
            # create new item
            itemclass = self.lookup_class(data["__class__"])
            item = itemclass(data.pop("name"), title=data.pop("title"), descr=data.pop("descr"), short_descr=data.pop("short_descr"))
        del data["vnum"]
        item.aliases = set(data.pop("aliases"))
        self.apply_attributes(item, data)
        return {
            "old_vnum": old_vnum,
            "item": item
        }

    def make_Living(self, data: Dict, existing_object_lookup) -> Dict[str, Any]:
        living = existing_object_lookup.living(data["vnum"], data["name"], data["__class__"])
        if living:
            # overwrite existing attributes
            del data["vnum"]
            living.init_gender(data.pop("gender"))
            living.init_names(data.pop("name"), title=data.pop("title"), descr=data.pop("descr"), short_descr=data.pop("short_descr"))
        else:
            # create new item
            livingclass = self.lookup_class(data["__class__"])
            living = livingclass(data.pop("name"), data.pop("gender"), race=data.pop("race"),
                                 title=data.pop("title"), descr=data.pop("descr"), short_descr=data.pop("short_descr"))
        living.aliases = set(data.pop("aliases"))
        living.privileges = set(data.pop("privileges"))
        inv = data.pop("inventory")
        loc = data.pop("location")
        living.stats = self.recreate_classes(data.pop("stats"), None)
        old_vnum = data.pop("vnum")
        self.apply_attributes(living, data)
        return {
            "living": living,
            "inventory": inv,
            "location": loc,
            "old_vnum": old_vnum
        }

    def make_Stats(self, data: Dict) -> Stats:
        if data["race"]:
            stats = Stats.from_race(data["race"], gender=data["gender"])
        else:
            stats = Stats()
        self.apply_attributes(stats, data)
        return stats

    def make_HintSystem(self, data: Dict) -> HintSystem:
        hs = HintSystem()
        self.apply_attributes(hs, data)
        return hs

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


def serialize_dummy(obj: Any, ser: serpent.Serializer, out: List[str], indentlevel: int) -> None:
    print("SERIALIZE", obj, " @@@TODO@@@") # XXX
    out.append("'@@@TODO@@@'")

serpent.register_class(Player, TaleSerializer.serialize_player)
serpent.register_class(Location, serialize_dummy)
serpent.register_class(Stats, TaleSerializer.serialize_stats)
serpent.register_class(Item, TaleSerializer.serialize_item)
serpent.register_class(Living, TaleSerializer.serialize_living)
serpent.register_class(Exit, serialize_dummy)


#---------------------test code--------------------

def test():
    cof = Drink("coffee")
    cof.contents = "coffee"
    cof.capacity = 99
    loc = Location("house")
    l = Living("rat", "m", race="rodent")
    e = Exit("south", loc, "going south")
    loc.add_exits([e])
    p = Player("julie", "f", short_descr="short description of player")
    p.story_data["derp"] = "HELLO!!!"
    p.privileges.add("wizard")
    p.money = 9.99

    loc.insert(p, p)
    p.known_locations.add(loc)
    p.insert(cof, p)

    ts = TaleSerializer()
    story = StoryConfig()
    story.requires_tale = "2.3"
    story.version = "9.1beta"
    story.name = "Test serialization story"
    clock = GameClock("ticker")
    d = ts.serialize(story, p, {cof}, {p, l}, {loc}, {e}, {}, clock)
    print(d.decode("utf-8"))
    p2 = ts.deserialize(d)
    print("------deserialized-----")
    pprint.pprint(p2)
    print("-------2classes--------")

    class ExistingObjectGetter:
        def item(self, vnum: int, name: str, classname: str) -> Item:
            pass

        def living(self, vnum: int, name: str, classname: str) -> Living:
            pass

    p2 = ts.recreate_classes(p2, existing_object_lookup=ExistingObjectGetter())
    pprint.pprint(p2)

    p2 = p2["player"]["player"]
    assert repr(p.stats) == repr(p2.stats)
    assert p.money == p2.money
    assert p.aliases == p2.aliases
    assert p.privileges == p2.privileges
    assert p.subjective == p2.subjective
    assert p.title == p2.title
    assert p.short_description == p2.short_description
    assert p.story_data == p2.story_data


if __name__ == '__main__':
    test()
