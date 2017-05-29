"""
The house, where the player starts the game.
Also defines the Neighbor's house, where other things can be found.
"""

from tale.base import Location, Exit, Door


# ----------------- START House & Kitchen  -------------------------

livingroom = Location("Living room", "The living room in your little home. Your big TV hangs on a wall.")
livingroom.add_extradesc({"plasma", "tv"},
                         "You recently bought a bigger TV, but haven't yet found the time to actually watch anything.")
kitchen = Location("Kitchen", "A small but well supplied kitchen. Rather than ordering take-away, "
                              "you prefer cooking your own meals -- unlike most of the other people you know in town. "
                              "A window lets you look outside.")
kitchen.add_extradesc({"window", "outside"},
                      "Through the kitchen window you can see your small garden and behind that, the children's playground.")

#  Exits

front_door = Door(["door", "outside", "street"], "magnolia_st.street1", "Your front door leads outside, to the street.",
                  "There's a heavy front door here that leads to the streets outside.", opened=False)
house_door = front_door.reverse_door(["house", "north", "inside"], livingroom,
                                     "You can go back inside your house.", "It's your house, on the north side of the street.",
                                     reverse_open_msg="Someone outside opens the door.",
                                     reverse_close_msg="Someone outside closes the door.",
                                     this_open_msg="Someone in the house opens the door.",
                                     this_close_msg="Someone in the house closes the door.")
livingroom.add_exits([
    Exit("kitchen", kitchen, "Your kitchen is adjacent to this room.",
                             "You can see your kitchen. The previous house owners had a door there but you removed it."),
    front_door
])

kitchen.add_exits([
    Exit(["living room", "livingroom", "back"], livingroom, "The living room is back the way you entered.")
])


# ----------------- Neighbours House, Bedroom, Garden  -------------------------

neighbors_house = Location("Neighbor's House", "The house of your neighbors across the street.")

bedroom = Location("Bedroom", "A rather untidy little bedroom. There's clothes lying all over the place. The window is open!")
bedroom.add_extradesc({"clothes"}, "A pile of clothes lies on the floor. The back pocket of some trousers draw your attention.")
bedroom.add_extradesc({"window"}, "The bedroom window is open and you see a ladder leading down to the garden.")
bedroom.add_extradesc({"pocket", "trousers"}, "There's something in the pocket.")

garden = Location("Neighbor's Garden", "The garden of your neighbor across the street. "
                                       "Behind some trees to the south you see what appears to be a storage building of a shop.")
garden.add_extradesc({"ladder"}, "It leads up towards a window.")
garden.add_extradesc({"trees", "south", "building"},
                     "The building behind the trees could very well be the meat storage room of the butcher shop in town.")
garden.add_exits([
    Exit(["ladder", "up"], bedroom, "A ladder leads up towards a window in the house."),
    Exit(["fence", "street"], "magnolia_st.street2", "You can step over a low fence back onto the street if you wish."),
    Exit(["house", "doors"], neighbors_house, "The garden doors are open and lead back to the house.")
])

bedroom.add_exits([
    Exit(["ladder", "down"], garden, "The ladder that is placed outside of the window provides access down to the garden below.")
])

neighbors_house.add_exits([
    Exit(["street", "north"], "magnolia_st.street2", "The street is back north."),
    Exit(["up", "stairs"], bedroom, "Up the stairs is the bedroom."),
    Exit(["garden", "doors"], garden, "The garden doors are open and lead to... the garden.")
])
