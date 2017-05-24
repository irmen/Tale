"""
Unit tests for serialization

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import pickle
import unittest

from tale import mud_context, races, base, player, util, hints
from tale.story import *
from tests.supportstuff import FakeDriver


def serializecycle(obj):
    ser = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
    return pickle.loads(ser)


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
        self.assertEqual(races.races, o)
        o = base.Item("name", "title", "description")
        o.aliases = ["alias"]
        x = serializecycle(o)
        self.assert_base_attrs(x)
        self.assertEqual(["alias"], x.aliases)

    def test_items_and_container(self):
        o = base.Item("name", "title", "description")
        o.aliases = ["alias"]
        bag = base.Container("name", "title", "description")
        bag.insert(o, None)
        x = serializecycle(bag)
        self.assert_base_attrs(x)
        self.assertEqual(1, x.inventory_size)
        y = list(x.inventory)[0]
        self.assertEqual(x, y.contained_in)
        o = base.Weapon("w")
        x = serializecycle(o)
        self.assertEqual("w", x.name)
        o = base.Armour("a")
        x = serializecycle(o)
        self.assertEqual("a", x.name)

    def test_location(self):
        room = base.Location("room", "description")
        x = serializecycle(room)
        self.assertEqual("room", x.name)
        self.assertEqual(set(), x.livings)
        self.assertEqual(set(), x.items)
        # now add some exits and a second location, and try again
        room2 = base.Location("room2", "description")
        exit1 = base.Exit("room2", room2, "to room2")
        exit2 = base.Exit("room", room, "back to room")
        room.add_exits([exit1])
        room2.add_exits([exit2])
        [r1, r2] = serializecycle([room, room2])
        self.assertEqual("room", r1.name)
        self.assertEqual("room2", r2.name)
        self.assertEqual(1, len(r1.exits))
        self.assertEqual(1, len(r2.exits))
        exit1 = r1.exits["room2"]
        exit2 = r2.exits["room"]
        self.assertEqual("to room2", exit1.short_description)
        self.assertEqual("back to room", exit2.short_description)
        self.assertEqual(r2, exit1.target)
        self.assertEqual(r1, exit2.target)

    def test_exits_and_doors(self):
        o = base.Exit("east", "target", "somewhere")
        x = serializecycle(o)
        self.assertIsNone(x.target)
        self.assertEqual("target", x._target_str)
        self.assertEqual("somewhere", x.short_description)
        self.assertEqual("east", x.name)
        o = base.Door("east", "target", "somewhere", locked=True, opened=False)
        self.assertEqual("somewhere It is closed and locked.", o.description)
        x = serializecycle(o)
        self.assertIsNone(x.target)
        self.assertEqual("target", x._target_str)
        self.assertEqual("east", x.name)
        self.assertEqual("somewhere It is closed and locked.", x.description)

    def test_npc(self):
        o = base.Living("name", "n", title="title", description="description", race="dragon")
        x = serializecycle(o)
        self.assert_base_attrs(x)
        self.assertFalse(x.aggressive)

    def test_player_and_soul(self):
        o = base.Soul()
        x = serializecycle(o)
        self.assertIsNotNone(x)
        p = player.Player("name", "n", description="description")
        p.title = "title"
        p.money = 42
        x = serializecycle(p)
        self.assert_base_attrs(x)
        self.assertEqual(42, x.money)

    def test_storyconfig(self):
        s = StoryBase()
        s.server_mode = GameMode.IF
        s.display_gametime = True
        s.name = "test"
        x = serializecycle(s)
        self.assertEqual(s.__dict__, x.__dict__)
        x = serializecycle(s.config)
        self.assertEqual(s.config, x)

    def test_Context(self):
        c = util.Context(driver=mud_context.driver, clock=mud_context.driver.game_clock, config=mud_context.config, player_connection=42)
        with self.assertRaises(RuntimeError) as x:
            serializecycle(c)
        self.assertEqual("cannot serialize context", str(x.exception))

    def test_Hints(self):
        h = hints.HintSystem()
        h.init([hints.Hint("start", None, "first")])
        x = serializecycle(h)
        self.assertEqual(h.all_hints, x.all_hints)


if __name__ == '__main__':
    unittest.main()
