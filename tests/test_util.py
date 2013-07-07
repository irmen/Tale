"""
Unit tests for util functions

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import datetime
import unittest
from tale import util, globalcontext
from tale.errors import ParseError
from tale.base import Item, Container, Location, Exit
from tale.player import Player
from tale.io.vfs import VirtualFileSystem, VfsError
from tests.supportstuff import DummyDriver, Wiretap


class TestUtil(unittest.TestCase):
    def setUp(self):
        globalcontext.mud_context.driver = DummyDriver()

    def test_print_location(self):
        p = Player("julie", "f")
        key = Item("key")
        bag = Container("bag")
        room = Location("room")
        bag.insert(key, p)
        p.insert(bag, p)
        room.insert(p, p)
        with self.assertRaises(Exception):
            util.print_object_location(p, None, None)
        util.print_object_location(p, key, None)
        self.assertEqual(["(It's not clear where key is).\n"], p.get_output_paragraphs_raw())
        util.print_object_location(p, key, None, print_parentheses=False)
        self.assertEqual(["It's not clear where key is.\n"], p.get_output_paragraphs_raw())
        util.print_object_location(p, key, bag)
        result = "".join(p.get_output_paragraphs_raw())
        self.assertTrue("in bag" in result and "in your inventory" in result)
        util.print_object_location(p, key, room)
        self.assertTrue("in your current location" in "".join(p.get_output_paragraphs_raw()))
        util.print_object_location(p, bag, p)
        self.assertTrue("in your inventory" in "".join(p.get_output_paragraphs_raw()))
        util.print_object_location(p, p, room)
        self.assertTrue("in your current location" in "".join(p.get_output_paragraphs_raw()))

    def test_moneydisplay(self):
        # fantasy
        mf = util.MoneyFormatter("fantasy")
        self.assertEqual("nothing", mf.display(0))
        self.assertEqual("zilch", mf.display(0, zero_msg="zilch"))
        self.assertEqual("nothing", mf.display(0.01))
        self.assertEqual("1 copper", mf.display(0.06))
        self.assertEqual("12 gold, 3 silver, and 2 copper", mf.display(123.24))
        self.assertEqual("12 gold, 3 silver, and 3 copper", mf.display(123.26))
        self.assertEqual("0g/0s/0c", mf.display(0, True))
        self.assertEqual("12g/3s/2c", mf.display(123.24, True))
        self.assertEqual("12g/3s/3c", mf.display(123.26, True))
        # modern
        mf = util.MoneyFormatter("modern")
        self.assertEqual("nothing", mf.display(0))
        self.assertEqual("zilch", mf.display(0, zero_msg="zilch"))
        self.assertEqual("nothing", mf.display(0.001))
        self.assertEqual("1 cent", mf.display(0.006))
        self.assertEqual("5 cent", mf.display(0.05))
        self.assertEqual("123 dollar and 24 cent", mf.display(123.244))
        self.assertEqual("123 dollar and 25 cent", mf.display(123.246))
        self.assertEqual("$ 0.00", mf.display(0, True))
        self.assertEqual("$ 123.24", mf.display(123.244, True))
        self.assertEqual("$ 123.25", mf.display(123.246, True))

    def test_money_to_float(self):
        with self.assertRaises(ValueError):
            util.MoneyFormatter("bubblewrap")
        # fantasy
        mf = util.MoneyFormatter("fantasy")
        self.assertEqual(0.0, mf.money_to_float({}))
        self.assertAlmostEqual(0.3, mf.money_to_float({"copper": 1.0, "coppers": 2.0}), places=4)
        self.assertAlmostEqual(325.6, mf.money_to_float({"gold": 22.5, "silver": 100.2, "copper": 4}), places=4)
        self.assertAlmostEqual(289.3, mf.money_to_float("22g/66s/33c"), places=4)
        # modern
        mf = util.MoneyFormatter("modern")
        self.assertEqual(0.0, mf.money_to_float({}))
        self.assertAlmostEqual(0.55, mf.money_to_float({"cent": 22, "cents": 33}), places=4)
        self.assertAlmostEqual(55.0, mf.money_to_float({"dollar": 22, "dollars": 33}), places=4)
        self.assertAlmostEqual(5.42, mf.money_to_float({"dollar": 5, "cent": 42}), places=4)
        self.assertAlmostEqual(3.45, mf.money_to_float("$3.45"), places=4)
        self.assertAlmostEqual(3.45, mf.money_to_float("$  3.45"), places=4)

    def test_words_to_money(self):
        # fantasy
        mf = util.MoneyFormatter("fantasy")
        with self.assertRaises(ParseError):
            mf.parse([])
        with self.assertRaises(ParseError):
            mf.parse(["44"])
        with self.assertRaises(ParseError):
            mf.parse(["44g/s"])
        with self.assertRaises(ParseError):
            mf.parse(["gold"])
        self.assertAlmostEqual(451.6, mf.parse(["44", "gold", "5", "silver", "66", "copper"]), places=4)
        self.assertAlmostEqual(451.6, mf.parse(["44g/5s/66c"]), places=4)
        # modern
        mf = util.MoneyFormatter("modern")
        with self.assertRaises(ParseError):
            mf.parse([])
        with self.assertRaises(ParseError):
            mf.parse(["44"])
        with self.assertRaises(ParseError):
            mf.parse(["$xxx"])
        with self.assertRaises(ParseError):
            mf.parse(["dollar"])
        self.assertAlmostEqual(46.15, mf.parse(["44", "dollar", "215", "cent"]), places=4)
        self.assertAlmostEqual(46.15, mf.parse(["$46.15"]), places=4)
        self.assertAlmostEqual(46.15, mf.parse(["$ 46.15"]), places=4)
        self.assertAlmostEqual(46.15, mf.parse(["$", "46.15"]), places=4)

    def test_roll_die(self):
        total, values = util.roll_die()
        self.assertTrue(1 <= total <= 6)
        self.assertEqual(1, len(values))
        self.assertEqual(total, values[0])
        total, values = util.roll_die(20, 10)   # 20d10
        self.assertEqual(20, len(values))
        with self.assertRaises(AssertionError):
            util.roll_die(21, 10)

    def test_parse_duration(self):
        duration = util.parse_duration(["1", "hour", "1", "minute", "1", "second"])
        self.assertEqual(datetime.timedelta(hours=1, minutes=1, seconds=1), duration)
        duration = util.parse_duration(["3", "hours", "2", "minutes", "5", "seconds"])
        self.assertEqual(datetime.timedelta(hours=3, minutes=2, seconds=5), duration)
        duration = util.parse_duration(["3", "h", "2", "min", "5", "sec"])
        self.assertEqual(datetime.timedelta(hours=3, minutes=2, seconds=5), duration)
        duration = util.parse_duration(["3", "h", "2", "m", "5", "s"])
        self.assertEqual(datetime.timedelta(hours=3, minutes=2, seconds=5), duration)
        duration = util.parse_duration(["3h", "2m", "5s"])
        self.assertEqual(datetime.timedelta(hours=3, minutes=2, seconds=5), duration)
        duration = util.parse_duration(["2.5", "min"])
        self.assertEqual(datetime.timedelta(minutes=2, seconds=30), duration)
        with self.assertRaises(ParseError):
            util.parse_duration(None)
        with self.assertRaises(ParseError):
            util.parse_duration(["1", "2", "3"])
        with self.assertRaises(ParseError):
            util.parse_duration(["1", "apple"])
        with self.assertRaises(ParseError):
            util.parse_duration(["seconds", "2"])

    def test_duration_display(self):
        self.assertEqual("no time at all", util.duration_display(datetime.timedelta(0)))
        self.assertEqual("1 hour, 1 minute, and 1 second", util.duration_display(datetime.timedelta(hours=1, minutes=1, seconds=1)))
        self.assertEqual("2 hours, 3 minutes, and 4 seconds", util.duration_display(datetime.timedelta(hours=2, minutes=3, seconds=4)))
        self.assertEqual("2 minutes", util.duration_display(datetime.timedelta(minutes=2)))
        self.assertEqual("2 minutes and 1 second", util.duration_display(datetime.timedelta(minutes=2, seconds=1)))

    def test_message_nearby_location(self):
        plaza = Location("plaza")
        road = Location("road")
        house = Location("house")
        attic = Location("attic")
        plaza.add_exits([Exit("north", road, "road leads north"), Exit("door", house, "door to a house")])
        road.add_exits([Exit("south", plaza, "plaza to the south")])
        house.add_exits([Exit("door", plaza, "door to the plaza"), Exit("ladder", attic, "dusty attic")])
        attic.add_exits([Exit("ladder", house, "the house")])
        wiretap_plaza = Wiretap(plaza)
        wiretap_road = Wiretap(road)
        wiretap_house = Wiretap(house)
        wiretap_attic = Wiretap(attic)
        util.message_nearby_locations(plaza, "boing")
        self.assertEqual([], wiretap_plaza.msgs, "the plaza doesnt receive tells")
        self.assertEqual([], wiretap_attic.msgs, "the attic is too far away to receive msgs")
        self.assertTrue(("road", "boing") in wiretap_road.msgs)
        self.assertTrue(("road", "The sound is coming from the south.") in wiretap_road.msgs, "road should give sound direction")
        self.assertTrue(("house", "boing") in wiretap_house.msgs)
        self.assertTrue(("house", "You can't hear where the sound is coming from.") in wiretap_house.msgs, "in the house you can't locate the sound direction")

    def test_formatdocstring(self):
        d = "hai"
        self.assertEqual("hai", util.format_docstring(d))
        d = """first
        second
        third

        """
        self.assertEqual("first\nsecond\nthird", util.format_docstring(d))
        d = """
        first
          second
            third
        """
        self.assertEqual("first\n  second\n    third", util.format_docstring(d))

    def test_vfs_load(self):
        vfs = VirtualFileSystem(util)
        with self.assertRaises(VfsError):
            vfs.load_text("a\\b")
        with self.assertRaises(VfsError):
            vfs.load_text("/abs/path")
        with self.assertRaises(IOError):
            vfs.load_text("normal/text")
        with self.assertRaises(IOError):
            vfs.load_image("normal/image")
        vfs = VirtualFileSystem("/var/temp")
        with self.assertRaises(IOError):
            vfs.load_text("test_doesnt_exist_999.txt")

    def test_vfs_storage(self):
        vfs = VirtualFileSystem(util)
        with vfs.open_write("unittest.txt") as f:
            f.write("test")
        with self.assertRaises(IOError):
            vfs.load_from_storage("test_doesnt_exist_999.txt")
        vfs.write_to_storage("unittest.txt", b"Test1\nTest2\n")
        self.assertEqual(b"Test1\nTest2\n", vfs.load_from_storage("unittest.txt"))
        vfs.delete_storage("unittest.txt")

    def test_clone(self):
        item = Item("thing", "description")
        item.aliases = ["a1", "a2"]
        item2 = util.clone(item)
        self.assertNotEqual(item, item2)
        item2.aliases.append("a3")
        self.assertNotEqual(item.aliases, item2.aliases)
        player = Player("julie", "f")
        player.insert(item, player)
        player2 = util.clone(player)
        player2.insert(item2, player2)
        self.assertNotEqual(player.inventory_size, player2.inventory_size)
        self.assertNotEqual(player.inventory, player2.inventory)
        self.assertTrue(item in player)
        self.assertFalse(item in player2)

    def test_gametime_realtime(self):
        epoch = datetime.datetime(2012, 4, 19, 14, 0, 0)
        gt = util.GameDateTime(epoch)  # realtime=1
        self.assertEqual(1, gt.times_realtime)
        self.assertEqual(epoch, gt.clock)
        # test realtime plus/minus
        gt2 = gt.plus_realtime(datetime.timedelta(minutes=2, seconds=30))
        self.assertNotEqual(gt2, gt.clock)
        self.assertEqual(datetime.datetime(2012, 4, 19, 14, 2, 30), gt2)
        gt2 = gt.minus_realtime(datetime.timedelta(minutes=2, seconds=30))
        self.assertEqual(datetime.datetime(2012, 4, 19, 13, 57, 30), gt2)
        # test realtime add/sub
        gt.add_realtime(datetime.timedelta(minutes=2, seconds=30))
        self.assertEqual(datetime.datetime(2012, 4, 19, 14, 2, 30), gt.clock)
        gt.sub_realtime(datetime.timedelta(minutes=2, seconds=30))
        self.assertEqual(epoch, gt.clock)
        # test gametime add/sub
        gt.add_gametime(datetime.timedelta(minutes=2, seconds=30))
        self.assertEqual(datetime.datetime(2012, 4, 19, 14, 2, 30), gt.clock)
        gt.sub_gametime(datetime.timedelta(minutes=2, seconds=30))
        self.assertEqual(epoch, gt.clock)

    def test_gametime_notrealtime(self):
        epoch = datetime.datetime(2012, 4, 19, 14, 0, 0)
        gt = util.GameDateTime(epoch, times_realtime=5)  # not realtime, 5 times as fast
        self.assertEqual(5, gt.times_realtime)
        self.assertEqual(epoch, gt.clock)
        # test realtime plus/minus (so in game-time, it should be 5 times faster)
        gt2 = gt.plus_realtime(datetime.timedelta(minutes=2, seconds=30))
        self.assertNotEqual(gt2, gt.clock)
        self.assertEqual(datetime.datetime(2012, 4, 19, 14, 12, 30), gt2)
        gt2 = gt.minus_realtime(datetime.timedelta(minutes=2, seconds=30))
        self.assertEqual(datetime.datetime(2012, 4, 19, 13, 47, 30), gt2)
        # test realtime add/sub (so in game-time, it should be 5 times faster)
        gt.add_realtime(datetime.timedelta(minutes=2, seconds=30))
        self.assertEqual(datetime.datetime(2012, 4, 19, 14, 12, 30), gt.clock)
        gt.sub_realtime(datetime.timedelta(minutes=2, seconds=30))
        self.assertEqual(epoch, gt.clock)
        # test gametime add/sub (directly manipulates the -ingame- clock, so no surprises here)
        gt.add_gametime(datetime.timedelta(minutes=2, seconds=30))
        self.assertEqual(datetime.datetime(2012, 4, 19, 14, 2, 30), gt.clock)
        gt.sub_gametime(datetime.timedelta(minutes=2, seconds=30))
        self.assertEqual(epoch, gt.clock)

    def test_parsetime(self):
        self.assertEqual(datetime.time(hour=13, minute=22, second=58), util.parse_time(["13:22:58"]))
        self.assertEqual(datetime.time(hour=13, minute=22, second=58), util.parse_time(["13:22:58"]))
        self.assertEqual(datetime.time(hour=13, minute=22, second=0), util.parse_time(["13:22"]))
        time = util.parse_time(["3", "h", "2", "m", "5", "s"])
        self.assertEqual(datetime.time(hour=3, minute=2, second=5), time)
        self.assertEqual(datetime.time(hour=0), util.parse_time(["midnight"]))
        self.assertEqual(datetime.time(hour=12), util.parse_time(["noon"]))
        util.parse_time(["sunrise"])
        util.parse_time(["sunset"])
        with self.assertRaises(ParseError):
            util.parse_time(None)
        with self.assertRaises(ParseError):
            util.parse_time([])
        with self.assertRaises(ParseError):
            util.parse_time(["some_weird_occasion"])

    def test_attrdict(self):
        ad = util.AttrDict(a=42, b="hello")
        self.assertEqual([42, 42], [ad.a, ad["a"]])
        self.assertEqual(["hello", "hello"], [ad.b, ad["b"]])
        ad.a = 999
        ad["b"] = "bye"
        self.assertEqual(999, ad.a)
        self.assertEqual("bye", ad.b)
        d = {"a": 1, "b": 2}
        ad = util.AttrDict(d)
        self.assertEqual([1, 2], [ad.a, ad.b])

    def test_context(self):
        ctx = util.Context(driver=1, clock=2)
        self.assertEqual(1, ctx.driver)
        self.assertEqual(2, ctx.clock)
        self.assertEqual(1, ctx["driver"])
        self.assertEqual(2, ctx["clock"])
        self.assertIsNone(ctx.state)
        self.assertIsNone(ctx.config)
        with self.assertRaises(AttributeError):
            _ = ctx.doesnotexist


if __name__ == '__main__':
    unittest.main()
