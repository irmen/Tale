"""
Rose street.
Connects with Magnolia street on the Crossing.

car park, playground
rose street north, crossing, rose street south
butcher, storage room
"""

import random
import zones.magnolia_st
import zones.houses

from tale.base import Location, Exit, Door, Key, _limbo, Living
from tale.util import call_periodically, Context


north_street = Location("Rose Street", "The northern part of Rose Street.")
south_street = Location("Rose Street", "The southern part of Rose Street.")

crossing = Location("Crossing", "Town Crossing.")
crossing.add_exits([
    Exit("west", zones.magnolia_st.street2, "Westwards lies Magnolia Street."),
    Exit("east", zones.magnolia_st.street3, "Magnolia Street extends to the east, eventually leading towards the factory."),
    Exit("north", north_street, "A part of Rose Street lies to the north."),
    Exit("south", south_street, "Rose Street continues to the south.")
])

playground = Location("Playground", "Children's playground. You see a rusty merry-go-round, and a little swing. "
                                    "To the west, a house is visible.")
playground.add_extradesc({"west", "house"}, "You can see your house from here!")
playground.add_exits([
    Door("fence", _limbo, "On the north end of the playground is a sturdy looking padlocked fence.",
         locked=True, opened=False),  # this door is never meant to be opened
    Exit(["east", "street"], north_street, "Rose Street is back east."),
    zones.magnolia_st.street_gate
])

carpark = Location("Car Parking", "There are a few cars still parked over here. Their owners are nowhere to be seen. "
                                  "One yellow car grabs your attention.")
carpark.add_extradesc({"cars"}, "They look abandoned, but their doors are all locked.")
carpark.add_extradesc({"car", "yellow"}, "It is a small two seater!")
carpark.add_exits([
    Exit(["gate", "street"], north_street, "Rose street is back through the gate.")
])

parking_gate = Door(["gate", "parking"], carpark,
                    "Through the iron gate you can see the car parking. A few cars are still parked there, it seems.",
                    locked=True, opened=False)
parking_gate.key_code = "111"


class StorageRoom(Location):
    @call_periodically(10.0, 20.0)
    def shiver_from_cold(self, ctx: Context) -> None:
        # it's cold in the storage room, it makes you shiver
        if self.livings:
            living = random.choice(list(self.livings))
            living.do_socialize("shiver")


class Friend(Living):
    # @todo add more behavior and stop screaming when rescued
    @call_periodically(10.0, 20.0)
    def say_something(self, ctx: Context) -> None:
        self.do_verb("yell \"Help me, I'm locked in\"", ctx)


butcher = Location("Butcher shop", "The town's butcher shop. Usually there's quite a few people waiting in line, but now it is deserted.")
storage_room = StorageRoom("Storage room", "The butcher's meat storage room. Brrrrr, it is cold here!")
storage_room_door = Door(["door", "storage"], storage_room, "A door leads to the storage room.",
                         "The meat storage is behind it. The door's locked with a security card instead of a key.",
                         locked=True, opened=False)
storage_room_door.key_code = "butcher1"
butcher.add_exits([
    Exit(["north", "street"], south_street, "Rose street is back to the north."),
    storage_room_door
])
storage_room.add_exits([
    storage_room_door.reverse_door(["door", "shop"], butcher, "The door leads back to the shop.")
])
friend = Friend("Peter", "m", descr="It's your friend Peter, who works at the butcher shop.")
storage_room.insert(friend, None)


north_street.add_exits([
    Exit(["west", "playground"], playground, "The children's playground is to the west."),
    Exit(["south", "crossing"], crossing, "The street goes south towards the crossing."),
    parking_gate
])

south_street.add_exits([
    Exit(["north", "crossing"], crossing, "The crossing is back towards the north."),
    Exit(["south", "butcher"], butcher, "The butcher shop is to the south.")
])

parking_key = Key("key", "rusty key", descr="It is what appears to be an old key, with a label on it.",
                  short_descr="On the ground is a key, it's become quite rusty.")
parking_key.key_for(parking_gate)
parking_key.add_extradesc({"label"}, "The label says: 'parking area gate'.")

butcher.insert(parking_key, None)

butcher_key = Key("card", "security card", descr="It is a security card, with a single word 'storage' written on it.")
butcher_key.key_for(storage_room_door)
zones.houses.garden.insert(butcher_key, None)
