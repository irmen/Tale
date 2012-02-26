import unittest
from mudlib.baseobjects import Location, Exit, Thing, Item
from mudlib.npc import NPC

hall = Location("Main hall", "A very large hall.")
attic = Location("Attic", "A dark attic.")
street = Location("Street", "An endless street.")
hall.exits["up"] = Exit(attic, "A ladder leads up.")
hall.exits["door"] = Exit(street, "A heavy wooden door to the east blocks the noises from the street outside.")
hall.exits["east"] = hall.exits["door"]
hall.items += [ Thing("oak table", "a large round table with a lot of cracks"),
                Thing("hum", "a faint but annoying hum is coming from somewhere", visible=False),
                Item("rusty key", "a large rusty key without any label") ]
max,julie = NPC("Max", "m", "red-haired max"), NPC("Julie", "f", "attractive julie")
max.set_race("human")
julie.set_race("human")
hall.livings = { max, julie }

class TestLocations(unittest.TestCase):
    def test_look(self):
        expected="""[Main hall]
A very large hall.
You see an oak table and a rusty key.
You can see the following exits:
A heavy wooden door to the east blocks the noises from the street outside.
A ladder leads up.
Julie and Max are here."""
        self.assertEqual(expected, hall.look())

if __name__ == '__main__':
    unittest.main()
