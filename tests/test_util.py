"""
Unit tests for util functions

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import datetime
import unittest
from mudlib import util
from mudlib.errors import ParseError
from mudlib.base import Item, Container, Location
from mudlib.player import Player

class TestUtil(unittest.TestCase):
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
        self.assertEqual("(it's not clear where key is)\n", "".join(p.get_output_lines()))
        util.print_object_location(p, key, None, print_parentheses=False)
        self.assertEqual("It's not clear where key is.\n", "".join(p.get_output_lines()))
        util.print_object_location(p, key, bag)
        result = "".join(p.get_output_lines())
        self.assertTrue("in bag" in result and "in your inventory" in result)
        util.print_object_location(p, key, room)
        self.assertTrue("in your current location" in "".join(p.get_output_lines()))
        util.print_object_location(p, bag, p)
        self.assertTrue("in your inventory" in "".join(p.get_output_lines()))
        util.print_object_location(p, p, room)
        self.assertTrue("in your current location" in "".join(p.get_output_lines()))

    def test_moneydisplay(self):
        self.assertEqual("nothing", util.money_display_fantasy(0))
        self.assertEqual("zilch", util.money_display_fantasy(0, zero_msg="zilch"))
        self.assertEqual("nothing", util.money_display_fantasy(0.01))
        self.assertEqual("1 copper", util.money_display_fantasy(0.06))
        self.assertEqual("12 gold, 3 silver, and 2 copper", util.money_display_fantasy(123.24))
        self.assertEqual("12 gold, 3 silver, and 3 copper", util.money_display_fantasy(123.26))
        self.assertEqual("0g/0s/0c", util.money_display_fantasy(0, True))
        self.assertEqual("12g/3s/2c", util.money_display_fantasy(123.24, True))
        self.assertEqual("12g/3s/3c", util.money_display_fantasy(123.26, True))
        self.assertEqual("nothing", util.money_display_modern(0))
        self.assertEqual("zilch", util.money_display_modern(0, zero_msg="zilch"))
        self.assertEqual("nothing", util.money_display_modern(0.001))
        self.assertEqual("1 cent", util.money_display_modern(0.006))
        self.assertEqual("5 cent", util.money_display_modern(0.05))
        self.assertEqual("123 dollar and 24 cent", util.money_display_modern(123.244))
        self.assertEqual("123 dollar and 25 cent", util.money_display_modern(123.246))
        self.assertEqual("$ 0.00", util.money_display_modern(0, True))
        self.assertEqual("$ 123.24", util.money_display_modern(123.244, True))
        self.assertEqual("$ 123.25", util.money_display_modern(123.246, True))

    def test_money_to_float(self):
        self.assertEqual(0.0, util.money_to_float_fantasy({}))
        self.assertAlmostEqual(0.3, util.money_to_float_fantasy({"copper": 1.0, "coppers": 2.0 }), places=4)
        self.assertAlmostEqual(325.6, util.money_to_float_fantasy({"gold": 22.5, "silver": 100.2, "copper": 4 }), places=4)
        self.assertAlmostEqual(289.3, util.money_to_float_fantasy("22g/66s/33c"), places=4)
        self.assertEqual(0.0, util.money_to_float_modern({}))
        self.assertAlmostEqual(0.55, util.money_to_float_modern({"cent": 22, "cents": 33}), places=4)
        self.assertAlmostEqual(55.0, util.money_to_float_modern({"dollar": 22, "dollars": 33}), places=4)
        self.assertAlmostEqual(5.42, util.money_to_float_modern({"dollar": 5, "cent": 42 }), places=4)
        self.assertAlmostEqual(3.45, util.money_to_float_modern("$3.45"), places=4)
        self.assertAlmostEqual(3.45, util.money_to_float_modern("$  3.45"), places=4)

    def test_words_to_money_fantasy(self):
        tf = util.money_to_float_fantasy
        mw = util.MONEY_WORDS_FANTASY
        with self.assertRaises(ParseError):
            util.words_to_money([], money_to_float=tf, money_words=mw)
        with self.assertRaises(ParseError):
            util.words_to_money(["44"], money_to_float=tf, money_words=mw)
        with self.assertRaises(ParseError):
            util.words_to_money(["44g/s"], money_to_float=tf, money_words=mw)
        with self.assertRaises(ParseError):
            util.words_to_money(["gold"], money_to_float=tf, money_words=mw)
        self.assertAlmostEqual(451.6, util.words_to_money(["44", "gold", "5", "silver", "66", "copper"], money_to_float=tf, money_words=mw), places=4)
        self.assertAlmostEqual(451.6, util.words_to_money(["44g/5s/66c"], money_to_float=tf, money_words=mw), places=4)

    def test_words_to_money_modern(self):
        tf = util.money_to_float_modern
        mw = util.MONEY_WORDS_MODERN
        with self.assertRaises(ParseError):
            util.words_to_money([], money_to_float=tf, money_words=mw)
        with self.assertRaises(ParseError):
            util.words_to_money(["44"], money_to_float=tf, money_words=mw)
        with self.assertRaises(ParseError):
            util.words_to_money(["$xxx"], money_to_float=tf, money_words=mw)
        with self.assertRaises(ParseError):
            util.words_to_money(["dollar"], money_to_float=tf, money_words=mw)
        self.assertAlmostEqual(46.15, util.words_to_money(["44", "dollar", "215", "cent"], money_to_float=tf, money_words=mw), places=4)
        self.assertAlmostEqual(46.15, util.words_to_money(["$46.15"], money_to_float=tf, money_words=mw), places=4)
        self.assertAlmostEqual(46.15, util.words_to_money(["$ 46.15"], money_to_float=tf, money_words=mw), places=4)
        self.assertAlmostEqual(46.15, util.words_to_money(["$", "46.15"], money_to_float=tf, money_words=mw), places=4)

    def test_roll_die(self):
        total, values = util.roll_die()
        self.assertTrue(1<=total<=6)
        self.assertEqual(1, len(values))
        self.assertEqual(total, values[0])
        total, values = util.roll_die(20, 10)   # 20d10
        self.assertEqual(20, len(values))
        with self.assertRaises(AssertionError):
            util.roll_die(21, 10)

    def test_parse_duration(self):
        duration = util.parse_duration(["1","hour","1","minute","1","second"])
        self.assertEqual(datetime.timedelta(hours=1, minutes=1, seconds=1), duration)
        duration = util.parse_duration(["3","hours","2","minutes","5","seconds"])
        self.assertEqual(datetime.timedelta(hours=3, minutes=2, seconds=5), duration)
        duration = util.parse_duration(["3","h","2","min","5","sec"])
        self.assertEqual(datetime.timedelta(hours=3, minutes=2, seconds=5), duration)
        duration = util.parse_duration(["3","h","2","m","5","s"])
        self.assertEqual(datetime.timedelta(hours=3, minutes=2, seconds=5), duration)
        duration = util.parse_duration(["3h","2m","5s"])
        self.assertEqual(datetime.timedelta(hours=3, minutes=2, seconds=5), duration)
        duration = util.parse_duration(["2.5","min"])
        self.assertEqual(datetime.timedelta(minutes=2, seconds=30), duration)
        with self.assertRaises(ParseError):
            util.parse_duration(None)
        with self.assertRaises(ParseError):
            util.parse_duration(["1","2","3"])
        with self.assertRaises(ParseError):
            util.parse_duration(["1","apple"])
        with self.assertRaises(ParseError):
            util.parse_duration(["seconds","2"])

    def test_duration_display(self):
        self.assertEqual("no time at all", util.duration_display(datetime.timedelta(0)))
        self.assertEqual("1 hour, 1 minute, and 1 second", util.duration_display(datetime.timedelta(hours=1, minutes=1, seconds=1)))
        self.assertEqual("2 hours, 3 minutes, and 4 seconds", util.duration_display(datetime.timedelta(hours=2, minutes=3, seconds=4)))
        self.assertEqual("2 minutes", util.duration_display(datetime.timedelta(minutes=2)))
        self.assertEqual("2 minutes and 1 second", util.duration_display(datetime.timedelta(minutes=2, seconds=1)))


if __name__ == '__main__':
    unittest.main()
