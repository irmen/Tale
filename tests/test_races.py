"""
Unit tests for race data

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import unittest
import tale.races as races


class TestRaces(unittest.TestCase):
    def test_attributes(self):
        human = races._races["human"]
        self.assertEqual(72.0, human["mass"])
        self.assertEqual(8, len(human["stats"]))
        self.assertEqual(races.BodyType.HUMANOID, human["body"])
        self.assertEqual(races.BodySize.HUMAN_SIZED, human["size"])
        self.assertEqual("English", human["language"])

    def test_generated_race(self):
        human = races.races["human"]
        self.assertEqual(72.0, human.mass)
        self.assertEqual(8, len(human.stats))
        self.assertEqual(races.BodyType.HUMANOID, human.body)
        self.assertEqual(races.BodySize.HUMAN_SIZED, human.size)
        self.assertEqual("English", human.language)
        self.assertEqual((33, 3), human.stats.agi)
        self.assertTrue(human.flags.playable)
        self.assertFalse(races.races["plant"].flags.playable)

    def test_enum_descriptions(self):
        self.assertEqual("somewhat large", races.BodySize.SOMEWHAT_LARGE.value)
        self.assertEqual("biped", races.BodyType.BIPED.value)

    def test_bodysize_compare(self):
        self.assertEqual(races.BodySize.LARGE, races.BodySize.LARGE)
        self.assertNotEqual(races.BodySize.LARGE, races.BodySize.SMALL)
        self.assertLess(races.BodySize.TINY, races.BodySize.VAST)
        self.assertGreater(races.BodySize.LARGE, races.BodySize.SMALL)

    def test_globals(self):
        self.assertIn("human", races.playable_races)
        self.assertIn("elf", races.races)


if __name__ == '__main__':
    unittest.main()
