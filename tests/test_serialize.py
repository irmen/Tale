"""
Unit tests for serialization

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import os
import unittest
import datetime

from tale import mud_context, races, base, player, util, hints, driver
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

    def test_basic(self):
        o = serializecycle(races.races)
        self.assertEqual(len(races.races), len(o))
        self.assertIn("golem", o)
        o = base.Item("name", "title", descr="description")
        o.aliases = ["alias"]
        x = serializecycle(o)
        # @todo check

    def test_items_and_container(self):
        o = base.Item("name", "title", descr="description")
        o.aliases = ["alias"]
        bag = base.Container("name", "title", descr="description")
        bag.insert(o, None)
        x = serializecycle(bag)
        # @todo check
        x = serializecycle(o)
        # @todo check
        o = base.Armour("a")
        x = serializecycle(o)
        # @todo check

    def test_location(self):
        room = base.Location("room", "description")
        x = serializecycle(room)
        # @todo check
        # now add some exits and a second location, and try again
        room2 = base.Location("room2", "description")
        exit1 = base.Exit("room2", room2, "to room2")
        exit2 = base.Exit("room", room, "back to room")
        room.add_exits([exit1])
        room2.add_exits([exit2])
        x = serializecycle([room, room2])
        # @todo check

    def test_exits_and_doors(self):
        o = base.Exit("east", "target", "somewhere")
        x = serializecycle(o)
        # @todo check
        o = base.Door("east", "target", "somewhere", locked=True, opened=False)
        self.assertEqual("somewhere It is closed and locked.", o.description)
        x = serializecycle(o)
        # @todo check

    def test_npc(self):
        o = base.Living("name", "n", title="title", descr="description", race="dragon")
        x = serializecycle(o)
        # @todo check

    def test_player_and_soul(self):
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
        c = util.Context(driver=mud_context.driver, clock=mud_context.driver.game_clock, config=mud_context.config, player_connection=42)
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


if __name__ == '__main__':
    unittest.main()
