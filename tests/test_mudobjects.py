"""
Unittests for Mud base objects

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import unittest
from mudlib.baseobjects import Location, Exit, Item, Living, MudObject, _Limbo, Container, Weapon
from mudlib.errors import SecurityViolation
from mudlib.npc import NPC
from mudlib.player import Player


class Wiretap(object):
    def __init__(self):
        self.msgs=[]
    def tell(self, msg):
        self.msgs.append(msg)
    def clear(self):
        self.msgs=[]


class TestLocations(unittest.TestCase):
    def setUp(self):
        self.hall = Location("Main hall", "A very large hall.")
        self.attic = Location("Attic", "A dark attic.")
        self.street = Location("Street", "An endless street.")
        self.hall.exits["up"] = Exit(self.attic, "A ladder leads up.")
        self.hall.exits["door"] = Exit(self.street, "A heavy wooden door to the east blocks the noises from the street outside.")
        self.hall.exits["east"] = self.hall.exits["door"]
        self.table = Item("table", "oak table", "a large dark table with a lot of cracks in its surface")
        self.key = Item("key", "rusty key", "an old rusty key without a label")
        self.magazine =Item ("magazine", "university magazine")
        self.hall.enter(self.table)
        self.hall.enter(self.key)
        self.hall.enter(self.magazine)
        self.rat = NPC("rat", "n", race="rodent")
        self.julie = NPC("julie", "f", "attractive Julie",
                     """
                     She's quite the looker.
                     """)
        self.player = Player("player","m")
        self.pencil = Item("pencil")
        self.bag = Container("bag")
        self.notebook_in_bag = Item("notebook")
        self.bag.inventory.add(self.notebook_in_bag)
        self.player.inventory.add(self.pencil)
        self.player.inventory.add(self.bag)
        self.hall.enter(self.rat)
        self.hall.enter(self.julie)
        self.hall.enter(self.player)

    def test_contains(self):
        self.assertTrue(self.julie in self.hall)
        self.assertTrue(self.magazine in self.hall)
        self.assertFalse(self.pencil in self.hall)
        self.assertFalse(self.magazine in self.attic)
        self.assertFalse(self.julie in self.attic)

    def test_look(self):
        expected = """[Main hall]
A very large hall.
A heavy wooden door to the east blocks the noises from the street outside.
A ladder leads up.
You see an oak table, a rusty key, and a university magazine.
Player, attractive Julie, and rat are here."""
        self.assertEqual(expected, self.hall.look())
        expected = """[Main hall]
A very large hall.
A heavy wooden door to the east blocks the noises from the street outside.
A ladder leads up.
You see an oak table, a rusty key, and a university magazine.
Attractive Julie and rat are here."""
        self.assertEqual(expected, self.hall.look(exclude_living=self.player))
        expected = """[Attic]
A dark attic."""
        self.assertEqual(expected, self.attic.look())

    def test_look_short(self):
        expected = """[Attic]"""
        self.assertEqual(expected, self.attic.look(short=True))
        expected = """[Main hall]
Exits: door, east, up
You see: key, magazine, table
Present: julie, player, rat"""
        self.assertEqual(expected, self.hall.look(short=True))
        expected = """[Main hall]
Exits: door, east, up
You see: key, magazine, table
Present: julie, rat"""
        self.assertEqual(expected, self.hall.look(exclude_living=self.player, short=True))

    def test_search_living(self):
        self.assertEqual(None, self.hall.search_living("<notexisting>"))
        self.assertEqual(None, self.attic.search_living("<notexisting>"))
        self.assertEqual(self.rat, self.hall.search_living("rat"))
        self.assertEqual(self.julie, self.hall.search_living("Julie"))
        self.assertEqual(self.julie, self.hall.search_living("attractive julie"))

    def test_search_item(self):
        # almost identical to locate_item so only do a few basic tests
        self.assertEqual(None, self.player.search_item("<notexisting>"))
        self.assertEqual(self.pencil, self.player.search_item("pencil"))

    def test_locate_item(self):
        item, container = self.player.locate_item("<notexisting>")
        self.assertEqual(None, item)
        self.assertEqual(None, container)
        item, container = self.player.locate_item("pencil")
        self.assertEqual(self.pencil, item)
        self.assertEqual(self.player, container)
        item, container = self.player.locate_item("pencil", include_inventory=False)
        self.assertEqual(None, item)
        self.assertEqual(None, container)
        item, container = self.player.locate_item("key")
        self.assertEqual(self.key, item)
        self.assertEqual(self.hall, container)
        item, container = self.player.locate_item("key", include_location=False)
        self.assertEqual(None, item)
        self.assertEqual(None, container)
        item, container = self.player.locate_item("KEY")
        self.assertEqual(self.key, item, "should work case-insensitive")
        self.assertEqual(self.hall, container, "should work case-insensitive")
        item, container = self.player.locate_item("notebook")
        self.assertEqual(self.notebook_in_bag, item)
        self.assertEqual(self.bag, container, "should search in bags in inventory")
        item, container = self.player.locate_item("notebook", include_containers_in_inventory=False)
        self.assertEqual(None, item)
        self.assertEqual(None, container, "should not search in bags in inventory")

    def test_tell(self):
        class MsgTraceNPC(NPC):
            def __init__(self, name, gender, race):
                super(MsgTraceNPC, self).__init__(name, gender, race=race)
                self.clearmessages()
            def clearmessages(self):
                self.messages = []
            def tell(self, *messages):
                self.messages.extend(messages)
        rat = MsgTraceNPC("rat", "n", "rodent")
        julie = MsgTraceNPC("julie", "f", "human")
        hall = Location("hall")
        hall.livings = [rat, julie]
        hall.tell("roommsg")
        self.assertEqual(["roommsg"], rat.messages)
        self.assertEqual(["roommsg"], julie.messages)
        rat.clearmessages()
        julie.clearmessages()
        hall.tell("roommsg", rat, [julie], "juliemsg")
        self.assertEqual([], rat.messages)
        self.assertEqual(["juliemsg"], julie.messages)

    def test_enter_leave(self):
        hall = Location("hall")
        rat1 = NPC("rat1", "n")
        rat2 = NPC("rat2", "n")
        with self.assertRaises(TypeError):
            hall.enter(12345)
        self.assertEqual(_Limbo, rat1.location)
        self.assertFalse(rat1 in hall.livings)
        wiretap = Wiretap()
        hall.wiretaps.add(wiretap)
        hall.enter(rat1)
        self.assertEqual(hall, rat1.location)
        self.assertTrue(rat1 in hall.livings)
        self.assertEqual(["Rat1 arrives."], wiretap.msgs)
        hall.enter(rat2, force_and_silent=True)
        self.assertTrue(rat2 in hall.livings)
        self.assertEqual(["Rat1 arrives."], wiretap.msgs, "2nd rat should not be mentioned")
        # now test leave
        wiretap.clear()
        hall.leave(rat1)
        self.assertFalse(rat1 in hall.livings)
        self.assertIsNone(rat1.location)
        self.assertEqual(["Rat1 leaves."], wiretap.msgs)
        hall.leave(rat2, force_and_silent=True)
        self.assertFalse(rat2 in hall.livings)
        self.assertEqual(["Rat1 leaves."], wiretap.msgs, "2nd rat should not be mentioned")
        # test random leave
        hall.leave(rat1)
        hall.leave(12345)

    def test_move(self):
        hall = Location("hall")
        attic = Location("attic")
        rat = Living("rat", "n")
        hall.enter(rat)
        wiretap_hall = Wiretap()
        wiretap_attic = Wiretap()
        hall.wiretaps.add(wiretap_hall)
        attic.wiretaps.add(wiretap_attic)
        self.assertTrue(rat in hall.livings)
        self.assertFalse(rat in attic.livings)
        self.assertEqual(hall, rat.location)
        rat.move(attic)
        self.assertTrue(rat in attic.livings)
        self.assertFalse(rat in hall.livings)
        self.assertEqual(attic, rat.location)
        self.assertEqual(["Rat leaves."], wiretap_hall.msgs)
        self.assertEqual(["Rat arrives."], wiretap_attic.msgs)
        # now try silent
        wiretap_attic.clear()
        wiretap_hall.clear()
        rat.move(hall, force_and_silent=True)
        self.assertTrue(rat in hall.livings)
        self.assertFalse(rat in attic.livings)
        self.assertEqual(hall, rat.location)
        self.assertEqual([], wiretap_hall.msgs)
        self.assertEqual([], wiretap_attic.msgs)


class TestLiving(unittest.TestCase):
    def test_contains(self):
        orc = Living("orc", "m")
        axe = Weapon("axe")
        orc.inventory.add(axe)
        self.assertTrue(axe in orc)


class TestNPC(unittest.TestCase):
    def test_init(self):
        rat = NPC("rat", "n", race="rodent")
        julie = NPC("julie", "f", "attractive Julie",
                    """
                    She's quite the looker.
                    """)
        self.assertEqual("julie", julie.name)
        self.assertEqual("attractive Julie", julie.title)
        self.assertEqual("She's quite the looker.", julie.description)
        self.assertEqual("human", julie.race)
        self.assertEqual("f", julie.gender)
        self.assertTrue(1 < julie.stats["agi"] < 100)
        self.assertEqual("rat", rat.name)
        self.assertEqual("rat", rat.title)
        self.assertEqual("rodent", rat.race)
        self.assertEqual("", rat.description)
        self.assertEqual("n", rat.gender)
        self.assertTrue(1 < rat.stats["agi"] < 100)


class TestPlayer(unittest.TestCase):
    def test_init(self):
        player = Player("fritz", "m")
        player.set_title("%s the great", includes_name_param=True)
        self.assertEqual("fritz", player.name)
        self.assertEqual("Fritz the great", player.title)
        self.assertEqual("", player.description)
        self.assertEqual("human", player.race)
        self.assertEqual("m", player.gender)
        self.assertEqual(set(), player.privileges)
        self.assertTrue(1 < player.stats["agi"] < 100)
    def test_tell(self):
        player = Player("fritz", "m")
        player.tell("line1")
        player.tell("line2")
        player.tell("ints", 42, 999)
        self.assertEqual("line1\nline2\nints 42 999\n", "".join(player.get_output_lines()))
        self.assertEqual([], player.get_output_lines())
    def test_look(self):
        player = Player("fritz", "m")
        attic = Location("Attic", "A dark attic.")
        self.assertEqual("[Limbo]\nThe intermediate or transitional place or state. There's only nothingness.\nLivings end up here if they're not inside a proper location yet.", player.look())
        player.move(attic)
        self.assertEqual("[Attic]", player.look(short=True))
        julie = NPC("julie", "f")
        julie.move(attic)
        self.assertEqual("[Attic]\nPresent: julie", player.look(short=True))
    def test_wiretap(self):
        attic = Location("Attic", "A dark attic.")
        player = Player("fritz", "m")
        julie = NPC("julie", "f")
        julie.move(attic)
        player.move(attic)
        julie.tell("message for julie")
        attic.tell("message for room")
        self.assertEqual("message for room\n", "".join(player.get_output_lines()))
        with self.assertRaises(SecurityViolation):
            player.create_wiretap(julie)
        player.privileges = {"wizard"}
        player.create_wiretap(julie)
        player.create_wiretap(attic)
        julie.tell("message for julie")
        attic.tell("message for room")
        self.assertEqual(["\n","\n","\n","\n",
            "[wiretap on 'Attic': message for room]","[wiretap on 'julie': message for julie]",
            "[wiretap on 'julie': message for room]","message for room"], sorted(player.get_output_lines()))
        # test removing the wiretaps
        player.installed_wiretaps.clear()
        julie.tell("message for julie")
        attic.tell("message for room")
        self.assertEqual("message for room\n", "".join(player.get_output_lines()))


class TestDescriptions(unittest.TestCase):
    def test_name(self):
        item = Item("key")
        self.assertEqual("key", item.name)
        self.assertEqual("key", item.title)
        self.assertEqual("", item.description)
    def test_title(self):
        item = Item("key", "rusty old key")
        self.assertEqual("key", item.name)
        self.assertEqual("rusty old key", item.title)
        self.assertEqual("", item.description)
    def test_description(self):
        item = Item("key", "rusty old key", "a small old key that's rusted")
        self.assertEqual("key", item.name)
        self.assertEqual("rusty old key", item.title)
        self.assertEqual("a small old key that's rusted", item.description)
        item = Item("key", "rusty old key",
                    """
                    a very small, old key that's rusted
                    """)
        self.assertEqual("key", item.name)
        self.assertEqual("rusty old key", item.title)
        self.assertEqual("a very small, old key that's rusted", item.description)


class TestDestroy(unittest.TestCase):
    def test_destroy_base(self):
        ctx = {}
        o = MudObject("x")
        o.destroy(ctx)
    def test_destroy_loc(self):
        ctx = {}
        loc = Location("loc")
        i = Item("item")
        liv = Living("rat","n")
        loc.enter(i)
        loc.enter(liv)
        loc.exits={"north": Exit("somehwere", "somewhere")}
        player = Player("julie","f")
        player.privileges = {"wizard"}
        player.create_wiretap(loc)
        loc.enter(player)
        self.assertTrue(len(loc.exits)>0)
        self.assertTrue(len(loc.items)>0)
        self.assertTrue(len(loc.livings)>0)
        self.assertTrue(len(loc.wiretaps)>0)
        self.assertEqual(loc, player.location)
        self.assertEqual(loc, liv.location)
        self.assertTrue(len(player.installed_wiretaps)>0)
        loc.destroy(ctx)
        self.assertTrue(len(loc.exits)==0)
        self.assertTrue(len(loc.items)==0)
        self.assertTrue(len(loc.livings)==0)
        self.assertTrue(len(loc.wiretaps)==0)
        self.assertTrue(len(player.installed_wiretaps)>0, "wiretap object must remain on player")
        self.assertEqual(_Limbo, player.location)
        self.assertEqual(_Limbo, liv.location)

    def test_destroy_player(self):
        ctx = {}
        loc = Location("loc")
        player = Player("julie","f")
        player.privileges = {"wizard"}
        player.create_wiretap(loc)
        player.inventory.add(Item("key"))
        loc.enter(player)
        self.assertTrue(len(loc.wiretaps)>0)
        self.assertEqual(loc, player.location)
        self.assertTrue(len(player.installed_wiretaps)>0)
        self.assertTrue(len(player.inventory)>0)
        self.assertTrue(player in loc.livings)
        player.destroy(ctx)
        self.assertTrue(len(loc.wiretaps)==0)
        self.assertTrue(len(player.installed_wiretaps)==0)
        self.assertTrue(len(player.inventory)==0)
        self.assertFalse(player in loc.livings)
        self.assertIsNone(player.location, "destroyed player should end up nowhere (None)")


class TestContainer(unittest.TestCase):
    def test_container_contains(self):
        bag = Container("bag")
        key = Item("key")
        self.assertTrue(len(bag.inventory)==0)
        npc = NPC("julie","f")
        bag.accept(key, npc)
        bag.inventory.add(key)
        self.assertTrue(key in bag)


if __name__ == '__main__':
    unittest.main()
