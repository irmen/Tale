"""
Rose street.
Connects with Magnolia street on the Crossing.

car park, playground
rose street north, crossing, rose street south
butcher, storage room
"""

import random
import zones.houses
import zones.npcs

from tale.base import Location, Exit, Door, Key, Living, ParseResult, _limbo
from tale.items.basic import Money
from tale.errors import ParseError, ActionRefused, StoryCompleted
from tale.util import call_periodically, Context
from tale import mud_context


north_street = Location("Rose Street", "The northern part of Rose Street.")
south_street = Location("Rose Street", "The southern part of Rose Street.")

crossing = Location("Crossing", "Town Crossing.")
crossing.add_exits([
    Exit("west", "magnolia_st.street2", "Westwards lies Magnolia Street."),
    Exit("east", "magnolia_st.street3", "Magnolia Street extends to the east, eventually leading towards the factory."),
])

Exit.connect(crossing, "north", "A part of Rose Street lies to the north.", None,
             north_street, ["south", "crossing"], "The street goes south towards the crossing.", None)
Exit.connect(crossing, "south", "Rose Street continues to the south.", None,
             south_street, ["north", "crossing"], "The crossing is back towards the north.", None)

playground = Location("Playground", "Children's playground. You see a rusty merry-go-round, and a little swing. "
                                    "To the west, a house is visible.")
playground.add_extradesc({"west", "house"}, "You can see your house from here!")
playground.add_exits([
    Door("fence", _limbo, "On the north end of the playground is a sturdy looking padlocked fence.",
         locked=True, opened=False, key_code="999999999"),  # this door is never meant to be opened
])

Exit.connect(playground, ["east", "street"], "Rose Street is back east.", None,
             north_street, ["west", "playground"], "The children's playground is to the west.", None)


class CarPark(Location):
    def init(self):
        self.verbs = {"drive": "Drive a car",
                      "open": "Open something",
                      "enter": "Enter something",
                      "sit": "Sit somewhere",
                      "use": "Use something",
                      "start": "Start something"
                      }

    def handle_verb(self, parsed: ParseResult, actor: Living) -> bool:
        if parsed.verb in ("drive", "open", "enter", "sit", "use", "start"):
            if not parsed.args:
                raise ParseError("%s what?" % parsed.verb)
            if "yellow" not in parsed.args and "convertible" not in parsed.args:
                if "car" in parsed.args or "engine" in parsed.args:
                    raise ActionRefused("Most of the cars are locked. You should look for one that isn't.")
                raise ActionRefused("You cannot do that.")
            # check if Peter is with you
            if not self.search_living("Peter"):
                raise ActionRefused("Surely you wouldn't leave the town without your friend Peter! "
                                    "You should find him and get out here together!")
            # player drives the yellow car away from here together with her friend Peter, and thus the story ends!
            actor.tell_text_file(mud_context.resources["messages/completion_success.txt"])
            raise StoryCompleted
        return False


carpark = CarPark("Car Parking", "There are a few cars still parked over here. Their owners are nowhere to be seen. "
                                 "One yellow convertible grabs your attention.")
carpark.add_extradesc({"cars"}, "They look abandoned. The doors are all locked, except the doors of the yellow convertible.")
carpark.add_extradesc({"convertible", "yellow"}, "It is a small two-seater and the doors are open. You can't believe your eyes, "
                                                 "but the key is actually still in the ignition!")

# not enough to buy the medicine, player needs to find more, or haggle:
carpark.init_inventory([Money("wallet", 16.0, title="someone's wallet",
                              short_descr="Someone's wallet lies on the pavement, "
                                          "they seem to have lost it. There's some money in it.")])


parking_gate, _ = Door.connect(north_street, ["gate", "parking"],
                               "Through the iron gate you can see the car parking. A few cars are still parked there, it seems.",
                               None, carpark, ["gate", "street"], "Rose street is back through the gate.", None,
                               locked=True, opened=False, key_code="carpark-gate")

parking_key = Key("key", "rusty key", descr="It is what appears to be an old key, with a label on it.",
                  short_descr="On the ground is a key, it's become quite rusty.")
parking_key.key_for(parking_gate)
parking_key.add_extradesc({"label"}, "The label says: `parking area gate'.")


class StorageRoom(Location):
    @call_periodically(5.0, 20.0)
    def shiver_from_cold(self, ctx: Context) -> None:
        # it's cold in the storage room, it makes people shiver
        if self.livings:
            living = random.choice(list(self.livings))
            living.do_socialize("shiver")


butcher = Location("Butcher shop", "The town's butcher shop. Usually there's quite a few people waiting in line, but now it is deserted.")
butcher.insert(parking_key, None)
Exit.connect(butcher, ["north", "street"], "Rose street is back to the north.", None,
             south_street, ["south", "butcher"], "The butcher shop is to the south.", None)

storage_room = StorageRoom("Storage room", "The butcher's meat storage room. Brrrrr, it is cold here!")

storage_room_door, _ = Door.connect(butcher, ["door", "storage"],
                                    "A door leads to the storage room.",
                                    "The meat storage is behind it. The door's locked with a security card instead of a key.",
                                    storage_room, ["door", "shop"], "The door leads back to the shop.", None,
                                    locked=True, key_code="butcher1")

friend = zones.npcs.Friend("Peter", "m", descr="It's your friend Peter, who works at the butcher shop.")
storage_room.insert(friend, None)

butcher_key = Key("card", "security card", descr="It is a security card, with a single word `storage' written on it.")
butcher_key.key_for(storage_room_door)
zones.houses.garden.insert(butcher_key, None)
