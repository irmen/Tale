"""
Rose street.
Connects with Magnolia street on the Crossing.

car park, playground
rose street north, crossing, rose street south
butcher, storage room
"""

import zones.magnolia_st

from tale.base import Location, Exit, Door, Key, _limbo


north_street = Location("Rose Street", "The northern part of Rose Street.")
south_street = Location("Rose Street", "The southern part of Rose Street.")

crossing = Location("Crossing", "Town Crossing.")
crossing.add_exits([
    Exit("west", "magnolia_st.street2", "Westwards lies Magnolia Street."),
    Exit("east", "magnolia_st.street3", "Magnolia Street extends to the east, eventually leading towards the factory."),
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

butcher = Location("Butcher shop", "The town's butcher shop. Usually there's quite a few people waiting in line, but now it is deserted.")
storage_room = Location("Storage Cell", "The butcher's meat storage cell. Brrrrr, it is cold here!")
butcher.add_exits([
    Exit(["north", "street"], south_street, "Rose street is back to the north."),
    Door(["door", "storage"], storage_room, "A door leads to the storage room.")
])
storage_room.add_exits([
    Door(["door", "shop"], butcher, "The door leads back to the shop.")
])

north_street.add_exits([
    Exit(["west", "playground"], playground, "The children's playground is to the west."),
    Exit(["south", "crossing"], crossing, "The street goes south towards the crossing."),
    parking_gate
])

south_street.add_exits([
    Exit(["north", "crossing"], crossing, "The crossing is back towards the north."),
    Exit(["south", "butcher"], butcher, "The butcher shop is to the south.")
])

parking_key = Key("key", "rusty key", "It is what appears to be an old key, with a label on it.",
                  "On the ground is a key, it's become quite rusty.")
parking_key.key_for(parking_gate)
parking_key.add_extradesc({"label"}, "The label says: 'parking area gate'.")

butcher.insert(parking_key, None)
