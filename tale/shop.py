# coding = utf-8
"""
Shopping and shopkeepers.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)

Shopping related commands will be roughly:

LIST [item type]
   list what the shop has for sale
BUY
  > buy sword        (buy the first sword on the list)
  > buy #3           (buy the third item on the list)
  > buy #4 sword     (buy the fourth sword on the list)
  > buy 10 bread     (buy 10 pieces of bread)
  > buy 10 #2        (buy 10 of the second item on the list)
SELL
  > sell sword       (sell the first sword in your inventory)
  > sell 3 sword     (sell the first three swords in your inventory)
  > sell #3 sword     (sell the third sword in your inventory)

VALUE/APPRAISE  (ask shop keeper how much he is willing to pay for an item)
  > sell sword       (sell the first sword in your inventory)
  > sell 3 sword     (sell the first three swords in your inventory)
  > sell #3 sword    (sell the third sword in your inventory)
  > sell all         (sell everything you have)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import random
import datetime
from .npc import Monster
from .errors import ActionRefused
from . import mud_context
from . import lang


class Shopkeeper(Monster):
    def init(self):
        super(Shopkeeper, self).init()
        self.shop = ShopBehavior()
        self.verbs = {
            "shop": "Go shopping! This shows some information about the shop, and what it has for sale.",
            "list": "Go shopping! This shows some information about the shop, and what it has for sale.",
            "sell": "Sell stuff",
            "buy": "Buy stuff",
            "value": "Ask the shopkeeper about what he's willing to pay for an item",
            "appraise": "Ask the shopkeeper about what he's willing to pay for an item",
        }

    def do_wander(self, ctx):
        # let the shopkeeper wander randomly
        direction = self.select_random_move()
        if direction:
            self.tell_others("{Title} wanders to the %s." % direction.name)
            self.move(direction.target, self)
        ctx.driver.defer(random.randint(20, 60), self.do_wander)

    def validate_open_hours(self, current_time=None):
        time = current_time or mud_context.driver.game_clock.clock.time()
        assert isinstance(time, datetime.time)
        for from_hr, to_hr in self.shop.open_hours:
            from_t = datetime.time(from_hr)
            to_t = datetime.time(to_hr)
            if from_hr < to_hr:
                if from_t <= time < to_t:  # normal order such as 9..17
                    return  # we're open!
            else:
                if from_t <= time or time < to_t:  # reversed order, passes midnight, such as 20..3
                    return  # we're open!
        raise ActionRefused("The shop is currently closed! Come back another time, during opening hours.")

    def handle_verb(self, parsed, actor):
        subj_cap = lang.capital(self.subjective)
        if parsed.verb in ("shop", "list"):
            actor.tell("%s says: \"Welcome to my shop.\"" % lang.capital(self.title))
            open_hrs = lang.join(["%d to %d" % hours for hours in self.shop.open_hours])
            actor.tell("%s continues: \"Our opening hours are:" % subj_cap, open_hrs)
            if self.shop.willbuy:
                actor.tell(", and we specialize in", lang.join(lang.pluralize(word) for word in self.shop.willbuy))
            actor.tell("\"\n")
            self.validate_open_hours()
            # don't show shop.forsale, it is for the code to know what items have limitless supply
            if self.inventory_size == 0:
                actor.tell("%s apologizes, \"I'm sorry, but our stock is all gone for the moment. Come back later.\"" % subj_cap)
                self.do_socialize("shrug at " + actor.name)
            else:
                actor.tell("%s shows you a list of what is in stock at the moment:" % subj_cap, end=True)
                txt = []
                for i, itemname in enumerate(sorted(item.name for item in self.inventory), start=1):
                    txt.append(" %d. %s" % (i, itemname))
                actor.tell(*txt, format=False)
            return True
        elif parsed.verb in ("value", "appraise"):
            print(parsed)  # XXX
            self.validate_open_hours()
            actor.tell("I can tell you what it's worth for me")
            return True
        elif parsed.verb == "buy":
            print(parsed)  # XXX
            self.validate_open_hours()
            actor.tell(self.shop.msg_playercantbuy)
            return True
        elif parsed.verb == "sell":
            print(parsed)  # XXX
            self.validate_open_hours()
            actor.tell(self.shop.msg_shopdoesnotbuy)
            print(1//0) # XXX
            return True
        return False


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
