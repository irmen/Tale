"""
Unit tests for race data

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import unittest
import tale.races as races


class TestRaces(unittest.TestCase):
    def test_attributes(self):
        human = races.races["human"]
        self.assertEqual(72.0, human["mass"])
        self.assertEqual(8, len(human["stats"]))
        self.assertEqual(races.B_HUMANOID, human["bodytype"])
        self.assertEqual(races.S_HUMAN_SIZED, human["size"])
        self.assertEqual("English", human["language"])

    def test_descriptions(self):
        self.assertEqual("somewhat large", races.sizes[races.S_SOMEWHAT_LARGE])
        self.assertEqual("biped", races.bodytypes[races.B_BIPED])


if __name__ == '__main__':
    unittest.main()
