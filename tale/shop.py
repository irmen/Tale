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
  > sell #3 sword    (sell the third sword in your inventory)
  > sell 3 sword     (sell the first three swords in your inventory)

VALUE/APPRAISE  (ask shop keeper how much he is willing to pay for an item)
  > value sword      (appraise the first sword in your inventory)
  > value #3 sword   (appraise the third sword in your inventory)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import random
import datetime
from .npc import NPC
from .base import Item
from .errors import ActionRefused, ParseError
from . import mud_context
from . import lang


class Shopkeeper(NPC):
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

    def validate_open_hours(self, actor=None, current_time=None):
        if actor and "wizard" in actor.privileges:
            return   # for wizards, shops are always open
        if current_time is None:
            current_time = mud_context.driver.game_clock.clock.time()
        assert isinstance(current_time, datetime.time)
        for from_hr, to_hr in self.shop.open_hours:
            from_t = datetime.time(from_hr)
            to_t = datetime.time(to_hr)
            if from_hr < to_hr:
                if from_t <= current_time < to_t:  # normal order such as 9..17
                    return  # we're open!
            else:
                if from_t <= current_time or current_time < to_t:  # reversed order, passes midnight, such as 20..3
                    return  # we're open!
        raise ActionRefused("The shop is currently closed! Come back another time, during opening hours.")

    def _parse_item(self, parsed, actor):
        if len(parsed.who_info) != 1:
            raise ParseError("I don't understand what single item you're talking about.")
        item, info = parsed.who_info.popitem()
        if item not in actor:
            raise ActionRefused(self.shop.msg_playercantsell or "You don't have that.")
        if not isinstance(item, Item):
            raise ActionRefused("You can't sell %s, %s is not trade goods!" % (item.objective, item.subjective))
        designator = info.previous_word or ""
        return item, designator

    def _sorted_inventory(self):
        return self.inventory

    def handle_verb(self, parsed, actor):
        self.validate_open_hours(actor)
        subj_cap = lang.capital(self.subjective)
        if parsed.verb in ("shop", "list"):
            open_hrs = lang.join(["%d to %d" % hours for hours in self.shop.open_hours])
            actor.tell("%s says: \"Welcome. Our opening hours are:" % lang.capital(self.title), open_hrs)
            if "wizard" in actor.privileges:
                actor.tell(" (but for wizards, we're always open)")
            if self.shop.willbuy:
                actor.tell(", and we specialize in", lang.join(lang.pluralize(word) for word in self.shop.willbuy))
            actor.tell("\"\n", end=True)
            # don't show shop.forsale, it is for the code to know what items have limitless supply
            if self.inventory_size == 0:
                actor.tell("%s apologizes, \"I'm sorry, but our stuff is all gone for the moment. Come back later.\"" % subj_cap)
                self.do_socialize("shrug at " + actor.name)
            else:
                actor.tell("%s shows you a list of what is in stock at the moment:" % subj_cap, end=True)
                txt = ["<ul>  # <dim>|</><ul>  item                        <dim>|</><ul> price     </>"]
                for i, item in enumerate(self._sorted_inventory(), start=1):
                    price = item.cost * self.shop.sellprofit
                    txt.append("%3d. %-30s  %s" % (i, item.title, mud_context.driver.moneyfmt.display(price)))
                actor.tell(*txt, format=False)
            return True

        elif parsed.verb in ("value", "appraise"):
            item, designator = self._parse_item(parsed, actor)
            if designator:
                raise ParseError("designator not yet supported")   # @todo handle designator
            if item.cost <= 0:
                actor.tell("%s tells you it's worthless." % lang.capital(self.title))
                return True
            price = item.cost * self.shop.buyprofit
            value_str = mud_context.driver.moneyfmt.display(price)
            actor.tell("%s appraises the %s." % (lang.capital(self.title), item.name))
            actor.tell("%s tells you: \"I'll give you %s for it.\"" % (lang.capital(self.subjective), value_str))
            return True

        elif parsed.verb == "buy":
            item, designator = None, None  # @todo buy from shop inventory
            if designator:
                raise ParseError("designator not yet supported")   # @todo handle designator
            actor.tell(self.shop.msg_playercantbuy)
            # @todo check banks_money
            self.do_socialize("thank " + actor.name)
            return True

        elif parsed.verb == "sell":
            item, designator = self._parse_item(parsed, actor)
            if designator:
                raise ParseError("designator not yet supported")   # @todo handle designator
            if item.cost <= 0:
                actor.tell("%s tells you: \"%s\"" % (lang.capital(self.title), self.shop.msg_shopdoesnotbuy))
                if self.shop.action_temper:
                    self.do_socialize("%s %s" % (self.shop.action_temper, actor.name))
                return True
            # @todo check wontdealwith
            # @todo check item type
            # check money
            price = item.cost * self.shop.buyprofit
            limit = self.money * 0.75   # shopkeeper should not spend more than 75% of his money on a single sale
            if price >= limit:
                actor.tell("%s says: \"%s\"" % (lang.capital(self.title), self.shop.msg_shopcantafford))
                return True
            item.move(self, actor)
            actor.money += price
            self.money -= price
            assert self.money >= 0.0
            actor.tell("You've sold the %s." % item.name)
            if self.shop.msg_shopboughtitem:
                actor.tell("%s says: \"%s\"" % (lang.capital(self.title), self.shop.msg_shopboughtitem % price))   # @todo money format
            else:
                actor.tell("%s gave you %s for it." % (lang.capital(self.title), mud_context.driver.moneyfmt.display(price)))
            self.do_socialize("thank " + actor.name)
            return True

        else:
            # unrecognised verb
            return False


class ShopBehavior(object):
    """the data describing the behavior of a particular shop"""
    shopkeeper_vnum = None     # used for circle data to designate the shopkeeper belonging to this shop
    banks_money = False
    will_fight = False
    _buyprofit = 0.3     # price factor when shop buys item
    _sellprofit = 1.6    # price factor when shop sells item
    open_hours = [(9, 17), (18, 22)]
    forsale = set()     # items the shop always sells no matter how many are bought
    msg_playercantafford = "No cash, no goods!"
    msg_playercantbuy = "We don't sell that."
    msg_playercantsell = "I don't think you have that."
    msg_shopboughtitem = "Thank-you very much.  Here are your %d coins as payment."   # @todo money speller
    msg_shopcantafford = "I can't afford to buy anything, I'm only a poor peddler."
    msg_shopdoesnotbuy = "I don't buy that stuff.  Try another shop."
    msg_shopsolditem = "Here you go.  That'll be... %d coins."   # @todo money speller
    action_temper = "smoke"
    willbuy = set()
    wontdealwith = set()

    @property
    def buyprofit(self):
        return self._buyprofit

    @buyprofit.setter
    def buyprofit(self, value):
        assert value <= 1.0
        self._buyprofit = value

    @property
    def sellprofit(self):
        return self._sellprofit

    @sellprofit.setter
    def sellprofit(self, value):
        assert value >= 1.0
        self._sellprofit = value
