"""
Unit tests for serialization

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import unittest
import pickle
import datetime
from mudlib import globals, races, base, npc, soul, player

class DummyDriver(object):
    heartbeats = set()
    exits = []
    game_clock = datetime.datetime.now()
    def register_heartbeat(self, obj):
        self.heartbeats.add(obj)
    def unregister_heartbeat(self, obj):
        self.heartbeats.discard(obj)
    def register_exit(self, exit):
        self.exits.append(exit)
    def defer(self, due, owner, callable, *vargs, **kwargs):
        pass

globals.mud_context.driver = DummyDriver()

def serializecycle(obj):
    ser=pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
    return pickle.loads(ser)


class TestSerializing(unittest.TestCase):
    def assert_base_attrs(self, obj):
        self.assertEqual("name", obj.name)
        self.assertEqual("title", obj.title)
        self.assertEqual("description", obj.description)
        self.assertEqual("n", obj.gender)

    def test_basic(self):
        o = serializecycle(races.races)
        self.assertEqual(races.races, o)
        o=base.MudObject("name","title","description")
        o.aliases = ["alias"]
        x = serializecycle(o)
        self.assert_base_attrs(x)
        self.assertEqual(["alias"], x.aliases)
    def test_items_and_container(self):
        o=base.Item("name", "title", "description")
        o.aliases = ["alias"]
        bag=base.Container("name", "title", "description")
        bag.insert(o,None)
        x = serializecycle(bag)
        self.assert_base_attrs(x)
        self.assertEqual(1, x.inventory_size())
        y = list(x.inventory())[0]
        self.assertEqual(x, y.contained_in)
        o=base.Weapon("w")
        x=serializecycle(o)
        self.assertEqual("w", x.name)
        o=base.Armour("a")
        x=serializecycle(o)
        self.assertEqual("a", x.name)
    def test_location(self):
        room=base.Location("room", "description")
        x=serializecycle(room)
        self.assertEqual("room", x.name)
        self.assertIsNotNone(x.wiretaps)
        self.assertEqual(set(), x.livings)
        self.assertEqual(set(), x.items)
        # now add some exits and a second location, and try again
        room2=base.Location("room2", "description")
        exit1=base.Exit(room2, "to room2", direction="room2")
        exit2=base.Exit(room, "back to room", direction="room")
        room.add_exits([exit1])
        room2.add_exits([exit2])
        [r1,r2]=serializecycle([room, room2])
        self.assertEqual("room", r1.name)
        self.assertEqual("room2", r2.name)
        self.assertEqual(1, len(r1.exits))
        self.assertEqual(1, len(r2.exits))
        exit1=r1.exits["room2"]
        exit2=r2.exits["room"]
        self.assertEqual("to room2", exit1.short_description)
        self.assertEqual("back to room", exit2.short_description)
        self.assertEqual(r2, exit1.target)
        self.assertEqual(r1, exit2.target)
    def test_exits_and_doors(self):
        o=base.Exit("target", "somewhere", direction="east")
        x=serializecycle(o)
        self.assertFalse(x.bound)
        self.assertEqual("target", x.target)
        self.assertEqual("somewhere", x.short_description)
        self.assertEqual("east", x.direction)
        o=base.Door("target", "somewhere", direction="east", locked=True, opened=False)
        self.assertEqual("somewhere It is closed and locked.", o.long_description)
        x=serializecycle(o)
        self.assertEqual("target", x.target)
        self.assertEqual("somewhere It is closed and locked.", x.long_description)
    def test_living_npc_monster(self):
        o=base.Living("name","n","title", "description", race="dragon")
        x=serializecycle(o)
        self.assert_base_attrs(x)
        o=npc.NPC("name","n","title", "description", race="dragon")
        x=serializecycle(o)
        self.assert_base_attrs(x)
        m=npc.Monster("name","n","title", "description", race="dragon")
        self.assertTrue(m.aggressive)
        x=serializecycle(m)
        self.assert_base_attrs(x)
        self.assertTrue(x.aggressive)
        self.assertIsNotNone(x.wiretaps)
    def test_player_and_soul(self):
        o=soul.Soul()
        x=serializecycle(o)
        self.assertIsNotNone(x)
        p=player.Player("name", "n", description="description")
        p.set_title("title")
        p.money=42
        x=serializecycle(p)
        self.assert_base_attrs(x)
        self.assertEqual(42,x.money)
        self.assertIsNotNone(x.wiretaps)


if __name__ == '__main__':
    unittest.main()
