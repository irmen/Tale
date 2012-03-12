# -*- coding: utf-8 -*-
"""
A player's 'soul', which provides a lot of possible emotes (verbs).

Written by Irmen de Jong (irmen@razorvine.net)
Based on ancient soul.c v1.2 written in LPC by profezzorn@nannymud (Fredrik Hübinette)
Only the verb table is more or less intact (with some additions and fixes).
The verb parsing and message generation have been rewritten.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import re
from . import languagetools as lang
from .errors import ParseError


class SoulException(Exception):
    """Internal error, should never happen. Not intended for user display."""
    pass


class UnknownVerbException(SoulException):
    """
    The soul doesn't recognise the verb that the user typed.
    The engine can and should search for other places that define this verb first.
    If nothing recognises it, this error should be shown to the user in a nice way.
    """
    def __init__(self, verb, words, qualifier):
        super(UnknownVerbException, self).__init__(verb)
        self.verb = verb
        self.words = words
        self.qualifier = qualifier


DEFA = 1  # adds HOW+AT   (you smile happily at Fritz)
PREV = 2  # adds a WHO+HOW   (you ignore Fritz completely)
PHYS = 3  # adds a WHO+HOW+WHERE  (you stroke Anna softly on the shoulder)
SHRT = 4  # just adds a HOW, won't show a target  (you sweat profusely)
PERS = 5  # provide an alternate WHO text  (you shiver with fear / you fear Fritz)
SIMP = 6  # don't add stuff, the text itself has all escapes  (you snap your fingers at Fritz)
DEUX = 7  # a room text is provided with alternate spelling or wording  (you fall down and play dead / Player falls to the ground, dead)
QUAD = 8  # like DEUX, but also provides two more texts for when a target is used
FULL = 9  # not used yet

# escapes used: AT, HOW, IS, MSG, MY, POSS, SUBJ, WHAT, WHERE, WHO, YOUR
# adverbs tuple: (adverb, message, where)
# if message starts with a ' (single quote), it will appear *without quotes*.

VERBS = {
"flex":      ( DEUX, None, "flex \nYOUR muscles \nHOW", "flexes \nYOUR muscles \nHOW" ),
"snort":     ( SIMP, None, "snort$ \nHOW \nAT", "at" ),
"pant":      ( SIMP, ( "heavily", ), "pant$ \nHOW \nAT", "at" ),
"hmm":       ( SIMP, None, "hmm$ \nHOW \nAT", "at" ),
"ack":       ( SIMP, None, "ack$ \nHOW \nAT", "at" ),
"guffaw":    ( SIMP, None, "guffaw$ \nHOW \nAT", "at" ),
"raise":     ( SIMP, None, " \nHOW raise$ an eyebrow \nAT", "at" ),
"snap":      ( SIMP, None, "snap$ \nYOUR fingers \nAT", "at" ),
"lust":      ( DEFA, None, "", "for"),
"burp":      ( DEFA, ( "rudely", ), "", "at" ),
"bump":      ( DEFA, ( "clumsily", ), "", "into"),
"wink":      ( DEFA, ( "suggestively", ), "", "at" ),
"smile":     ( DEFA, ( "happily", ), "", "at" ),
"yawn":      ( DEFA, None, "", "at" ),
"swoon":     ( DEFA, ( "romantically", ), "", "at" ),
"sneer":     ( DEFA, ( "disdainfully", ), "", "at" ),
"talk":      ( SIMP, None, "want$ to talk \nAT \nHOW", "to" ),
"beam":      ( DEFA, None, "", "at" ),
"point":     ( DEFA, None, "", "at" ),
"grin":      ( DEFA, ( "evilly", ), "", "at" ),
"laugh":     ( DEFA, None, "", "at" ),
"nod":       ( DEFA, ( "solemnly", ), "", "at" ),
"wave":      ( DEFA, ( "happily", ), "", "at" ),
"cackle":    ( DEFA, ( "gleefully", ), "", "at" ),
"chuckle":   ( DEFA, None, "", "at" ),
"bow":       ( DEFA, None, "", "to" ),
"surrender": ( DEFA, None, "", "to" ),
"sit":       ( DEFA, ( "down", ), "", "in front of" ),
"stand":     ( DEFA, ( "up", ), "", "in front of" ),
"capitulate": ( DEFA, ( "unconditionally", ), "", "to" ),
"glare":     ( DEFA, ( "stonily", ), "", "at" ),
"giggle":    ( DEFA, ( "merrily", ), "", "at" ),
"groan":     ( DEFA, None, "", "at" ),
"grunt":     ( DEFA, None, "", "at" ),
"growl":     ( DEFA, None, "", "at" ),
"breathe":   ( DEFA, ( "heavily", ), "", "at" ),
"argh":      ( DEFA, None, "", "at" ),
"scowl":     ( DEFA, ( "darkly", ), "", "at" ),
"snarl":     ( DEFA, None, "", "at" ),
"recoil":    ( DEFA, ( "with fear", ), "", "from" ),
"moan":      ( DEFA, None, "", "at" ),
"howl":      ( DEFA, ( "in pain", ), "", "at" ),
"puke":      ( DEFA, None, "", "on" ),
"drool":     ( DEFA, None, "", "on" ),
"sneeze":    ( DEFA, ( "loudly", ), "", "at" ),
"spit":      ( DEFA, None, "", "on" ),
"stare":     ( DEFA, None, "", "at" ),
"whistle":   ( DEFA, ( "appreciatively", ), "", "at" ),
"applaud":   ( DEFA, None, "", "" ),
"leer":      ( DEFA, None, "", "at" ),
"agree":     ( DEFA, None, "", "with" ),
"believe":   ( PERS, None, "believe$ in \nMYself \nHOW", "believe$ \nWHO \nHOW" ),
"understand": ( PERS, ( "now", ), "understand$ \nHOW", "understand$ \nWHO \nHOW" ),
"disagree":  ( DEFA, None, "", "with" ),
"fart":      ( DEFA, None, "", "at" ),
"dance":     ( DEFA, None, "", "with" ),
"spin":      ( DEFA, ("dizzily",), "", "around" ),
"flirt":     ( DEFA, None, "", "with" ),
"meow":      ( DEFA, None, "", "at" ),
"bark":      ( DEFA, None, "", "at" ),
"slide":     ( SIMP, None, "slip$ and slide$ \nHOW" ),
"ogle":      ( PREV, None, "" ),
"eye":       ( PREV, ("suspiciously", ), "" ),
"pet":       ( SIMP, None, "pet$ \nWHO \nHOW \nWHERE" ),
"barf":      ( DEFA, None, "", "on" ),
"listen":    ( DEFA, None, "", "to" ),
"purr":      ( DEFA, None, "", "at" ),
"curtsy":    ( DEFA, None, "", "before" ),
"puzzle":    ( SIMP, None, "look$ \nHOW puzzled \nAT", "at" ),
"grovel":    ( DEFA, None, "", "before" ),
"tongue":    ( SIMP, None, "stick$ \nYOUR tongue out \nHOW \nAT", "at" ),
"swing":     ( SIMP, ( "wildly", ), "swing$ \nYOUR arms \nHOW \nAT", "at" ),
"apologize": ( DEFA, None, "", "to" ),
"complain":  ( DEFA, None, "", "about" ),
"rotate":    ( PERS, None, "rotate$ \nHOW", "rotate$ \nWHO \nHOW" ),
"excuse":    ( PERS, None, " \nHOW excuse$ \nMYself", " \nHOW excuse$ \nMYself to \nWHO" ),
"beg":       ( PERS, None, "beg$ \nHOW", "beg$ \nWHO for mercy \nHOW" ),
"fear":      ( PERS, None, "shiver$ \nHOW with fear", "fear$ \nWHO \nHOW" ),
"headshake": ( SIMP, None, "shake$ \nYOUR head \nAT \nHOW", "at" ),
"shake":     ( SIMP, ( "like a bowlful of jello", ), "shake$ \nAT \nHOW", "" ),
"stink":     ( PERS, None, "smell$ \nYOUR armpits. Eeeww!", "smell$ \nPOSS armpits. Eeeww!" ),
"grimace":   ( SIMP, None, " \nHOW make$ an awful face \nAT", "at" ),
"stomp":     ( PERS, None, "stomp$ \nYOUR foot \nHOW", "stomp$ on \nPOSS foot \nHOW" ),
"snigger":   ( DEFA, ( "jeeringly", ), "", "at" ),
"watch":     ( QUAD, ( "carefully", ), "watch the surroundings \nHOW", "watches the surroundings \nHOW", "watch \nWHO \nHOW", "watches \nWHO \nHOW", ),
"scratch":   ( QUAD, ( None, None, "on the head" ), "scratch \nMYself \nHOW \nWHERE", "scratches \nMYself \nHOW \nWHERE", "scratch \nWHO \nHOW \nWHERE", "scratches \nWHO \nHOW \nWHERE", ),
"tap":       ( PERS, ( "impatiently", None, "on the shoulder" ), "tap$ \nYOUR foot \nHOW", "tap$ \nWHO \nWHERE" ),
"wobble":    ( SIMP, None, "wobble$ \nAT \nHOW", "" ),
"move":      ( SIMP, ( "thoughtfully", ), "move$ out of the way \nHOW", "" ),
"yodel":     ( SIMP, None, "yodel$ a merry tune \nHOW", "" ),
"spray":     ( SIMP, None, "spray$ \nHOW \nAT", "all over" ),
"spill":     ( SIMP, None, "spill$ \nYOUR drink \nHOW \nAT", "all over" ),
"melt":      ( PERS, ( "in front of",), "melt$ from the heat", "melt$ \nHOW \nWHO"),
"hello":     ( PERS, None, "greet$ everyone \nHOW", "greet$ \nWHO \nHOW"),
"hi":        ( PERS, None, "greet$ everyone \nHOW", "greet$ \nWHO \nHOW"),
"wait":      ( SIMP, None, "wait$ \nHOW", ""),
"grease":    ( SIMP, ("like in a shiatsu",), "grease$ \nWHO \nHOW"),
"oil":       ( SIMP, ("like in a shiatsu",), "oil$ \nWHO \nHOW"),
"search":    ( DEUX, ("thoroughly",), "search \nWHO \nHOW, where is it?", "searches \nWHO \nHOW, where is it?"),
"sniff":     ( PERS, None, "sniff$. What's that smell?", "sniff$ \nWHO. What's that smell?" ),

# Message-based verbs
"curse":    ( PERS, None, "curse$ \nWHAT \nHOW", "curse$ \nWHO \nHOW" ),
"swear":    ( SIMP, None, "swear$ \nWHAT \nAT \nHOW", "before" ),
"criticize": ( PERS, None, "criticize$ \nWHAT \nHOW", "criticize$ \nWHO \nHOW" ),
"lie":      ( PERS, None, "lie$ \nMSG \nHOW", "lie$ to \nWHO \nHOW" ),
"mutter":   ( PERS, None, "mutter$ \nMSG \nHOW", "mutter$ \nMSG to \nWHO \nHOW" ),
"say":      ( SIMP, ( None, "'nothing" ), " \nHOW say$ \nMSG \nAT", "to" ),
"babble":   ( SIMP, ( "incoherently", "'something" ), "babble$ \nMSG \nHOW \nAT", "to" ),
"chant":    ( SIMP, ( None, "Hare Krishna Krishna Hare Hare" ), " \nHOW chant$: \nWHAT", "" ),
"sing":     ( SIMP, None, "sing$ \nWHAT \nHOW \nAT", "to" ),
"hiss":     ( QUAD, None, "hiss \nMSG \nHOW", "hisses \nMSG \nHOW", "hiss \nMSG to \nWHO \nHOW", "hisses \nMSG to \nWHO \nHOW", ),
"answer":   ( SIMP, None, " \nHOW answer$ \nAT: \nWHAT", "" ),
"reply":    ( QUAD, None, " \nHOW reply: \nWHAT", " \nHOW replies: \nWHAT", " \nHOW reply to \nWHO: \nWHAT", " \nHOW replies to \nWHO: \nWHAT" ),
"exclaim":  ( SIMP, None, " \nHOW exclaim$ \nAT: \nWHAT!", "" ),
"quote":    ( SIMP, None, " \nHOW quote$ \nAT \nMSG", "to" ),
"ask":      ( SIMP, (None, "ehh"), " \nHOW ask$ \nAT: \nWHAT?", "" ),
"request":  ( SIMP, None, " \nHOW request$ \nAT \nWHAT", "" ),
"consult":  ( SIMP, None, " \nHOW consult$ \nAT \nWHAT", "" ),
"mumble":   ( SIMP, None, "mumble$ \nMSG \nHOW \nAT", "to" ),
"murmur":   ( SIMP, None, "murmur$ \nMSG \nHOW \nAT", "to" ),
"scream":   ( SIMP, ( "loudly", ), "scream$ \nMSG \nHOW \nAT", "at" ),
"yell":     ( SIMP, ( "in a high pitched voice", ), "yell$ \nMSG \nHOW \nAT", "at" ),
"command":  ( SIMP, (None, "follow orders"), "command$ \nWHO \nHOW to \nWHAT" ),
"utter":    ( SIMP, None, " \nHOW utter$ \nMSG \nAT", "to" ),
"whisper":  ( SIMP, None, "whisper$ \nMSG \nHOW \nAT", "to" ),
"emote":    ( DEUX, None, "emote: player \nWHAT", " \nWHAT"),

# Verbs that require a person
"hide":     ( SIMP, None, "hide$ \nHOW behind \nWHO" ),
"finger":   ( SIMP, None, "give$ \nWHO the finger" ),
"mercy":    ( SIMP, None, "beg$ \nWHO for mercy" ),
"gripe":    ( PREV, None, "to" ),
"peer":     ( PREV, None, "at" ),
"chase":    ( PREV, ("angrily",), "after" ),
"remember": ( SIMP, None, "remember$ \nAT \nHOW", "" ),
"surprise": ( PREV, None, "" ),
"pounce":   ( PHYS, ( "playfully", ), "" ),
"feel":     ( PHYS, ( "softly", ), "" ),
"bite":     ( PERS, None, " \nHOW bite$ \nYOUR lip", "bite$ \nWHO \nHOW \nWHERE" ),
"lick":     ( SIMP, None, "lick$ \nWHO \nHOW \nWHERE" ),
"caper":    ( PERS, ( "merrily", ), "caper$ \nHOW about", "caper$ around \nWHO \nHOW" ),
"beep":     ( PERS, ( "triumphantly", None, "on the nose" ), " \nHOW beep$ \nMYself \nWHERE", " \nHOW beep$ \nWHO \nWHERE" ),
"blink":    ( PERS, None, "blink$ \nHOW", "blink$ \nHOW at \nWHO" ),
"knock":    ( PHYS, ( None, None, "on the head" ), "" ),
"bonk":     ( PHYS, ( None, None, "on the head" ), "" ),
"bop":      ( PHYS, ( None, None, "on the head" ), "" ),
"stroke":   ( PHYS, ( None, None, "on the cheek" ), "" ),
"shove":    ( PHYS, ( "briskly", None, "to the side" ), "" ),
"push":     ( PHYS, ( None, None, "to the side" ), "" ),
"pull":     ( SIMP, None, "pull$ at \nWHO" ),
"rub":      ( PHYS, ( "gently", None, "on the back" ), "" ),
"hold":     ( PHYS, ( None, None, "in \nYOUR arms" ), "" ),
"embrace":  ( PHYS, ( None, None, "in \nYOUR arms" ), "" ),
"handshake": ( SIMP, None, "shake$ hands with \nWHO", "" ),
"tickle":   ( PREV, None, "" ),
"worship":  ( PREV, None, "" ),
"admire":   ( PREV, None, "" ),
"mock":     ( PREV, None, "" ),
"tease":    ( PREV, None, "" ),
"taunt":    ( PREV, None, "" ),
"strangle": ( PREV, None, "" ),
"hate":     ( PREV, None, "" ),
"fondle":   ( PREV, None, "" ),
"nominate": ( PREV, None, "" ),
"startle":  ( PREV, None, "" ),
"lift":     ( PREV, ( "from the floor", ), "" ),
"turn":     ( PREV, None, "\nYOUR head towards" ),
"squeeze":  ( PREV, ( "fondly", ), "" ),
"comfort":  ( PREV, None, "" ),
"nudge":    ( PHYS, ( "suggestively", ), "" ),
"slap":     ( PHYS, ( None, None, "in the face" ), "" ),
"hit":      ( PHYS, ( None, None, "in the face" ), "" ),
"kick":     ( PHYS, ( "hard", ), "" ),
"tackle":   ( SIMP, None, "tackle$ \nWHO \nHOW", "" ),
"tell":     ( SIMP, None, "tell$ \nWHO \nMSG", "" ),
"spank":    ( PHYS, ( None, None, "on the butt" ), "" ),
"pat":      ( PHYS, ( None, None, "on the head" ), "" ),
"punch":    ( DEUX, ( None, None, "in the eye" ), "punch \nWHO \nHOW \nWHERE", "punches \nWHO \nHOW \nWHERE" ),
"hug":      ( PREV, None, "" ),
"want":     ( PREV, None, "" ),
"pinch":    ( DEUX, None, "pinch \nWHO \nHOW \nWHERE", "pinches \nWHO \nHOW \nWHERE" ),
"kiss":     ( DEUX, None, "kiss \nWHO \nHOW \nWHERE", "kisses \nWHO \nHOW \nWHERE" ),
"caress":   ( DEUX, ( None, None, "on the cheek" ), "caress \nWHO \nHOW \nWHERE", "caresses \nWHO \nHOW \nWHERE" ),
"smooch":   ( DEUX, None, "smooch \nWHO \nHOW", "smooches \nWHO \nHOW" ),
"envy":     ( DEUX, None, "envy \nWHO \nHOW", "envies \nWHO \nHOW" ),
"touch":    ( DEUX, None, "touch \nWHO \nHOW \nWHERE", "touches \nWHO \nHOW \nWHERE" ),
"knee":     ( PHYS, ( None, None, "where it hurts" ), "" ),
"love":     ( PREV, None, "" ),
"adore":    ( PREV, None, "" ),
"grope":    ( PREV, None, "" ),
"poke":     ( PHYS, ( None, None, "in the ribs" ), "" ),
"snuggle":  ( PREV, None, "" ),
"kneel":    ( SIMP, None, " \nHOW fall$ on \nYOUR knees \nAT", "in front of" ),
"trust":    ( PREV, None, "" ),
"like":     ( PREV, None, "" ),
"greet":    ( PREV, None, "" ),
"welcome":  ( PREV, None, "" ),
"thank":    ( PREV, None, "" ),
"cuddle":   ( PREV, None, "" ),
"salute":   ( PREV, None, "" ),
"french":   ( SIMP, None, "give$ \nWHO a REAL kiss, it seems to last forever" ),
"nibble":   ( SIMP, None, "nibble$ \nHOW on \nPOSS ear" ),
"ruffle":   ( SIMP, None, "ruffle$ \nPOSS hair \nHOW" ),
"ignore":   ( PREV, None, "" ),
"forgive":  ( PREV, None, "" ),
"congratulate": ( PREV, None, "" ),
"ayt":      ( SIMP, None, "wave$ \nYOUR hand in front of \nPOSS face, \nIS \nSUBJ \nHOW there?" ),
"judge":    ( PREV, None, "", ),

# Verbs that don't need, nor use persons
"roll":     ( SIMP, ( "to the ceiling", ), "roll$ \nYOUR eyes \nHOW" ),
"boggle":   ( SIMP, None, "boggle$ \nHOW at the concept" ),
"cheer":    ( SHRT, ( "enthusiastically", ), "" ),
"twiddle":  ( SIMP, None, "twiddle$ \nYOUR thumbs \nHOW" ),
"wiggle":   ( SIMP, None, "wiggle$ \nYOUR bottom \nAT \nHOW", "at" ),
"wrinkle":  ( SIMP, None, "wrinkle$ \nYOUR nose \nAT \nHOW", "at" ),
"thumb":    ( SIMP, None, " \nHOW suck$ \nYOUR thumb" ),
"flip":     ( SIMP, None, "flip$ \nHOW head over heels" ),
"cry":      ( DEUX, None, "cry \nHOW", "cries \nHOW" ),
"ah":       ( DEUX, None, "go 'ah' \nHOW", "goes 'ah' \nHOW" ),
"clear":    ( SIMP, None, "clear$ \nYOUR throat \nHOW" ),
"sob":      ( SHRT, None, "" ),
"lag":      ( SHRT, ( "helplessly", ), "" ),
"whine":    ( SHRT, None, "" ),
"cringe":   ( SIMP, ( "in terror", ), "cringe$ \nHOW" ),
"sweat":    ( SHRT, None, "" ),
"gurgle":   ( SHRT, None, "" ),
"grumble":  ( SHRT, None, "" ),
"panic":    ( SHRT, None, "" ),
"pace":     ( SIMP, ( "impatiently", ), "start$ pacing \nHOW" ),
"pale":     ( SIMP, None, "turn$ white as ashes \nHOW" ),
"die":      ( DEUX, None, " \nHOW fall down and play dead", " \nHOW falls to the ground, dead" ),
"sleep":    ( DEUX, ( "soundly", ), "fall asleep \nHOW", "falls asleep \nHOW" ),
"wake":     ( SIMP, ( "groggily", ), "awake$ \nHOW" ),
"awake":    ( SIMP, ( "groggily", ), "awake$ \nHOW" ),
"stumble":  ( SHRT, None, "" ),
"bounce":   ( SHRT, ( "up and down", ), "" ),
"sulk":     ( SHRT, ( "in the corner", ), "" ),
"strut":    ( SHRT, ( "proudly", ), "" ),
"snivel":   ( SHRT, ( "pathetically", ), "" ),
"snore":    ( SHRT, None, "" ),
"clue":     ( SIMP, None, "need$ a clue \nHOW" ),
"stupid":   ( SIMP, None, "look$ \nHOW stupid" ),
"bored":    ( SIMP, None, "look$ \nHOW bored" ),
"repent":   ( SIMP, None, "repent$ \nYOUR sins" ),
"snicker":  ( SHRT, None, "" ),
"smirk":    ( SHRT, None, "" ),
"jump":     ( SIMP, ( "up and down in aggravation", ) , "jump$ \nHOW" ),
"squint":   ( SHRT, None, "" ),
"huff":     ( SHRT, None, "" ),
"puff":     ( SHRT, None, "" ),
"fume":     ( SHRT, None, "" ),
"steam":    ( SHRT, None, "" ),
"choke":    ( SHRT, None, "" ),
"faint":    ( SHRT, None, "" ),
"shrug":    ( SHRT, None, "" ),
"pout":     ( SHRT, None, "" ),
"hiccup":   ( SHRT, None, "" ),
"frown":    ( SHRT, None, "" ),
"pray":     ( SIMP, None, "mumble$ a short prayer \nAT", "to" ),
"gasp":     ( SHRT, ( "in astonishment", ), "" ),
"think":    ( SHRT, ( "carefully", ), "" ),
"ponder":   ( SHRT, ( "over some problem", ), "" ),
"wonder":   ( DEFA, None, "", "at" ),
"clap":     ( SHRT, None, "" ),
"sigh":     ( SHRT, None, "" ),
"cough":    ( SHRT, ( "noisily", ), "" ),
"shiver":   ( SHRT, ( "from the cold", ), "" ),
"tremble":  ( SHRT, None, "" ),
"twitch":   ( DEUX, None, "twitch \nHOW", "twitches \nHOW" ),
"bitch":    ( DEUX, None, "bitch \nHOW", "bitches \nHOW" ),
"blush":    ( DEUX, None, "blush \nHOW", "blushes \nHOW" ),
"stretch":  ( DEUX, None, "stretch \nHOW", "stretches \nHOW" ),
"relax":    ( DEUX, None, "relax \nHOW", "relaxes \nHOW" ),
"duck":     ( PERS, None, "duck$ \nHOW out of the way", "duck$ \nHOW out of \nPOSS way" ),

}

assert not any(type(v[1]) == str for v in VERBS.itervalues()), "Second specifier in verb list must be None or tuple, not str"

AGGRESSIVE_VERBS = {
    "barf", "bitch", "bite", "bonk", "bop", "bump", "burp", "chase", "curse", "feel", "finger", "fondle", "french",
    "grease", "grimace", "grope", "growl", "guffaw", "handshake", "hit", "hold", "hug", "kick", "kiss", "knee",
    "knock", "lick", "lift", "mock", "nibble", "nudge", "oil", "pat", "pet", "pinch", "poke", "pounce", "puke", "push", "pull",
    "punch", "rotate", "rub", "ruffle", "scowl", "scratch", "search", "shake", "shove", "slap", "smooch", "sneer", "snigger",
    "snuggle", "spank", "spill", "spit", "spray", "squeeze", "startle", "stomp", "strangle", "stroke", "surprise",
    "swing", "tackle", "tap", "taunt", "tease", "tickle", "tongue", "touch", "wiggle", "wobble", "wrinkle"
}

assert(AGGRESSIVE_VERBS.issubset(VERBS.keys()))

ACTION_QUALIFIERS = {
    # qualifier -> (actionmsg, roommsg, use room actionstr)
    "suddenly": ("suddenly %s", "suddenly %s", True),
    "fail": ("try to %s, but fail miserably", "tries to %s, but fails miserably", False),
    "again": ("%s again", "%s again", True),
    "pretend": ("pretend to %s", "pretends to %s", False),
    "dont": ("don't %s", "doesn't %s", False),
    "don't": ("don't %s", "doesn't %s", False),
    "attempt": ("attempt to %s, without much success", "attempts to %s, without much success", False)
}

BODY_PARTS = {
        "hand": "on the hand",
        "forehead": "on the forehead",
        "head": "on the head",
        "kneecap": "on the kneecap",
        "ankle": "in the ankle",
        "knee": "on the knee",
        "face": "in the face",
        "hurts": "where it hurts",
        "nuts": "where it hurts",
        "eye": "in the eye",
        "ear": "on the ear",
        "stomach": "in the stomach",
        "butt": "on the butt",
        "behind": "on the behind",
        "leg": "on the leg",
        "foot": "on the foot",
        "toe": "on the right toe",
        "nose": "on the nose",
        "neck": "in the neck",
        "back": "on the back",
        "arm": "on the arm",
        "chest": "on the chest",
        "cheek": "on the cheek",
        "side": "in the side",
        "everywhere": "everywhere",
        "shoulder": "on the shoulder"
    }


def check_person(action, who):
    if not who and ("\nWHO" in action or "\nPOSS" in action):
        return False
    return True


def spacify(string):
    """returns string prefixed with a space, if it has contents. If it is empty, prefix nothing"""
    return " " + string.lstrip(" \t") if string else ""


def who_replacement(actor, target, observer):
    """determines what word to use for a WHO"""
    if target is actor:
        if actor is observer:
            return "yourself"       # you kick yourself
        else:
            return actor.objective + "self"    # ... kicks himself
    else:
        if target is observer:
            return "you"            # ... kicks you
        else:
            return target.title      # ... kicks ...


def poss_replacement(actor, target, observer):
    """determines what word to use for a POSS"""
    if target is actor:
        if actor is observer:
            return "your own"       # your own foot
        else:
            return actor.possessive + " own"   # his own foot
    else:
        if target is observer:
            return "your"           # your foot
        else:
            return lang.possessive(target.title)


_message_regex = re.compile(r"(^|\s)['\"]([^'\"]+?)['\"]")
_skip_words = {"and", "&", "at", "to", "before", "in", "on", "the", "with"}


class Soul(object):
    """
    The 'soul' of a Player. Handles the high level verb actions and allows for social player interaction.
    Verbs that actually do something in the environment (not purely social messages) are implemented elsewhere.
    """
    def __init__(self):
        pass

    def process_verb(self, player, commandstring):
        """
        Parse a command string and return a tuple containing the main verb (tickle, ponder, ...)
        and another tuple containing the targets of the action and the various action messages.
        Any action qualifier is added to the verb string if it is present ("fail kick").
        """
        qualifier, verb, who, adverb, message, bodypart = self.parse(player, commandstring)
        who_objects = set()
        if who:
            # translate the names to actual Livings/items objects
            for name in who:
                living = [living for living in player.location.livings if living.name == name]
                if living:
                    who_objects.update(living)
                else:
                    # try an item
                    item = player.search_item(name, include_containers_in_inventory=False)
                    if item:
                        who_objects.add(item)
        result = self.process_verb_parsed(player, verb, who_objects, adverb, message, bodypart, qualifier)
        if qualifier:
            verb = qualifier + " " + verb
        return verb, result

    def process_verb_parsed(self, player, verb, who=None, adverb=None, message="", bodypart=None, qualifier=None):
        """
        This function takes a verb and the arguments given by the user
        and converts it to an internal representation: (targets-without-player, playermessage, roommessage, targetmessage)
        who = set of actual mud objects (livings), not just player/npc names (strings)
        """
        if not player:
            raise SoulException("no player in process_verb_parsed")
        verbdata = VERBS.get(verb)
        if not verbdata:
            raise UnknownVerbException(verb, None, qualifier)
        vtype = verbdata[0]
        who = set(who or [])   # be sure to make this a set, to allow O(1) lookups later
        if not message and verbdata[1] and len(verbdata[1]) > 1:
            message = verbdata[1][1]  # get the message from the verbs table
        if message:
            if message.startswith("'"):
                # use the message without single quotes around it
                msg = message = spacify(message[1:])
            else:
                msg = " '" + message + "'"
                message = " " + message
        else:
            msg = message = ""
        if not adverb:
            if verbdata[1]:
                adverb = verbdata[1][0]    # normal-adverb
            else:
                adverb = ""
        where = ""
        if bodypart:
            where = " " + BODY_PARTS[bodypart]
        elif not bodypart and verbdata[1] and len(verbdata[1]) > 2 and verbdata[1][2]:
            where = " " + verbdata[1][2]  # replace bodyparts string by specific one from verbs table
        how = spacify(adverb)

        def result_messages(action, action_room):
            if qualifier:
                qual_action, qual_room, use_room_default = ACTION_QUALIFIERS[qualifier]
                action_room = qual_room % action_room if use_room_default else qual_room % action
                action = qual_action % action
            # construct message seen by player
            targetnames = [ who_replacement(player, target, player) for target in who ]
            player_msg = action.replace(" \nWHO", " " + lang.join(targetnames))
            player_msg = player_msg.replace(" \nYOUR", " your")
            player_msg = player_msg.replace(" \nMY", " your")
            # construct message seen by room
            targetnames = [ who_replacement(player, target, None) for target in who ]
            room_msg = action_room.replace(" \nWHO", " " + lang.join(targetnames))
            room_msg = room_msg.replace(" \nYOUR", " " + player.possessive)
            room_msg = room_msg.replace(" \nMY", " " + player.objective)
            # construct message seen by targets
            target_msg = action_room.replace(" \nWHO", " you")
            target_msg = target_msg.replace(" \nYOUR", " " + player.possessive)
            target_msg = target_msg.replace(" \nPOSS", " your")
            target_msg = target_msg.replace(" \nIS", " are")
            target_msg = target_msg.replace(" \nSUBJ", " you")
            target_msg = target_msg.replace(" \nMY", " " + player.objective)
            # fix up POSS, IS, SUBJ in the player and room messages
            if len(who) == 1:
                only_living = list(who)[0]
                subjective = getattr(only_living, "subjective", "it")  # if no subjective attr, use "it"
                player_msg = player_msg.replace(" \nIS", " is")
                player_msg = player_msg.replace(" \nSUBJ", " " + subjective)
                player_msg = player_msg.replace(" \nPOSS", " " + poss_replacement(player, only_living, player))
                room_msg = room_msg.replace(" \nIS", " is")
                room_msg = room_msg.replace(" \nSUBJ", " " + subjective)
                room_msg = room_msg.replace(" \nPOSS", " " + poss_replacement(player, only_living, None))
            else:
                targetnames_player = lang.join([poss_replacement(player, living, player) for living in who])
                targetnames_room = lang.join([poss_replacement(player, living, None) for living in who])
                player_msg = player_msg.replace(" \nIS", " are")
                player_msg = player_msg.replace(" \nSUBJ", " they")
                player_msg = player_msg.replace(" \nPOSS", " " + lang.possessive(targetnames_player))
                room_msg = room_msg.replace(" \nIS", " are")
                room_msg = room_msg.replace(" \nSUBJ", " they")
                room_msg = room_msg.replace(" \nPOSS", " " + lang.possessive(targetnames_room))
            # add fullstops at the end
            player_msg = lang.fullstop("You " + player_msg.strip())
            room_msg = lang.capital(lang.fullstop(player.title + " " + room_msg.strip()))
            target_msg = lang.capital(lang.fullstop(player.title + " " + target_msg.strip()))
            if player in who:
                who.remove(player)  # the player should not be part of the targets
            return who, player_msg, room_msg, target_msg

        # construct the action string
        action = None
        if vtype == DEUX:
            action = verbdata[2]
            action_room = verbdata[3]
            if not check_person(action, who):
                raise ParseError("The verb %s needs a person." % verb)
            action = action.replace(" \nWHERE", where)
            action_room = action_room.replace(" \nWHERE", where)
            action = action.replace(" \nWHAT", message)
            action = action.replace(" \nMSG", msg)
            action_room = action_room.replace(" \nWHAT", message)
            action_room = action_room.replace(" \nMSG", msg)
            action = action.replace(" \nHOW", how)
            action_room = action_room.replace(" \nHOW", how)
            return result_messages(action, action_room)
        elif vtype == QUAD:
            if not who:
                action = verbdata[2]
                action_room = verbdata[3]
            else:
                action = verbdata[4]
                action_room = verbdata[5]
            action = action.replace(" \nWHERE", where)
            action_room = action_room.replace(" \nWHERE", where)
            action = action.replace(" \nWHAT", message)
            action = action.replace(" \nMSG", msg)
            action_room = action_room.replace(" \nWHAT", message)
            action_room = action_room.replace(" \nMSG", msg)
            action = action.replace(" \nHOW", how)
            action_room = action_room.replace(" \nHOW", how)
            return result_messages(action, action_room)
        elif vtype == FULL:
            raise SoulException("vtype FULL")  # doesn't matter, FULL is not used yet anyway
        elif vtype == DEFA:
            action = verb + "$ \nHOW \nAT"
        elif vtype == PREV:
            action = verb + "$" + spacify(verbdata[2]) + " \nWHO \nHOW"
        elif vtype == PHYS:
            action = verb + "$" + spacify(verbdata[2]) + " \nWHO \nHOW \nWHERE"
        elif vtype == SHRT:
            action = verb + "$" + spacify(verbdata[2]) + " \nHOW"
        elif vtype == PERS:
            action = verbdata[3] if who else verbdata[2]
        elif vtype == SIMP:
            action = verbdata[2]
        else:
            raise SoulException("invalid vtype " + vtype)

        if who and len(verbdata) > 3:
            action = action.replace(" \nAT", spacify(verbdata[3]) + " \nWHO")
        else:
            action = action.replace(" \nAT", "")

        if not check_person(action, who):
            raise ParseError("The verb %s needs a person." % verb)

        action = action.replace(" \nHOW", how)
        action = action.replace(" \nWHERE", where)
        action = action.replace(" \nWHAT", message)
        action = action.replace(" \nMSG", msg)
        action_room = action
        action = action.replace("$", "")
        action_room = action_room.replace("$", "s")
        return result_messages(action, action_room)

    def parse(self, player, cmd):
        """
        Parse a command string into the following tuple:
        qualifier, verb, who, adverb, message, bodypart
        who = a set of player/npc names (only strings (names) are returned, not the corresponding player objects)
        """
        qualifier = None
        verb = None
        adverb = None
        who = set()
        message = []
        bodypart = None

        # a substring enclosed in quotes will be extracted as the message
        m = _message_regex.search(cmd)
        if m:
            message = [m.group(2).strip()]
            cmd = cmd[:m.start()] + cmd[m.end():]

        if not cmd:
            raise ParseError("What?")
        words = cmd.split()
        if words[0] in ACTION_QUALIFIERS:     # suddenly, fail, ...
            qualifier = words.pop(0)
        if words and words[0] in _skip_words:
            words.pop(0)

        if not words:
            raise ParseError("What?")
        if words[0] in VERBS:
            verb = words.pop(0)
        else:
            raise UnknownVerbException(words[0], words, qualifier)

        include_flag = True
        collect_message = False
        verbdata = VERBS[verb][2]
        message_verb = "\nMSG" in verbdata or "\nWHAT" in verbdata
        all_livings_names = {living.name for living in player.location.livings}
        all_livings_names.update(item.name for item in player.location.items)
        all_livings_names.update(item.name for item in player.inventory)
        for word in words:
            if collect_message:
                message.append(word)
                continue
            if word in ("them", "him", "her", "it"):
                raise ParseError("It is not clear who you mean.")
            elif word in ("me", "myself"):
                if include_flag:
                    who.add(player.name)
                elif player.name in who:
                    who.remove(player.name)
            elif word in BODY_PARTS:
                if bodypart:
                    raise ParseError("You can't do that both %s and %s." % (BODY_PARTS[bodypart], BODY_PARTS[word]))
                bodypart = word
            elif word in ("everyone", "everybody", "all"):
                if include_flag:
                    if not all_livings_names:
                        raise ParseError("There is nobody here.")
                    # include every *living* thing visible, don't include items, and skip the player itself
                    who.update({living.name for living in player.location.livings if living is not player})
                else:
                    who.clear()
            elif word == "everything":
                raise ParseError("You can't do something to everything around you, be more specific.")
            elif word in ("except", "but"):
                include_flag = not include_flag
            elif word in lang.ADVERBS:
                if adverb:
                    raise ParseError("You can't do that both %s and %s." % (adverb, word))
                adverb = word
            elif word in all_livings_names:
                if include_flag:
                    who.add(word)
                elif word in who:
                    who.remove(word)
            else:
                if message_verb and not message:
                    collect_message = True
                    message.append(word)
                elif word not in _skip_words:
                    # unrecognised word.
                    # check if it could be a person's name
                    if not who:
                        for name in all_livings_names:
                            if name.startswith(word):
                                raise ParseError("Did you mean %s?" % name)
                    # check if it is a prefix of an adverb, if so, suggest the adverbs
                    adverbs = lang.adverb_by_prefix(word)
                    if len(adverbs) == 1:
                        word = adverbs[0]
                        if adverb:
                            raise ParseError("You can't do that both %s and %s." % (adverb, word))
                        adverb = word
                        continue
                    elif len(adverbs) > 1:
                        raise ParseError("What adverb did you mean: %s?" % lang.join(adverbs, conj="or"))
                    if word in VERBS or word in ACTION_QUALIFIERS or word in BODY_PARTS:
                        # in case of a misplaced verb, qualifier or bodypart give a little more specific error
                        raise ParseError("The word %s makes no sense at that location." % word)
                    else:
                        # no idea what the user typed, generic error
                        raise ParseError("The word %s is unrecognized." % word)

        message = " ".join(message)
        return qualifier, verb, who, adverb, message, bodypart
