import inflect
import os
import bisect

inflecter = inflect.engine()

# genders are m,f,n
SUBJECTIVE = { "m": "he",  "f": "she", "n": "it"  }
POSSESSIVE = { "m": "his", "f": "her", "n": "its" }
OBJECTIVE  = { "m": "him", "f": "her", "n": "it"  }

# join a list of words to "a,b,c,d and e"
join = inflecter.join

# a or an?
a = inflecter.a

# spell out a number
number_to_words = inflecter.number_to_words


def fullstop(sentence, punct="."):
    sentence = sentence.rstrip()
    if sentence[-1] not in "!?.,;:-=":
        return sentence + punct
    else:
        return sentence


# adverbs are stored in a datafile next to this module
with open(os.path.join(os.path.dirname(__file__), "soul_adverbs.txt")) as adverbsfile:
    ADVERB_LIST = adverbsfile.read().splitlines()     # keep the list for prefix search
    ADVERBS = frozenset(ADVERB_LIST)


def adverb_by_prefix(prefix, amount=5):
    """
    Return a list of adverbs starting with the given prefix, up to the given amount
    """
    i = bisect.bisect_left(ADVERB_LIST, prefix)
    if i >= len(ADVERB_LIST):
        return []
    elif ADVERB_LIST[i].startswith(prefix):
        j = i + 1
        while amount > 1 and ADVERB_LIST[j].startswith(prefix):
            j += 1
            amount -= 1
        return ADVERB_LIST[i:j]
    else:
        return []


def possessive_letter(name):
    if not name:
        return ""
    if name[-1] in ('s','z','x'):
        return "'"        # tess' foot
    elif name.endswith(" own"):
        return ""         # your own...
    else:
        return "s"        # marks foot
