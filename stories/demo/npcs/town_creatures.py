"""
Creatures living in the central town.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import random

from tale import lang, util
from tale.base import Living
from tale.parseresult import ParseResult
from tale.util import call_periodically


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
        self.tell_others("{Title} yells: welcome everyone!")
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
            self.tell_others("{Title} says: \"Hello there, %s.\"" % actor.title)


class WalkingRat(Living):
    def init(self) -> None:
        super().init()
        self.aggressive = True

    @call_periodically(5, 15)
    def do_idle_action(self, ctx: util.Context) -> None:
        if random.random() < 0.5:
            self.tell_others("{Title} wiggles %s tail." % self.possessive)
        else:
            self.tell_others("{Title} sniffs around and moves %s whiskers." % self.possessive)

    @call_periodically(10, 20)
    def do_random_move(self, ctx: util.Context) -> None:
        direction = self.select_random_move()
        if direction:
            self.move(direction.target, self)
