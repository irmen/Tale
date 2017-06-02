"""
The Olde Shoppe in the town.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from typing import Any

from tale import mud_context, util
from tale.base import Item, Location, Exit, Living
from tale.items.basic import gameclock, diamond, gem, newspaper
from tale.pubsub import Listener, TopicNameType
from tale.shop import ShopBehavior, Shopkeeper


# create the Olde Shoppe and its owner
shopinfo = ShopBehavior()
toothpick = Item("toothpick", "pointy wooden toothpick")
toothpick.value = 0.12
shopinfo.forsale.add(toothpick)
shopinfo.banks_money = True
shopkeeper = Shopkeeper("Lucy", "f", short_description="Lucy, the shop owner, is looking happily at her newly arrived customer.")
shopkeeper.money = 14000
shop = Location("Curiosity Shoppe", "A weird little shop. It sells odd stuff.")
shop.insert(shopkeeper, None)
shop.add_exits([Exit(["door", "out"], "town.lane", "A fancy door provides access back to the lane outside.")])


# provide some items in the shop
clock = gameclock.clone()
clock.value = 500
paper = newspaper.clone()
gem2 = diamond.clone()
gem2.value = 80000
gem3 = gem.clone()
gem3.value = 9055
shopkeeper.init_inventory([gem2, gem3, toothpick])
shopkeeper.set_shop(shopinfo)
shop.insert(clock, None)
shop.insert(paper, None)
lamp = Item("lamp", "rather small lamp")
lamp.value = 600


class James(Living, Listener):
    """The customer trying to sell a Lamp, and helpful as rat deterrent."""
    def pubsub_event(self, topicname: TopicNameType, event: Any) -> Any:
        if topicname[0] == "wiretap-location":
            if "Rat arrives" in event[1]:
                mud_context.driver.defer(2, self.rat_scream, "frown")
                mud_context.driver.defer(4, self.rat_kick)

    def rat_scream(self, action: str, ctx: util.Context) -> None:
        shopkeeper.do_socialize(action)

    def rat_kick(self, ctx: util.Context) -> None:
        rat = self.location.search_living("rat")
        if rat:
            self.do_socialize("kick rat")
            rat.do_socialize("recoil")
            direction = rat.select_random_move()
            if direction:
                rat.tell_others("{Actor} runs away towards the door!")
                rat.move(direction.target, self)
            mud_context.driver.defer(2, self.rat_scream, "smile at " + self.name)


customer = James("James", "m", title="Sir James", description="Sir James is trying to sell something, it looks like a lamp.")
lamp.add_extradesc({"lamp"}, "The lamp looks quite old, but otherwise is rather unremarkable."
                             " There is something weird going on with the cord though!")
lamp.add_extradesc({"cord"}, "Even when the lamp doesn't move, the power cord keeps snaking around as if it were alive. How odd.")
customer.insert(lamp, customer)
shop.insert(customer, None)
shop.get_wiretap().subscribe(customer)
