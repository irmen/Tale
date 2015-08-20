"""
Unit tests for util functions

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import datetime
import unittest
from tale import util, mud_context, pubsub
from tale.errors import ParseError, ActionRefused
from tale.base import Item, Container, Location, Exit
from tale.player import Player
from tale.tio.vfs import VirtualFileSystem, VfsError
from tests.supportstuff import TestDriver, Wiretap


class TestUtil(unittest.TestCase):
    def setUp(self):
        mud_context.driver = TestDriver()

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
        self.assertEqual(["(It's not clear where key is).\n"], p.test_get_output_paragraphs())
        util.print_object_location(p, key, None, print_parentheses=False)
        self.assertEqual(["It's not clear where key is.\n"], p.test_get_output_paragraphs())
        util.print_object_location(p, key, bag)
        result = "".join(p.test_get_output_paragraphs())
        self.assertTrue("in bag" in result and "in your inventory" in result)
        util.print_object_location(p, key, room)
        self.assertTrue("in your current location" in "".join(p.test_get_output_paragraphs()))
        util.print_object_location(p, bag, p)
        self.assertTrue("in your inventory" in "".join(p.test_get_output_paragraphs()))
        util.print_object_location(p, p, room)
        self.assertTrue("in your current location" in "".join(p.test_get_output_paragraphs()))

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
        self.assertEqual("5 cents", mf.display(0.05))
        self.assertEqual("1 dollar and 1 cent", mf.display(1.01))
        self.assertEqual("123 dollars and 24 cents", mf.display(123.244))
        self.assertEqual("123 dollars and 25 cents", mf.display(123.246))
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

    def test_roll_dice(self):
        total, values = util.roll_dice()
        self.assertTrue(1 <= total <= 6)
        self.assertEqual(1, len(values))
        self.assertEqual(total, values[0])
        total, values = util.roll_dice(20, 10)   # 20d10
        self.assertEqual(20, len(values))
        with self.assertRaises(AssertionError):
            util.roll_dice(0, 10)
        with self.assertRaises(AssertionError):
            util.roll_dice(400, 10)

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

    def test_vfs_load_and_names(self):
        vfs = VirtualFileSystem(root_package="os")
        with self.assertRaises(VfsError):
            _ = vfs["a\\b"]
        with self.assertRaises(VfsError):
            _ = vfs["/abs/path"]
        with self.assertRaises(IOError):
            _ = vfs["normal/text"]
        with self.assertRaises(IOError):
            _ = vfs["normal/image"]
        vfs = VirtualFileSystem(root_path=".")
        with self.assertRaises(IOError):
            _ = vfs["test_doesnt_exist_999.txt"]
        with self.assertRaises(VfsError):
            _ = VirtualFileSystem(root_path="@@@does/not/exist.foo@@@")
        with self.assertRaises(VfsError):
            _ = VirtualFileSystem(root_package="non.existing.package.name")
        with self.assertRaises(VfsError):
            _ = VirtualFileSystem(root_package="non_existing_package_name")

    def test_vfs_validate_path(self):
        vfs = VirtualFileSystem(root_path=".")
        vfs.validate_path(".")
        vfs.validate_path("./foo")
        vfs.validate_path("./foo/bar")
        vfs.validate_path(".")
        with self.assertRaises(VfsError):
            vfs.validate_path(r".\wrong\slash")
        with self.assertRaises(VfsError):
            vfs.validate_path(r"/absolute/not/allowed")
        with self.assertRaises(VfsError):
            vfs.validate_path(r"./foo/../../../../../rootescape/notallowed")

    def test_vfs_storage(self):
        with self.assertRaises(ValueError):
            _ = VirtualFileSystem(root_package="os", readonly=False)
        vfs = VirtualFileSystem(root_path=".", readonly=False)
        with self.assertRaises(IOError):
            _ = vfs["test_doesnt_exist_999.txt"]
        vfs["unittest.txt"] = "Test1\nTest2\n"
        rsc = vfs["unittest.txt"]
        self.assertEqual("Test1\nTest2\n", rsc.data)
        self.assertEqual("text/plain", rsc.mimetype)
        self.assertEqual(12, len(rsc))
        self.assertEqual("unittest.txt", rsc.name)
        vfs["unittest.txt"] = "Test1\nTest2\n"
        rsc = vfs["unittest.txt"]
        self.assertEqual("Test1\nTest2\n", rsc.data)
        vfs["unittest.jpg"] = b"imagedata\nblob"
        rsc = vfs["unittest.jpg"]
        self.assertEqual(b"imagedata\nblob", rsc.data)
        self.assertTrue(rsc.mimetype in ("image/jpeg", "image/pjpeg"))
        self.assertEqual(14, len(rsc))
        self.assertEqual("unittest.jpg", rsc.name)
        vfs["unittest.jpg"] = rsc
        del vfs["unittest.txt"]
        del vfs["unittest.jpg"]

    def test_vfs_readonly(self):
        vfs = VirtualFileSystem(root_path=".")
        with self.assertRaises(VfsError):
            vfs.open_write("test.txt")
        with self.assertRaises(VfsError):
            vfs["test.txt"] = "data"

    def test_vfs_write_stream(self):
        vfs = VirtualFileSystem(root_path=".", readonly=False)
        with vfs.open_write("unittest.txt") as f:
            f.write("test write")
        self.assertEqual("test write", vfs["unittest.txt"].data)
        with vfs.open_write("unittest.txt", append=False) as f:
            f.write("overwritten")
        self.assertEqual("overwritten", vfs["unittest.txt"].data)
        with vfs.open_write("unittest.txt", append=True) as f:
            f.write("appended")
        self.assertEqual("overwrittenappended", vfs["unittest.txt"].data)
        del vfs["unittest.txt"]

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

    def test_context(self):
        ctx = util.Context(driver=1, clock=2, config=None, player_connection=None)
        self.assertEqual(1, ctx.driver)
        self.assertEqual(2, ctx.clock)
        self.assertIsNone(ctx.config)
        with self.assertRaises(AttributeError):
            _ = ctx.doesnotexist
        ctx.x = 99
        self.assertEqual(99, ctx.x)

    def test_storyname(self):
        self.assertEqual("name", util.storyname_to_filename("NaMe"))
        self.assertEqual("story_name_dot", util.storyname_to_filename("story name.dot"))
        self.assertEqual("name", util.storyname_to_filename("name\\/*"))
        self.assertEqual("name", util.storyname_to_filename("name'\""))

    def test_authorized(self):
        with self.assertRaises(SyntaxError):
            @util.authorized("wizard", "god")
            def func_no_actor(args):
                pass

        @util.authorized("wizard", "god")
        def func(args, actor=None):
            pass

        class Actor(object):
            pass
        actor = Actor()
        actor2 = Actor()
        actor2.privileges = {"nobody"}
        actor3 = Actor()
        actor3.privileges = {"wizard", "noob"}
        with self.assertRaises(ActionRefused):
            func(42)
        with self.assertRaises(ActionRefused):
            func(42, actor=actor)
        with self.assertRaises(ActionRefused):
            func(42, actor=actor2)
        func(42, actor=actor3)


if __name__ == '__main__':
    unittest.main()
