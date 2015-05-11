# coding=utf-8
"""
Language processing related operations.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import re
import bisect
from .tio import vfs

# genders are m,f,n
SUBJECTIVE = {"m": "he", "f": "she", "n": "it"}
POSSESSIVE = {"m": "his", "f": "her", "n": "its"}
OBJECTIVE = {"m": "him", "f": "her", "n": "it"}
GENDERS = {"m": "male", "f": "female", "n": "neuter"}


def join(words, conj="and"):
    """join a list of words to 'a,b,c, and e'"""
    words = list(words)
    if not words:
        return ""
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return "%s %s %s" % (words[0], conj, words[1])
    return "%s, %s %s" % (", ".join(words[:-1]), conj, words[-1])


__a_exceptions = {
    "universe": "a",
    "university": "a",
    "user": "a",
    "hour": "an"
    # probably more, but these will have to do for now
}


def a(word):
    """a or an? simplistic version: if the word starts with aeiou, returns an, otherwise a"""
    if not word:
        return ""
    if word.startswith(("a ", "an ")):
        return word
    firstword = word.split(None, 1)[0]
    exception = __a_exceptions.get(firstword.lower(), None)
    if exception:
        return exception + " " + word
    elif word.startswith(('a', 'e', 'i', 'o', 'u')):
        return "an " + word
    return "a " + word


def reg_a_exceptions(exceptions):
    __a_exceptions.update(exceptions)


def fullstop(sentence, punct="."):
    """adds a fullstop to the end of a sentence if needed"""
    sentence = sentence.rstrip()
    if sentence.endswith(('!', '?', '.', ';', ':', '-', '=')):
        return sentence
    return sentence + punct


# adverbs are stored in a datafile next to this module
ADVERB_LIST = sorted(vfs.internal_resources["soul_adverbs.txt"].data.splitlines())   # keep the list for prefix search
ADVERBS = frozenset(ADVERB_LIST)


def adverb_by_prefix(prefix, amount=5):
    """
    Return a list of adverbs starting with the given prefix, up to the given amount
    Uses binary search in the sorted adverbs list, O(log n)
    """
    i = bisect.bisect_left(ADVERB_LIST, prefix)
    if i >= len(ADVERB_LIST):
        return []
    elif ADVERB_LIST[i].startswith(prefix):
        j = i + 1
        amount = min(amount, len(ADVERB_LIST) - i)   # avoid reading past the end of the list
        while amount > 1 and ADVERB_LIST[j].startswith(prefix):
            j += 1
            amount -= 1
        return ADVERB_LIST[i:j]
    else:
        return []


def possessive_letter(name):
    if not name:
        return ""
    if name[-1] in ('s', 'z', 'x'):
        return "'s"        # tess's foot
    elif name.endswith(" own"):
        return ""         # your own...
    else:
        return "'s"        # mark's foot


def possessive(name):
    return name + possessive_letter(name)


def capital(string):
    if string:
        string = string[0].upper() + string[1:]
    return string


def fullverb(verb):
    """return the full verb: shoot->shooting, poke->poking"""
    if verb[-1] == "e":
        return verb[:-1] + "ing"
    return verb + "ing"


def split(string):
    """
    Split a string on whitespace, but keeps words enclosed in quotes (' or ") together.
    The quotes themselves are stripped out.
    """
    def removequotes(word):
        if word.startswith(('"', "'")) and word.endswith(('"', "'")):
            return word[1:-1].strip()
        return word
    return [removequotes(p) for p in re.split("( |\\\".*?\\\"|'.*?')", string) if p.strip()]


__number_words = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"
]


def spell_number(number):
    result = ""
    if number < 0:
        result = "minus "
        number = -number
    if number > 20:
        return result + str(number)
    if number is int:
        return result + __number_words[number]
    int_number = int(number)
    fraction = number - int_number
    if fraction == 0:
        fraction_txt = ""
    elif fraction == 0.5:
        fraction_txt = " and a half"
    else:
        return str(number)  # can't spell fractions other than 0.5
    return result + __number_words[int_number] + fraction_txt


__plural_irregularities = {
    "mouse": "mice",
    "child": "children",
    "person": "people",
    "man": "men",
    "woman": "women",
    "foot": "feet",
    "goose": "geese",
    "tooth": "teeth",
    "aircraft": "aircraft",
    "fish": "fish",
    "headquarters": "headquarters",
    "sheep": "sheep",
    "species": "species",
    "cattle": "cattle",
    "scissors": "scissors",
    "trousers": "trousers",
    "pants": "pants",
    "tweezers": "tweezers",
    "congratulations": "congratulations",
    "pyjamas": "pyjamas",
    "photo": "photos",
    "piano": "pianos",
    # probably more, but these will have to do for now
}


def pluralize(word, amount=2):
    if amount == 1:
        return word
    if word in __plural_irregularities:
        return __plural_irregularities[word]
    if word.endswith("is"):
        return word[:-2] + "es"
    if word.endswith("z"):
        return word + "zes"
    if word.endswith("s") or word.endswith("ch") or word.endswith("x") or word.endswith("sh"):
        return word + "es"
    if word.endswith("y"):
        return word[:-1] + "ies"
    if word.endswith("f"):
        return word[:-1] + "ves"
    if word.endswith("fe"):
        return word[:-2] + "ves"
    if word.endswith("o") and len(word) > 1 and word[-2] not in "aeiouy":
        return word + "es"
    return word + "s"


def yesno(value):
    value = value.lower() if value else ""
    if value in {"y", "yes", "sure", "yep", "yeah", "yessir", "sure thing"}:
        return True
    if value in {"n", "no", "nope", "no way", "hell no"}:
        return False
    raise ValueError("That is not an understood yes or no.")


def validate_gender(value):
    value = value.lower() if value else ""
    if value in GENDERS:
        return value
    if len(value) > 1:
        if value[0] in GENDERS and GENDERS[value[0]] == value:
            return value
    raise ValueError("That is not a valid gender.")
