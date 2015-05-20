# coding=utf-8
"""
The Olde Shoppe in the town.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from tale.shop import ShopBehavior, Shopkeeper
from tale.base import Item, Location, Exit, clone
from tale.npc import NPC
from tale.pubsub import Listener
from tale.items.basic import gameclock, diamond, gem, newspaper
from tale import mud_context


def init(driver):
    # called when zone is first loaded
    pass


# create the Olde Shoppe and its owner
shopinfo = ShopBehavior()
toothpick = Item("toothpick", "pointy wooden toothpick")
toothpick.value = 0.12
shopinfo.forsale.add(toothpick)
shopinfo.banks_money = True
shopkeeper = Shopkeeper("Lucy", "f", short_description="Lucy, the shop owner, is looking happily at her newly arrived customer.")
shopkeeper.money = 14000
shop = Location("Curiosity Shoppe", "A weird little shop. It sells odd stuff.")
shop.insert(shopkeeper, shop)
shop.add_exits([Exit(["door", "out"], "town.lane", "A fancy door provides access back to the lane outside.")])


# provide some items in the shop
clock = clone(gameclock)
clock.value = 500
paper = clone(newspaper)
gem2 = clone(diamond)
gem2.value = 80000
gem3 = clone(gem)
gem3.value = 9055
shopkeeper.init_inventory([gem2, gem3, toothpick])
shopkeeper.set_shop(shopinfo)
shop.insert(clock, shop)
shop.insert(paper, shop)
lamp = Item("lamp", "rather small lamp")
lamp.value = 600


class James(NPC, Listener):
    """The customer trying to sell a Lamp, and helpful as rat deterrent."""
    def pubsub_event(self, topicname, event):
        if topicname[0] == "wiretap-location":
            if "Rat arrives" in event[1]:
                mud_context.driver.defer(2, self.rat_scream, "frown")
                mud_context.driver.defer(4, self.rat_kick)

    def rat_scream(self, action, ctx):
        shopkeeper.do_socialize(action)

    def rat_kick(self, ctx):
        rat = self.location.search_living("rat")
        if rat:
            self.do_socialize("kick rat")
            rat.do_socialize("recoil")
            direction = rat.select_random_move()
            if direction:
                rat.tell_others("{Title} runs away towards the door!")
                rat.move(direction.target, self)
            mud_context.driver.defer(2, self.rat_scream, "smile at " + self.name)

customer = James("James", "m", title="Sir James", description="Sir James is trying to sell something, it looks like a lamp.")
lamp.add_extradesc({"lamp"}, "The lamp looks quite old, but otherwise is rather unremarkable. There is something weird going on with the cord though!")
lamp.add_extradesc({"cord"}, "Even when the lamp doesn't move, the power cord keeps snaking around as if it were alive. How odd.")
customer.insert(lamp, customer)
shop.insert(customer, shop)
shop.get_wiretap().subscribe(customer)
