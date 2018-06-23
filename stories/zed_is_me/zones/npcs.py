"""
NPCS in the game.
"""
import random
from typing import Optional
from tale.base import Living, Door, ParseResult, Item
from tale.player import Player
from tale.util import call_periodically, Context
from tale.errors import TaleError, ActionRefused, ParseError, StoryCompleted
from tale import lang, mud_context


# the pharmacy sales person
class Apothecary(Living):
    pills_price = 20.0   # don't randomly change this, there's a fixed amount of money lying in the game...

    def init(self):
        super().init()
        self.verbs["haggle"] = "Haggles with a person to make them sell you something below the actual price. " \
                               "Provide the price you're offering."
        self.verbs["bargain"] = "Try to make a person sell you something below the actual price. " \
                                "Provide the price you're offering."
        self.verbs["buy"] = "Purchase something."

    @property
    def description(self) -> str:
        if self.search_item("pills", include_location=False):
            return "%s looks scared, and clenches a small bottle in %s hands." % (lang.capital(self.subjective), self.possessive)
        return "%s looks scared." % self.subjective

    @description.setter
    def description(self, value: str) -> None:
        raise TaleError("cannot set dynamic description")

    def handle_verb(self, parsed: ParseResult, actor: Living) -> bool:
        pills = self.search_item("pills", include_location=False)
        if parsed.verb in ("bargain", "haggle"):
            if not parsed.args:
                raise ParseError("For how much money do you want to haggle?")
            if not pills:
                raise ActionRefused("It is no longer available for sale.")
            amount = mud_context.driver.moneyfmt.parse(parsed.args)
            price = mud_context.driver.moneyfmt.display(self.pills_price)
            if amount < self.pills_price / 2:
                actor.tell("%s glares angrily at you and says, \"No way! I want at least half the original price! "
                           "Did't I tell you? They were %s!\"" % (lang.capital(self.title), price))
                raise ActionRefused()
            self.do_buy_pills(actor, pills, amount)
            return True
        if parsed.verb == "buy":
            if not parsed.args:
                raise ParseError("Buy what?")
            if "pills" in parsed.args or "bottle" in parsed.args or "medicine" in parsed.args:
                if not pills:
                    raise ActionRefused("It is no longer available for sale.")
                self.do_buy_pills(actor, pills, self.pills_price)
                return True
            if pills:
                raise ParseError("There's nothing left to buy in the shop, except for the pills the apothecary is holding.")
            else:
                raise ParseError("There's nothing left to buy.")
        return False

    def do_buy_pills(self, actor: Living, pills: Item, price: float) -> None:
        if actor.money < price:
            raise ActionRefused("You don't have enough money!")
        actor.money -= price
        self.money += price
        pills.move(actor, self)
        price_str = mud_context.driver.moneyfmt.display(price)
        actor.tell("After handing %s the %s, %s gives you the %s." % (self.objective, price_str, self.subjective, pills.title))
        self.tell_others("{Actor} says: \"Here's your medicine, now get out of here!\"")

    def notify_action(self, parsed: ParseResult, actor: Living) -> None:
        if actor is self or parsed.verb in self.verbs:
            return  # avoid reacting to ourselves, or reacting to verbs we already have a handler for
        # react on mentioning the medicine
        if "medicine" in parsed.unparsed or "pills" in parsed.unparsed or "bottle" in parsed.unparsed:
            if self.search_item("pills", include_location=False):  # do we still have the pills?
                price = mud_context.driver.moneyfmt.display(self.pills_price)
                self.tell_others("{Actor} clenches the bottle %s's holding even tighter. %s says: "
                                 "\"You won't get them for free! They will cost you %s!\""
                                 % (self.subjective, lang.capital(self.subjective), price))
            else:
                self.tell_others("{Actor} says: \"Good luck with it!\"")
        if random.random() < 0.5:
            actor.tell("%s glares at you." % lang.capital(self.title))


# Peter, the player's friend. They have to escape together.
class Friend(Living):
    @call_periodically(10.0, 20.0)
    def say_something(self, ctx: Context) -> None:
        door_open = any(d.opened for d in self.location.exits.values() if isinstance(d, Door))
        if door_open:
            self.do_socialize("say \"Finally someone who rescued me! Thank you so much.\"")
        else:
            self.do_command_verb("yell \"Help me, I'm locked in\"", ctx)

    @call_periodically(5.0, 20.0)
    def say_something_medicine(self, ctx: Context) -> None:
        living_with_medicine = None
        for living in self.location.livings:
            if living is not self and living.search_item("pills", include_location=False):
                living_with_medicine = living
                break
        if living_with_medicine:
            self.do_socialize("say \"Oh, wonderful, you have my medicine! Now let's get out of here!\"")
            self.tell_others("{Actor} starts following you.", target=living_with_medicine)
            self.following = living_with_medicine
        else:
            self.do_socialize("say \"Have you forgotten about my illness? I am not able to leave without my medicine! "
                              "Please go find it first.\"")

    def notify_action(self, parsed: ParseResult, actor: Living) -> None:
        if actor is self or parsed.verb in self.verbs:
            return  # avoid reacting to ourselves, or reacting to verbs we already have a handler for
        if self in parsed.who_info:
            self.do_socialize("smile " + actor.name)
        if self in parsed.who_info or parsed.verb in ("say", "greet", "hi"):
            self.say_something_medicine(Context(mud_context.driver, None, None, None))

    def allow_give_item(self, item: Item, actor: Optional[Living]) -> None:
        if item.name == "pills":
            self.do_socialize("say \"Keep the bottle with you, I'll ask when I need it. Let us just leave from this place!\"")
            raise ActionRefused()
        else:
            raise ActionRefused("%s doesn't want %s." % (lang.capital(self.title), item.title))


# A strange person wandering about the town, can kill the player if she's not careful to flee/run.
class Wanderer(Living):
    def init(self):
        self.attacking = False

    @call_periodically(10, 20)
    def do_wander(self, ctx: Context) -> None:
        if not self.attacking:
            # Let the mob wander randomly.
            direction = self.select_random_move()
            if direction:
                self.move(direction.target, self, direction_names=direction.names)

    @call_periodically(4, 10)
    def do_attack(self, ctx: Context) -> None:
        if not self.attacking:
            for liv in self.location.livings:
                if isinstance(liv, Player):
                    self.start_attack(liv)
                    liv.tell("It may be a good idea to run away!")
                    self.attacking = True
                    ctx.driver.defer(5, self.kill_player, liv)      # give player a moment to react to the attack
                    break

    def kill_player(self, player: Player, ctx: Context) -> None:
        # player can only be killed if she is still here, obviously
        if self.attacking and player in self.location.livings:
            player.tell_text_file(ctx.resources["messages/completion_failed.txt"])
            raise StoryCompleted
        self.attacking = False
