"""
Unit tests for util functions

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import unittest
import mudlib.util
from mudlib.baseobjects import Item, Container, Location
from mudlib.player import Player

class TestUtil(unittest.TestCase):
    def test_print_location(self):
        p = Player("julie", "f")
        key = Item("key")
        bag = Container("bag")
        room = Location("room")
        bag+=key
        p+=bag
        room.enter(p)
        with self.assertRaises(StandardError):
            mudlib.util.print_object_location(p, None, None)
        mudlib.util.print_object_location(p, key, None)
        self.assertEqual("(it's not clear where key is)\n", "".join(p.get_output_lines()))
        mudlib.util.print_object_location(p, key, None, print_parentheses=False)
        self.assertEqual("It's not clear where key is.\n", "".join(p.get_output_lines()))
        mudlib.util.print_object_location(p, key, bag)
        result = "".join(p.get_output_lines())
        self.assertTrue("in bag" in result and "in your inventory" in result)
        mudlib.util.print_object_location(p, key, room)
        self.assertTrue("in your current location" in "".join(p.get_output_lines()))
        mudlib.util.print_object_location(p, bag, p)
        self.assertTrue("in your inventory" in "".join(p.get_output_lines()))
        mudlib.util.print_object_location(p, p, room)
        self.assertTrue("in your current location" in "".join(p.get_output_lines()))


if __name__ == '__main__':
    unittest.main()
