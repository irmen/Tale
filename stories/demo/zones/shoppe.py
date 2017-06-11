"""
The Olde Shoppe in the town.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from tale.base import Item, Location, Exit, Living
from tale.items.basic import gameclock, diamond, gem, newspaper, woodenYstick, elastic_band
from tale.shop import ShopBehavior
from tale.player import Player
from tale.pubsub import topic
from npcs.town_creatures import ShoppeShopkeeper, CustomerJames


class Shoppe(Location):
    def notify_npc_arrived(self, npc: Living, previous_location: Location) -> None:
        # Using this notification override his is the best way to react to a certain
        # creatures (NPCs) arriving in the shop.
        # You could sniff the location's messages via a wiretap, but that often requires
        # nasty string parsing because they are messages meant for humans really.
        # We use pubsub to notify anyone interested.
        if npc.name == "rat":
            topic("shoppe-rat-arrival").send(npc)

    def notify_player_arrived(self, player: Player, previous_location: Location) -> None:
        # same as above, but for players entering the scene
        topic("shoppe-player-arrival").send(player)


# create the Olde Shoppe and its owner
shopinfo = ShopBehavior()
toothpick = Item("toothpick", "pointy wooden toothpick")
toothpick.value = 0.12
shopinfo.forsale.add(toothpick)   # never run out of toothpicks
shopinfo.banks_money = True
shopkeeper = ShoppeShopkeeper("Lucy", "f", short_descr="Lucy, the shop owner, is looking happily at her newly arrived customer.")
shopkeeper.money = 14000
shop = Shoppe("Curiosity Shoppe", "A weird little shop. It sells odd stuff.")
shop.insert(shopkeeper, None)
shop.get_wiretap().subscribe(shopkeeper)    # the shopkeeper wants to act on certain things happening in her shop.
shop.add_exits([Exit(["door", "out"], "town.lane", "A fancy door provides access back to the lane outside.")])


# provide some items in the shop
clock = gameclock.clone()
clock.value = 500
paper = newspaper.clone()
gem2 = diamond.clone()
gem2.value = 80000
gem3 = gem.clone()
gem3.value = 9055
stick = woodenYstick.clone()
elastic = elastic_band.clone()
shopkeeper.init_inventory([gem2, gem3, toothpick, stick, elastic])
shopkeeper.set_shop(shopinfo)


# some stuff and people that are present in the shoppe
shop.insert(clock, None)
shop.insert(paper, None)
lamp = Item("lamp", "rather small lamp")
lamp.value = 600
customer = CustomerJames("James", "m", title="Sir James", descr="Sir James is trying to sell something, it looks like a lamp.")
lamp.add_extradesc({"lamp"}, "The lamp looks quite old, but otherwise is rather unremarkable."
                             " There is something weird going on with the cord though!")
lamp.add_extradesc({"cord"}, "Even when the lamp doesn't move, the power cord keeps snaking around as if it were alive. How odd.")
customer.insert(lamp, customer)
shop.insert(customer, None)


# shopkeeper and the customer want to act on creatures entering the shop:
topic("shoppe-rat-arrival").subscribe(shopkeeper)
topic("shoppe-rat-arrival").subscribe(customer)
topic("shoppe-player-arrival").subscribe(shopkeeper)
topic("shoppe-player-arrival").subscribe(customer)
