"""
Unit tests for the hint system

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
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
        h.checkpoint("state1")
        self.assertIsNone(h.hint(self.player))

    def test_checkpoint(self):
        h = HintSystem()
        h.init([
            Hint("start", None, "first"),
            Hint("state2", None, "second"),
            Hint("state4", None, "third"),
        ])
        self.assertTrue(h.has_hints())
        self.assertIsNone(h.hint(self.player))
        self.assertTrue(h.checkpoint("start"))
        self.assertFalse(h.checkpoint("start"))
        self.assertEqual("first", h.hint(self.player))
        h.checkpoint("state1")
        self.assertEqual("first", h.hint(self.player))
        h.checkpoint("state2")
        self.assertEqual("second", h.hint(self.player))
        h.checkpoint("state3")
        self.assertEqual("second", h.hint(self.player))
        h.checkpoint("state4")
        self.assertEqual("third", h.hint(self.player))

    def test_location(self):
        h = HintSystem()
        h.init([
            Hint(None, None, "first"),
            Hint(None, "loc1", "second"),
            Hint(None, "loc2", "third"),
        ])
        self.assertEqual("first", h.hint(self.player))
        self.player.location = "loc999"
        self.assertEqual("first", h.hint(self.player))
        self.player.location = "loc1"
        self.assertEqual("second", h.hint(self.player))
        self.player.location = "loc2"
        self.assertEqual("third", h.hint(self.player))

    def test_active_and_multi(self):
        h = HintSystem()

        class Hint1(Hint):
            def active(self, checkpoints, player):
                return "1" in checkpoints

        class Hint2(Hint):
            def active(self, checkpoints, player):
                return "2" in checkpoints and "3" not in checkpoints

        class Hint3(Hint):
            def active(self, checkpoints, player):
                return "1" in checkpoints and "2" in checkpoints and "3" in checkpoints and "4" in checkpoints

        h.init([
            Hint1(None, None, "first"),
            Hint2(None, None, "second"),
            Hint3(None, None, "third"),
        ])
        self.assertIsNone(h.hint(self.player))
        h.checkpoint("1")
        self.assertEqual("first", h.hint(self.player))
        h.checkpoint("2")
        self.assertEqual("first second", h.hint(self.player))
        h.checkpoint("3")
        self.assertEqual("first", h.hint(self.player))
        h.checkpoint("4")
        self.assertEqual("first third", h.hint(self.player))

    def test_recap(self):
        h = HintSystem()
        self.assertEqual([], h.recap())
        h.checkpoint("state1", "recap one")
        self.assertEqual(["recap one"], h.recap())
        h.checkpoint("state1", "recap two")
        self.assertEqual(["recap one"], h.recap())
        h.checkpoint("state2", "recap three")
        self.assertEqual(["recap one", "recap three"], h.recap())


if __name__ == '__main__':
    unittest.main()
