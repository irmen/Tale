"""
Utility stuff

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

# there's nothing her so far

from __future__ import print_function, division
import random
import os
import time
from . import lang
from .errors import ParseError
from . import rooms


def roll_die(number=1, sides=6):
    """rolls a number (max 20) of dice with configurable number of sides"""
    assert 1 <= number <= 20
    values = [random.randint(1, sides) for _ in range(number)]
    return sum(values), values


def print_object_location(player, obj, container, print_parentheses=True):
    if not container:
        if print_parentheses:
            player.tell("(it's not clear where %s is)" % obj.name)
        else:
            player.tell("It's not clear where %s is." % obj.name)
        return
    if container in player:
        if print_parentheses:
            player.tell("(%s was found in %s, in your inventory)" % (obj.name, container.title))
        else:
            player.tell("%s was found in %s, in your inventory." % (lang.capital(obj.name), container.title))
    elif container is player.location:
        if print_parentheses:
            player.tell("(%s was found in your current location)" % obj.name)
        else:
            player.tell("%s was found in your current location." % lang.capital(obj.name))
    elif container is player:
        if print_parentheses:
            player.tell("(%s was found in your inventory)" % obj.name)
        else:
            player.tell("%s was found in your inventory." % lang.capital(obj.name))
    else:
        if print_parentheses:
            player.tell("(%s was found in %s)" % (obj.name, container.name))
        else:
            player.tell("%s was found in %s." % (lang.capital(obj.name), container.name))


def money_display_fantasy(amount, short=False, zero_msg="nothing"):
    """
    Display amount of money in gold/silver/copper units,
    base unit=silver, 10 silver=1 gold, 0.1 silver=1 copper
    """
    gold, amount = divmod(amount, 10.0)
    silver, copper = divmod(amount, 1.0)
    copper = round(copper * 10.0)
    if short:
        return "%dg/%ds/%dc" % (gold, silver, copper)
    result = []
    if gold:
        result.append("%d gold" % gold)
    if silver:
        result.append("%d silver" % silver)
    if copper:
        result.append("%d copper" % copper)
    if result:
        return lang.join(result)
    return zero_msg


def money_display_modern(amount, short=False, zero_msg="nothing"):
    """
    Display amount of money in modern currency (dollars/cents).
    """
    if short:
        return "$ %.2f" % amount
    dollar, cents = divmod(amount, 1.0)
    cents = round(cents * 100.0)
    result = []
    if dollar:
        result.append("%d dollar" % dollar)
    if cents:
        result.append("%d cent" % cents)
    if result:
        return lang.join(result)
    return zero_msg


def money_to_float_fantasy(coins):
    """Either a dictionary containing the values per cointype, or a string '11g22s33c' is converted to float."""
    if type(coins) is str:
        if not coins:
            raise ValueError("That's not an amount of money.")
        result = 0.0
        while coins:
            c, _, coins = coins.partition("/")
            try:
                if c.endswith("g"):
                    result += float(c[:-1]) * 10.0
                elif c.endswith("s"):
                    result += float(c[:-1])
                elif c.endswith("c"):
                    result += float(c[:-1]) / 10.0
                else:
                    raise ValueError("invalid coin letter")
            except ValueError:
                raise ValueError("That's not an amount of money.")
        return result
    result = coins.get("gold", 0.0) * 10.0
    result += coins.get("silver", 0.0)
    result += coins.get("copper", 0.0) / 10.0
    result += coins.get("coppers", 0.0) / 10.0
    return result


def money_to_float_modern(coins):
    """Either a dictionary containing the values per cointype, or a string '$1234.55' is converted to float."""
    if type(coins) is str:
        if coins.startswith("$"):
            return float(coins[1:])
        else:
            raise ValueError("That's not an amount of money.")
    result = coins.get("dollar", 0.0)
    result += coins.get("dollars", 0.0)
    result += coins.get("cent", 0.0) / 100.0
    result += coins.get("cents", 0.0) / 100.0
    return result


MONEY_WORDS_FANTASY = {"gold", "silver", "copper", "coppers"}
MONEY_WORDS_MODERN = {"dollar", "dollars", "cent", "cents"}

# select one of the above for each (must match ofcourse):
money_display = money_display_modern
money_to_float = money_to_float_modern
MONEY_WORDS = MONEY_WORDS_MODERN


def words_to_money(words, money_to_float=money_to_float, money_words=MONEY_WORDS):
    """Convert a parsed sequence of words to the amount of money it represents (foat)"""
    if len(words) == 1:
        try:
            return money_to_float(words[0])
        except ValueError:
            pass
    elif len(words) == 2:
        try:
            return money_to_float(words[0] + words[1])
        except ValueError:
            pass
    coins = {}
    for word in words:
        if word in money_words:
            # check if all words are either a number (currency) or a moneyword
            amount = None
            for word in words:
                if word in money_words:
                    if amount:
                        if word in coins:
                            raise ParseError("What amount?")
                        coins[word] = amount
                        amount = None
                    else:
                        raise ParseError("What amount?")
                else:
                    try:
                        amount = float(word)
                    except ValueError:
                        raise ParseError("What amount?")
            return money_to_float(coins)
    raise ParseError("That is not an amount of money.")


def get_motd():
    """Read the MOTD and return it and its modification timestamp, if it's not there, return None for both"""
    try:
        with open(os.path.join(os.path.dirname(__file__), "messages", "motd.txt")) as motd:
            message = motd.read().rstrip()
            if not message:
                return None, None
            mtime = os.fstat(motd.fileno()).st_mtime
            mtime = time.asctime(time.localtime(mtime))
            return message, mtime
    except IOError:
        return None, None


def get_banner():
    """Read the banner message, returns None if it's not there"""
    try:
        with open(os.path.join(os.path.dirname(__file__), "messages", "banner.txt")) as banner:
            return banner.read().rstrip() or None
    except IOError:
        return None


def yell_to_nearby_locations(source_location, message):
    """Yells a message to adjacent locations."""
    if source_location.exits:
        nearby_message = "Someone nearby is yelling: %s" % message
        yelled_locations = set()
        for exit in source_location.exits.values():
            if exit.target in yelled_locations:
                continue
            exit.bind(rooms)
            if exit.target is not source_location:
                exit.target.tell(nearby_message)
                yelled_locations.add(exit.target)
                for direction, return_exit in exit.target.exits.items():
                    if return_exit.target is source_location:
                        if direction in {"north", "east", "south", "west", "northeast", "northwest", "southeast",
                                         "southwest", "left", "right", "front", "back"}:
                            direction = "the " + direction
                        elif direction in {"up", "above", "upstairs"}:
                            direction = "above"
                        elif direction in {"down", "below", "downstairs"}:
                            direction = "below"
                        else:
                            continue  # no direction description possible for this exit
                        exit.target.tell("The sound is coming from %s." % direction)
                        break
                else:
                    exit.target.tell("You can't hear where the sound is coming from.")
