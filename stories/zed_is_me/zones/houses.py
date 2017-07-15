"""
The house, where the player starts the game.
Also defines the Neighbor's house, where other things can be found.
"""

from tale.base import Location, Exit
from tale.items.basic import Money


# ----------------- START House & Kitchen  -------------------------

livingroom = Location("Living room", "The living room in your little home. Your big TV hangs on a wall.")
livingroom.add_extradesc({"plasma", "tv"},
                         "You recently bought a bigger TV, but haven't yet found the time to actually watch anything.")
# living room front door is defined in the street zone module

kitchen = Location("Kitchen", "A small but well supplied kitchen. Rather than ordering take-away, "
                              "you prefer cooking your own meals -- unlike most of the other people you know in town. "
                              "A window lets you look outside.")
kitchen.add_extradesc({"window", "outside"},
                      "Through the kitchen window you can see your small garden and behind that, the children's playground.")
kitchen.init_inventory([Money("cash", 8.0, title="small amount of cash")])  # not enough, player needs to find more


Exit.connect(livingroom, "kitchen",
             "Your kitchen is adjacent to this room.",
             "You can see your kitchen. The previous house owners had a door there but you removed it.",
             kitchen, ["living room", "livingroom", "back"],
             "The living room is back the way you entered.",
             None)


# ----------------- Neighbours House, Bedroom, Garden  -------------------------

neighbors_house = Location("Neighbor's House", "The house of your neighbors across the street.")
# exit to street is defined in the street zone module

bedroom = Location("Bedroom", "A rather untidy little bedroom. There's clothes lying all over the place. The window is open!")
bedroom.add_extradesc({"clothes"}, "A pile of clothes lies on the floor.")
bedroom.add_extradesc({"window"}, "The bedroom window is open and you see a ladder leading down to the garden.")

garden = Location("Neighbor's Garden", "The garden of your neighbor across the street. "
                                       "Behind some trees to the south you see what appears to be a storage building of a shop.")
garden.add_extradesc({"ladder"}, "It leads up towards a window.")
garden.add_extradesc({"trees", "south", "building"},
                     "The building behind the trees could very well be the meat storage room of the butcher shop in town.")

Exit.connect(garden, ["ladder", "up"], "A ladder leads up towards a window in the house.", None,
             bedroom, ["ladder", "down"], "The ladder that is placed outside of the window provides access down to the garden below.", None)

Exit.connect(garden, ["house", "doors"], "The garden doors are open and lead back to the house.", None,
             neighbors_house, ["garden", "doors"], "The garden doors are open and lead to... the garden.", None)

Exit.connect(neighbors_house, ["up", "stairs"], "Up the stairs is the bedroom.", None,
             bedroom, "stairs", "Stairs lead back to the rest of the house.", None)


# oneway route to get back on the street from the garden:
garden.add_exits([
    Exit(["fence", "street"], "magnolia_st.street2", "You can step over a low fence back onto the street if you wish."),
])
