import unittest
from mudlib.baseobjects import Location, Exit, Item
from mudlib.npc import NPC

hall = Location("Main hall", "A very large hall.")
attic = Location("Attic", "A dark attic.")
street = Location("Street", "An endless street.")
hall.exits["up"] = Exit(attic, "A ladder leads up.")
hall.exits["door"] = Exit(street, "A heavy wooden door blocks the noises from the street outside.")
hall.items += [ Item("oak table", "a large round table with a lot of cracks"),
                Item("rusty key", "a large rusty key without any label") ]
hall.livings = { NPC("max", "m", "red-haired max"), NPC("julie", "f", "attractive julie") }

class TestLocations(unittest.TestCase):
    def test_look(self):
        expected="""[Main hall]
A very large hall.
You see an oak table and a rusty key.
You can see the following exits:
A heavy wooden door blocks the noises from the street outside.
A ladder leads up.
julie and max are here."""
        self.assertEqual(expected, hall.look())

if __name__ == '__main__':
    unittest.main()
