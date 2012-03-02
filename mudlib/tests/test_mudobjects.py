import unittest
from mudlib.baseobjects import Location, Exit, Item
from mudlib.npc import NPC

hall = Location("Main hall", "A very large hall.")
attic = Location("Attic", "A dark attic.")
street = Location("Street", "An endless street.")
hall.exits["up"] = Exit(attic, "A ladder leads up.")
hall.exits["door"] = Exit(street, "A heavy wooden door to the east blocks the noises from the street outside.")
hall.exits["east"] = hall.exits["door"]
hall.items += [ Item("table", "oak table",
                     """
                     a large dark table with a lot of cracks in its surface
                     """),
                Item("key", "rusty key",
                     """
                     an old rusty key without a label
                     """) ]
rat,julie = NPC("rat", "m", race="rodent"), NPC("julie", "f", "attractive Julie",
                                 """
                                 She's quite the looker.
                                 """)
hall.livings = { rat, julie }

class TestLocations(unittest.TestCase):
    def test_look(self):
        expected="""[Main hall]
A very large hall.
You see an oak table and a rusty key.
A heavy wooden door to the east blocks the noises from the street outside.
A ladder leads up.
Attractive Julie and rat are here."""
        self.assertEqual(expected, hall.look())
        expected="""[Attic]
A dark attic."""
        self.assertEqual(expected, attic.look())

    def test_look_short(self):
        expected="""[Attic]"""
        self.assertEqual(expected, attic.look(short=True))
        expected="""[Main hall]
You see: key, table
Exits: door, east, up
Present: julie, rat"""
        self.assertEqual(expected, hall.look(short=True))


class TestNPC(unittest.TestCase):
    def test_names(self):
        self.assertEqual("julie", julie.name)
        self.assertEqual("attractive Julie", julie.title)
        self.assertEqual("She's quite the looker.", julie.description)
        self.assertEqual("rat", rat.name)
        self.assertEqual("rat", rat.title)
        self.assertEqual("rat", rat.description)

if __name__ == '__main__':
    unittest.main()
