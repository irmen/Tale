"""
Unit tests for the shop system

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import unittest
import datetime
from tale.shop import Shopkeeper, ShopBehavior
from tale.errors import ActionRefused


class TestShopping(unittest.TestCase):
    def setUp(self):
        self.shopkeeper = Shopkeeper("lucy", "f")
        shop = ShopBehavior()
        shop.open_hours = [(9, 17), (22, 3)]    # from 9 to 17 and in the night from 22 to 03
        self.shopkeeper.shop = shop

    def test_open_hours(self):
        self.shopkeeper.validate_open_hours(datetime.time(9, 0))
        self.shopkeeper.validate_open_hours(datetime.time(9, 1))
        self.shopkeeper.validate_open_hours(datetime.time(13, 0))
        self.shopkeeper.validate_open_hours(datetime.time(16, 59))
        self.shopkeeper.validate_open_hours(datetime.time(22, 0))
        self.shopkeeper.validate_open_hours(datetime.time(23, 59))
        self.shopkeeper.validate_open_hours(datetime.time(0, 0))
        self.shopkeeper.validate_open_hours(datetime.time(0, 1))
        self.shopkeeper.validate_open_hours(datetime.time(2, 59))

    def test_closed_hours(self):
        with self.assertRaises(ActionRefused):
            self.shopkeeper.validate_open_hours(datetime.time(6, 30))
        with self.assertRaises(ActionRefused):
            self.shopkeeper.validate_open_hours(datetime.time(8, 59))
        with self.assertRaises(ActionRefused):
            self.shopkeeper.validate_open_hours(datetime.time(17, 0))
        with self.assertRaises(ActionRefused):
            self.shopkeeper.validate_open_hours(datetime.time(21, 59))
        with self.assertRaises(ActionRefused):
            self.shopkeeper.validate_open_hours(datetime.time(3, 0))


if __name__ == '__main__':
    unittest.main()
