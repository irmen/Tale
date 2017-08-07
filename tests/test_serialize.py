"""
Unit tests for serialization

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import os
import unittest
import datetime

from tale import mud_context, races, base, player, util, hints, driver
from tale.items import basic, bank, board
from tale.story import *
from tale.savegames import TaleSerializer, TaleDeserializer

from tests.supportstuff import FakeDriver, Thing


def serializecycle(obj):
    ser = TaleSerializer()
    deser = TaleDeserializer()
    p = player.Player("julie", "f")
    data = ser.serialize(None, p, [obj], [], [], [], [], None)
    stuff = deser.deserialize(data)
    items = stuff["items"]
    assert len(items) == 1
    return items[0]


def module_level_func(ctx):
    assert ctx is not None


class TestSerializing(unittest.TestCase):
    def setUp(self):
        mud_context.driver = FakeDriver()
        mud_context.config = StoryConfig()
        mud_context.resources = mud_context.driver.resources

    def test_fundamentals(self):
        o = serializecycle(races.races)
        assert len(races.races) == len(o)
        assert "golem" in o
        o = base.Item("name", "title", descr="description", short_descr="short description")
        o.aliases = ["alias"]
        o.default_verb = "push"
        o.extra_desc = {"thing": "there's a thing"}
        o.rent = 99
        o.value = 88
        o.story_data["data"] = 42
        o.weight = 123.0
        loc = base.Location("location")
        loc.insert(o, None)
        x = serializecycle(o)
        assert isinstance(x, dict)
        assert x["__base_class__"] == "tale.base.Item"
        assert x["__class__"] == "tale.base.Item"
        assert x["aliases"] == ["alias"]
        assert x["default_verb"] == "push"
        assert x["descr"] == "description"
        assert x["extra_desc"] == {"thing": "there's a thing"}
        assert x["name"] == "name"
        assert x["rent"] == 99
        assert x["value"] == 88
        assert x["short_descr"] == "short description"
        assert x["story_data"] == {"data": 42}
        assert x["takeable"] == True
        assert x["title"] == "title"
        assert x["vnum"] > 0
        assert x["weight"] == 123.0
        assert "inventory" not in x
        assert "location" not in x and "contained_in" not in x, "item is referenced from its location instead"

    def test_items_and_container(self):
        o = base.Item("name1", "title1", descr="description1")
        o.aliases = ["alias1"]
        bag = base.Container("name2", "title2", descr="description2")
        bag.insert(o, None)
        x = serializecycle(bag)
        x_inv = x["inventory"]
        assert isinstance(x_inv, set)
        assert len(x_inv) == 1
        x_contained = x_inv.pop()
        assert len(x_contained) == 4
        assert x_contained[0] > 1
        assert x_contained[1] == 'name1'
        assert x_contained[2] == 'tale.base.Item'
        assert x_contained[3] == 'tale.base.Item'
        x = serializecycle(o)
        assert "inventory" not in x
        assert "location" not in x and "contained_in" not in x, "item is referenced from its location instead"
        o = base.Armour("a")
        x = serializecycle(o)
        assert x["__class__"] == "tale.base.Armour"
        assert x["__base_class__"] == "tale.base.Item"

    def test_location(self):
        room = base.Location("room", "description")
        thing = base.Item("thing")
        room.insert(thing, None)
        npc = base.Living("dog", "m")
        room.insert(npc, None)
        x = serializecycle(room)
        assert x["__class__"] == "tale.base.Location"
        assert x["name"] == "room"
        assert x["descr"] == "description"
        assert x["exits"] == ()
        assert len(x["items"]) == 1
        assert len(x["livings"]) == 1
        assert isinstance(x["items"], set)
        assert isinstance(x["livings"], set)
        x_item = x["items"].pop()
        x_living = x["livings"].pop()
        assert len(x_item) == 4
        assert x_item[0] > 0
        assert x_item[1] == "thing"
        assert len(x_living) == 4
        assert x_living[0] > 0
        assert x_living[1] == "dog"
        # now add some exits and a second location, and try again
        room2 = base.Location("room2", "description")
        exit1 = base.Exit("room2", room2, "to room2")
        exit2 = base.Exit("room", room, "back to room")
        room.add_exits([exit1])
        room2.add_exits([exit2])
        x1, x2 = serializecycle([room, room2])
        assert len(x1["exits"]) == 1
        assert isinstance(x1["exits"], set)
        assert len(x2["exits"]) == 1
        assert isinstance(x2["exits"], set)
        x_exit = x1["exits"].pop()
        assert len(x_exit) == 4
        assert x_exit[0] > 0
        assert x_exit[1] == "room2"
        assert x_exit[2] == x_exit[3] == "tale.base.Exit"
        assert x2["name"] == "room2"
        x_exit = x2["exits"].pop()
        assert len(x_exit) == 4
        assert x_exit[0] > 0
        assert x_exit[1] == "room"

    def test_exits_and_doors(self):
        o = base.Exit("east", "target", "somewhere")
        o.enter_msg = "you enter a dark hallway"
        x = serializecycle(o)
        assert x["__class__"] == "tale.base.Exit"
        assert x["_target_str"] == "target"
        assert x["target"] is None
        assert x["descr"] == x["short_descr"] == "somewhere"
        assert x["enter_msg"] == "you enter a dark hallway"
        assert x["name"] == "east"
        assert x["title"] == "Exit to <unbound:target>"
        assert x["vnum"] > 0
        o = base.Door("east", "target", "somewhere", locked=True, opened=False, key_code="123")
        o.enter_msg = "going through"
        assert o.description == "somewhere It is closed and locked."
        x = serializecycle(o)
        assert x["__class__"] == "tale.base.Door"
        assert x["_target_str"] == "target"
        assert x["target"] is None
        assert x["descr"] == "somewhere It is closed and locked."
        assert x["short_descr"] == "somewhere"
        assert x["enter_msg"] == "going through"
        assert x["key_code"] == "123"
        assert x["linked_door"] is None
        assert x["name"] == "east"
        assert x["title"] == "Exit to <unbound:target>"
        assert x["locked"] == True
        assert x["opened"] == False
        assert x["vnum"] > 0

    def test_exit_pair(self):
        room1 = base.Location("room1")
        room2 = base.Location("room2")
        e1, e2 = base.Exit.connect(room1, "room2", "to room 2", None, room2, "room1", "to room 1", None)
        x = serializecycle(e1)
        assert x["_target_str"] == ""
        assert len(x["target"]) == 4
        assert x["target"][0] > 1
        assert x["target"][1] == "room2"
        assert x["target"][2] == x["target"][3] == "tale.base.Location"
        x = serializecycle(e2)
        assert x["_target_str"] == ""
        assert len(x["target"]) == 4
        assert x["target"][0] > 1
        assert x["target"][1] == "room1"
        assert x["target"][2] == x["target"][3] == "tale.base.Location"

    def test_door_pair(self):
        room1 = base.Location("room1")
        room2 = base.Location("room2")
        d1, d2 = base.Door.connect(room1, "room2", "to room 2", None, room2, "room1", "to room 1", None)
        x = serializecycle(d1)
        assert x["_target_str"] == ""
        assert len(x["target"]) == 4
        assert x["target"][0] > 1
        assert x["target"][1] == "room2"
        assert x["target"][2] == x["target"][3] == "tale.base.Location"
        assert len(x["linked_door"]) == 4
        assert x["linked_door"][0] > 1
        assert x["linked_door"][1] == "room1"
        assert x["linked_door"][2] == "tale.base.Door"
        assert x["linked_door"][3] == "tale.base.Exit"
        x = serializecycle(d2)
        assert x["_target_str"] == ""
        assert len(x["target"]) == 4
        assert x["target"][0] > 1
        assert x["target"][1] == "room1"
        assert x["target"][2] == x["target"][3] == "tale.base.Location"
        assert len(x["linked_door"]) == 4
        assert x["linked_door"][0] > 1
        assert x["linked_door"][1] == "room2"
        assert x["linked_door"][2] == "tale.base.Door"
        assert x["linked_door"][3] == "tale.base.Exit"

    def test_living_player(self):
        thing = base.Item("thing")
        p = player.Player("playername", "n", descr="description")
        p.insert(thing, None)
        p.title = "title"
        p.money = 42
        p.brief = True
        p.story_data = {"data": 42}
        p.privileges.add("wizard")
        o = base.Living("name", "f", title="title", descr="description", race="dragon")
        o.aggressive = True
        o.following = p
        o.is_pet = True
        o.stats.attack_dice = "2d8"
        o.stats.level = 12
        o.stats.hp = 100
        x = serializecycle(o)
        assert x["__class__"] == "tale.base.Living"
        assert x["aggressive"] == True
        assert len(x["following"]) == 4
        assert x["following"][1] == "playername"
        assert x["is_pet"] == True
        assert x["location"][1] == "Limbo"
        assert x["race"] == "dragon"
        assert len(x["privileges"]) == 0
        assert "soul" not in x
        assert "teleported_from" not in x
        s = x["stats"]
        assert s["gender"] == "f"
        assert s["race"] == "dragon"
        assert s["attack_dice"] == "2d8"
        assert s["level"] == 12
        assert s["hp"] == 100
        x = serializecycle(p)
        assert x["__class__"] == x["__base_class__"] == "tale.player.Player"
        assert x["brief"] == True
        assert x["location"][1] == "Limbo"
        assert x["money"] == 42
        assert x["name"] == "playername"
        assert x["story_data"]["data"] == 42
        assert x["turns"] == 0
        assert x["screen_width"] == p.screen_width
        assert x["hints"]["__class__"] == "tale.hints.HintSystem"
        assert x["hints"]["checkpoints"] == [None]
        assert x["stats"]["race"] == x["race"] == "human"
        assert x["stats"]["xp"] == 0
        assert len(x["inventory"]) == 1
        inv = x["inventory"].pop()
        assert inv[1] == "thing"

    def test_storyconfig(self):
        s = StoryConfig()
        s.server_mode = GameMode.IF
        s.display_gametime = True
        s.name = "test"
        x = serializecycle(s)
        assert x["__class__"] == "tale.story.StoryConfig"
        assert x["gametime_to_realtime"] == 1
        assert x["display_gametime"] == True
        assert x["name"] == "test"
        assert x["server_mode"] == "if"
        assert x["supported_modes"] == {"if"}

    def test_context(self):
        c = util.Context.from_global(player_connection=42)
        with self.assertRaises(RuntimeError) as x:
            serializecycle(c)
        self.assertTrue(str(x.exception).startswith("cannot serialize context"))

    def test_hints(self):
        h = hints.HintSystem()
        h.init([hints.Hint("start", None, "first")])
        h.checkpoint("checkpoint1", "something has been achieved")
        x = serializecycle(h)
        assert x["__class__"] == "tale.hints.HintSystem"
        assert x["active_hints"] == []
        assert len(x["all_hints"]) == 1
        h = x["all_hints"][0]
        assert h["__class__"] == "tale.hints.Hint"
        assert h["checkpoint"] == "start"
        assert h["text"] == "first"
        assert x["checkpoints"] == [None, 'checkpoint1']
        assert x["recap_log"] == ["something has been achieved"]

    def test_deferreds(self):
        target = Thing()
        item = base.Item("key")
        now = datetime.datetime.now()
        deferreds = [driver.Deferred(now, target.append, [1, 2, 3], {"kwarg": 42}),
                     driver.Deferred(now, os.getcwd, [], None),
                     driver.Deferred(now, module_level_func, [], None),
                     driver.Deferred(now, item.init, [], None, periodical=(11.1, 22.2))]
        x1, x2, x3, x4 = serializecycle(deferreds)
        assert x1["__class__"] == "tale.driver.Deferred"
        assert x1["action"] == "append"
        assert x1["vargs"] == [1, 2, 3]
        assert x1["kwargs"] == {"kwarg": 42}
        assert x1["periodical"] is None
        assert x1["owner"] == "class:tests.supportstuff.Thing"
        assert x1["due_gametime"] == now.isoformat()
        assert x2["action"] == "getcwd"
        assert x2["owner"] in ("module:os", "module:nt", "module:posix")
        assert x3["action"] == "module_level_func"
        assert x3["owner"] == "module:tests.test_serialize"
        assert x4["action"] == "init"
        assert len(x4["owner"]) == 4
        assert x4["owner"][1] == "key"
        assert x4["periodical"] == (11.1, 22.2)

    def test_bank(self):
        b = bank.Bank("atm")
        b.accounts["test"] = 55
        b.transaction_log.append("transaction: $10")
        x = serializecycle(b)
        assert x["__class__"] == "tale.items.bank.Bank"
        assert x["__base_class__"] == "tale.base.Item"
        assert x["accounts"] == {"test": 55}
        assert x["storage_file"] is None
        assert x["takeable"] == False
        assert x["transaction_log"] == ["transaction: $10"]
        assert x["verbs"]["balance"] is not None
        assert x["verbs"]["deposit"] is not None
        assert x["verbs"]["withdraw"] is not None

    def test_money(self):
        m = basic.Money("cash", 987.65)
        x = serializecycle(m)
        assert x["__class__"] == "tale.items.basic.Money"
        assert x["__base_class__"] == "tale.base.Item"
        assert x["title"] == "pile of money"
        assert x["descr"] == "It looks to be about 900 dollars."
        assert x["name"] == "cash"
        assert x["value"] == 987.65

    def test_catapult(self):
        c = basic.Catapult("catapult")
        c.aliases = {"weapon"}
        c.story_data = {"force": 99}
        c.verbs = {"shoot": "fire the weapon"}
        x = serializecycle(c)
        assert x["__class__"] == "tale.items.basic.Catapult"
        assert x["__base_class__"] == "tale.base.Item"
        assert x["aliases"] == {"weapon"}
        assert x["story_data"] == {"force": 99}
        assert x["takeable"] == True
        assert x["value"] == 15.0
        assert x["name"] == "catapult"
        assert x["verbs"]["shoot"] is not None

    def test_board(self):
        c = board.BulletinBoard("board")
        c.posts = {"post1": "hey there"}
        c.dummy = "dummyvalue"
        x = serializecycle(c)
        assert x["__class__"] == "tale.items.board.BulletinBoard"
        assert x["__base_class__"] == "tale.base.Item"
        assert x["descr"].startswith("\nThere's a message on it")
        assert x["name"] == "board"
        assert x["verbs"]["list"] is not None
        assert x["verbs"]["post"] is not None
        assert x["verbs"]["read"] is not None
        assert x["verbs"]["remove"] is not None
        assert x["verbs"]["reply"] is not None
        assert x["verbs"]["write"] is not None
        assert "posts" not in x, "default serpent doesn't serialize properties"
        assert x["dummy"] == "dummyvalue"


if __name__ == '__main__':
    unittest.main()
