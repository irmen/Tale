import unittest
import mudlib.races

class TestRaces(unittest.TestCase):
    def test_attributes(self):
        human = mudlib.races.races["human"]
        self.assertEqual(72.0, human["mass"])
        self.assertEqual(8, len(human["stats"]))
        self.assertEqual(mudlib.races.B_HUMANOID, human["bodytype"])
        self.assertEqual(mudlib.races.S_HUMAN_SIZED, human["size"])
        self.assertEqual("English", human["language"])
    def test_descriptions(self):
        self.assertEqual("somewhat large", mudlib.races.sizes[mudlib.races.S_SOMEWHAT_LARGE])
        self.assertEqual("biped", mudlib.races.bodytypes[mudlib.races.B_BIPED])

if __name__ == '__main__':
    unittest.main()
