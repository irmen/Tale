# coding = utf-8
"""
Shopping and shopkeepers.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
from .npc import Monster
import random


class Shopkeeper(Monster):
    def init(self):
        super(Shopkeeper, self).init()
        self.shop = ShopBehavior()

    def do_wander(self, ctx):
        # let the shopkeeper wander randomly
        direction = self.select_random_move()
        if direction:
            self.tell_others("{Title} wanders to the %s." % direction.name)
            self.move(direction.target, self)
        ctx.driver.defer(random.randint(20, 60), self.do_wander)


class ShopBehavior(object):
    """the data describing the behavior of a particular shop"""
    shopkeeper_vnum = None     # used for circle data to designate the shopkeeper belonging to this shop
    banks_money = False
    will_fight = False
    buyprofit = 1.6
    sellprofit = 0.3
    open_hours = [(9, 17), (18, 22)]
    forsale = set()     # items the shop always sells no matter how many are bought
    msg_playercantafford = "No cash, no goods!"
    msg_playercantbuy = "We don't sell that."
    msg_playercantsell = "I don't think you have that."
    msg_shopboughtitem = "Thank-you very much.  Here are your %d coins as payment."   # @todo money speller
    msg_shopcantafford = "I can't afford to buy anything, I'm only a poor peddler."
    msg_shopdoesnotbuy = "I don't stock that stuff.  Try another shop."
    msg_shopsolditem = "Here you go.  That'll be... %d coins."   # @todo money speller
    msg_temper = "The shopkeeper smokes his joint."
    willbuy = set()
    wontdealwith = set()
