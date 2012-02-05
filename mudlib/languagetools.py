import inflect

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
