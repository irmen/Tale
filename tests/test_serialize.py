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

    def assert_base_attrs(self, obj):
        self.assertEqual("name", obj.name)
        self.assertEqual("title", obj.title)
        self.assertEqual("description", obj.description)
        self.assertEqual("n", obj.gender)

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

    def test_player_and_soul(self):
        o = base.Living("name", "n", title="title", descr="description", race="dragon")
        x = serializecycle(o)
        # @todo check
        o = base.Soul()
        x = serializecycle(o)
        # @todo check
        p = player.Player("name", "n", descr="description")
        p.title = "title"
        p.money = 42
        x = serializecycle(p)
        # @todo check

    def test_storyconfig(self):
        s = StoryBase()
        s.server_mode = GameMode.IF
        s.display_gametime = True
        s.name = "test"
        x = serializecycle(s)
        # @todo check
        x = serializecycle(s.config)
        # @todo check

    def test_Context(self):
        c = util.Context.from_global(player_connection=42)
        with self.assertRaises(RuntimeError) as x:
            serializecycle(c)
        self.assertTrue(str(x.exception).startswith("cannot serialize context"))

    def test_Hints(self):
        h = hints.HintSystem()
        h.init([hints.Hint("start", None, "first")])
        h.checkpoint("checkpoint1", "something has been achieved")
        x = serializecycle(h)
        # @todo check

    def test_Deferreds(self):
        target = Thing()
        item = base.Item("key")
        deferreds = [driver.Deferred(datetime.datetime.now(), target.append, [1, 2, 3], {"kwarg": 42}),
                     driver.Deferred(datetime.datetime.now(), os.getcwd, [], None),
                     driver.Deferred(datetime.datetime.now(), module_level_func, [], None),
                     driver.Deferred(datetime.datetime.now(), item.init, [], None)]
        x = serializecycle(deferreds)
        # @todo check

    def test_bank(self):
        b = bank.Bank("atm")
        b.transaction_log.append("transaction: $10")
        x = serializecycle(b)
        # @todo check

    def test_money(self):
        m = basic.Money("cash", 987.65)
        x = serializecycle(m)
        # @todo check

    def test_catapult(self):
        c = basic.Catapult("catapult")
        c.aliases = {"weapon"}
        c.story_data = {"force": 99}
        c.verbs = {"shoot": "fire the weapon"}
        x = serializecycle(c)
        # @todo check

    def test_board(self):
        c = board.BulletinBoard("board")
        c.posts = {"post1": "hey there"}
        x = serializecycle(c)
        # @todo check


if __name__ == '__main__':
    unittest.main()
