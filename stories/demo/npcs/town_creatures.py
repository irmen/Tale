"""
Creatures living in the central town.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import random
from typing import Any

from tale import lang, util, mud_context
from tale.base import Living, ParseResult
from tale.util import call_periodically
from tale.shop import Shopkeeper
from tale.pubsub import Listener, TopicNameType


class VillageIdiot(Living):
    @call_periodically(5, 20)
    def do_drool(self, ctx: util.Context) -> None:
        if random.random() < 0.3:
            self.location.tell("%s drools. Yuck." % lang.capital(self.title))
        else:
            target = random.choice(list(self.location.livings))
            if target is self:
                self.location.tell("%s drools on %sself." % (lang.capital(self.title), self.objective))
            else:
                title = lang.capital(self.title)
                self.location.tell("%s drools on %s." % (title, target.title),
                                   specific_targets={target}, specific_target_msg="%s drools on you." % title)


class TownCrier(Living):
    @call_periodically(20, 40)
    def do_cry(self, ctx: util.Context) -> None:
        self.tell_others("{Actor} yells: welcome everyone!")
        self.location.message_nearby_locations("Someone nearby is yelling: welcome everyone!")

    def notify_action(self, parsed: ParseResult, actor: Living) -> None:
        greet = False
        if parsed.verb in ("hi", "hello"):
            greet = True
        elif parsed.verb == "say":
            if "hello" in parsed.args or "hi" in parsed.args:
                greet = True
        elif parsed.verb == "greet" and self in parsed.who_info:
            greet = True
        if greet:
            self.tell_others("{Actor} says: \"Hello there, %s.\"" % actor.title)


class WalkingRat(Living):
    def init(self) -> None:
        super().init()
        self.aggressive = False

    @call_periodically(5, 15)
    def do_idle_action(self, ctx: util.Context) -> None:
        if random.random() < 0.5:
            self.tell_others("{Actor} wiggles %s tail." % self.possessive)
        else:
            self.tell_others("{Actor} sniffs around and moves %s whiskers." % self.possessive)

    @call_periodically(10, 20)
    def do_random_move(self, ctx: util.Context) -> None:
        direction = self.select_random_move()
        if direction:
            self.move(direction.target, self, direction_name=direction.name)


class ShoppeShopkeeper(Shopkeeper, Listener):
    def pubsub_event(self, topicname: TopicNameType, event: Any) -> Any:
        if topicname == "shoppe-rat-arrival":
            # rat arrived in the shop
            mud_context.driver.defer(2, self.rat_event, "glance at rat")
        elif topicname == "shoppe-player-arrival":
            # player arrived in the shop
            mud_context.driver.defer(3, self.do_socialize, "welcome " + event.name)
        elif topicname[0] == "wiretap-location":
            if "kicks rat" in event[1]:
                # be happy about someone that is kicking the vermin!
                name = event[1].split("kicks rat")[0].strip()
                living = self.location.search_living(name)
                if living:
                    mud_context.driver.defer(2, self.rat_event, "smile " + living.name)

    def rat_event(self, action: str, ctx: util.Context) -> None:
        if "rat" not in action or self.location.search_living("rat"):
            self.do_socialize(action)


class CustomerJames(Living, Listener):
    """The customer in the shoppe, trying to sell a Lamp, and helpful as rat deterrent."""
    def pubsub_event(self, topicname: TopicNameType, event: Any) -> Any:
        if topicname == "shoppe-rat-arrival":
            # rat arrived in the shop, we're going to kick it out!
            mud_context.driver.defer(4, self.rat_kick)
        elif topicname == "shoppe-player-arrival":
            # player arrived in the shop.
            mud_context.driver.defer(5, self.do_socialize, "nod " + event.name)

    def rat_kick(self, ctx: util.Context) -> None:
        rat = self.location.search_living("rat")
        if rat:
            self.do_socialize("kick rat")
            rat.do_socialize("recoil")
            direction = rat.select_random_move()
            if direction:
                rat.tell_others("{Actor} runs away towards the door!")
                rat.move(direction.target, self, direction_name=direction.name)
