"""
Unit tests for the hint system

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import unittest
from tale.hints import Hint, HintSystem
from tale.player import Player


class TestHints(unittest.TestCase):
    def setUp(self):
        self.player = Player("peter", "m")

    def test_empty(self):
        h = HintSystem()
        self.assertFalse(h.has_hints())
        self.assertIsNone(h.hint(self.player))
        h.init([])
        self.assertIsNone(h.hint(self.player))
        h.state("state1")
        self.assertIsNone(h.hint(self.player))

    def test_state(self):
        h = HintSystem()
        h.init([
            Hint("start", None, None, "first"),
            Hint("state2", None, None, "second"),
            Hint("state4", None, None, "third"),
        ])
        self.assertTrue(h.has_hints())
        self.assertIsNone(h.hint(self.player))
        h.state("start")
        self.assertEqual("first", h.hint(self.player))
        h.state("state1")
        self.assertEqual("first", h.hint(self.player))
        h.state("state2")
        self.assertEqual("second", h.hint(self.player))
        h.state("state3")
        self.assertEqual("second", h.hint(self.player))
        h.state("state4")
        self.assertEqual("third", h.hint(self.player))

    def test_location(self):
        h = HintSystem()
        h.init([
            Hint(None, None, None, "first"),
            Hint(None, "loc1", None, "second"),
            Hint(None, "loc2", None, "third"),
        ])
        self.assertEqual("first", h.hint(self.player))
        self.player.location = "loc999"
        self.assertEqual("first", h.hint(self.player))
        self.player.location = "loc1"
        self.assertEqual("second", h.hint(self.player))
        self.player.location = "loc2"
        self.assertEqual("third", h.hint(self.player))

    def test_filter_and_multi(self):
        h = HintSystem()
        def filter1(states, player):
            return "1" in states
        def filter2(states, player):
            return "2" in states and not "3" in states
        def filterAll(states, player):
            return "1" in states and "2" in states and "3" in states and "4" in states
        h.init([
            Hint(None, None, filter1, "first"),
            Hint(None, None, filter2, "second"),
            Hint(None, None, filterAll, "third"),
        ])
        self.assertIsNone(h.hint(self.player))
        h.state("1")
        self.assertEqual("first", h.hint(self.player))
        h.state("2")
        self.assertEqual("first second", h.hint(self.player))
        h.state("3")
        self.assertEqual("first", h.hint(self.player))
        h.state("4")
        self.assertEqual("first third", h.hint(self.player))

    def test_recap(self):
        h = HintSystem()
        self.assertEqual([], h.recap())
        h.state("state1", "recap one")
        self.assertEqual(["recap one"], h.recap())
        h.state("state1", "recap two")
        self.assertEqual(["recap one"], h.recap())
        h.state("state2", "recap three")
        self.assertEqual(["recap one", "recap three"], h.recap())


if __name__ == '__main__':
    unittest.main()
