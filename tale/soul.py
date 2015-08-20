# coding=utf-8
"""
A player's 'soul', which provides a lot of possible emotes (verbs).

Written by Irmen de Jong (irmen@razorvine.net)
Based on ancient soul.c v1.2 written in LPC by profezzorn@nannymud (Fredrik Hübinette)
Only the verb table is more or less intact (with some additions and fixes).
The verb parsing and message generation have been rewritten.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import re
from collections import defaultdict
from . import lang
from .errors import ParseError
from .util import next_iter


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


class NonSoulVerb(SoulException):
    """
    The soul's parser encountered a verb that cannot be handled by the soul itself.
    However the command string has been parsed and the calling code could try
    to handle the verb by itself instead.
    """
    def __init__(self, parsed):
        assert isinstance(parsed, ParseResult)
        super(NonSoulVerb, self).__init__(parsed.verb)
        self.parsed = parsed


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

# Note: several verbs here are commented out because they are replaced by
# real commands or don't fit the game mechanics very well. It doesn't cause problems
# because they're just emotes, but it causes less confusion to disable them here.

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
"capitulate":( DEFA, ( "unconditionally", ), "", "to" ),
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
"understand":( PERS, None, "understand$ \nHOW", "understand$ \nWHO \nHOW" ),
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
"hear":      ( SIMP, None, "listen$ \nAT \nHOW", "to" ),        # the same effect as listen
"purr":      ( DEFA, None, "", "at" ),
"curtsy":    ( DEFA, None, "", "before" ),
"puzzle":    ( SIMP, None, "look$ \nHOW puzzled \nAT", "at" ),
"grovel":    ( DEFA, None, "", "before" ),
"tongue":    ( SIMP, None, "stick$ \nYOUR tongue out \nHOW \nAT", "at" ),
"swing":     ( SIMP, ( "wildly", ), "swing$ \nYOUR arms \nHOW \nAT", "at" ),
"apologize": ( DEFA, None, "", "to" ),
"sorry":     ( SIMP, None, "apologize$ \nAT \nHOW", "to" ),
"complain":  ( DEFA, None, "", "about" ),
"rotate":    ( PERS, None, "rotate$ \nHOW", "rotate$ \nWHO \nHOW" ),        # overridden by a cmd
"excuse":    ( PERS, None, " \nHOW excuse$ \nMYself", " \nHOW excuse$ \nMYself to \nWHO" ),
"beg":       ( PERS, None, "beg$ \nHOW", "beg$ \nWHO for mercy \nHOW" ),
"fear":      ( PERS, None, "shiver$ \nHOW with fear", "fear$ \nWHO \nHOW" ),
"fear":      ( PERS, None, "shiver$ \nHOW with fear", "fear$ \nWHO \nHOW" ),
"headshake": ( SIMP, None, "shake$ \nYOUR head \nAT \nHOW", "at" ),
"shake":     ( SIMP, ( "like a bowlful of jello", ), "shake$ \nAT \nHOW", "" ),
"jiggle":    ( SIMP, ( "like a bowlful of jello", ), "jiggle$ \nAT \nHOW", "" ),
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
"wait":      ( SIMP, None, "wait$ \nHOW", ""),   # replaced by a command
"grease":    ( SIMP, ("like a shiatsu",), "grease$ \nWHO \nHOW"),
"oil":       ( SIMP, ("like a shiatsu",), "oil$ \nWHO \nHOW"),
# "search":    ( DEUX, ("thoroughly",), "search \nWHO \nHOW, where is it?", "searches \nWHO \nHOW, where is it?"),    # replaced by a command
"sniff":     ( PERS, None, "sniff$. What's that smell?", "sniff$ \nWHO. What's that smell?" ),
"smell":     ( PERS, None, "sniff$. What's that smell?", "sniff$ \nWHO. What's that smell?" ),
"smoke":     ( PERS, None, "smoke$ a cigar, and blow$ out the smoke.", "smoke$ a cigar, and blow$ the smoke at \nWHO." ),

# Message-based verbs
"curse":    ( PERS, None, "curse$ \nWHAT \nHOW", "curse$ \nWHO \nHOW" ),
"swear":    ( SIMP, None, "swear$ \nWHAT \nAT \nHOW", "before" ),
"criticize":( PERS, None, "criticize$ \nWHAT \nHOW", "criticize$ \nWHO \nHOW" ),
"lie":      ( PERS, None, "lie$ \nMSG \nHOW", "lie$ to \nWHO \nHOW" ),
"mutter":   ( PERS, (None, "ehh..."), "mutter$ \nMSG \nHOW", "mutter$ \nMSG to \nWHO \nHOW" ),
# "say":      ( SIMP, ( None, "'nothing" ), " say$ \nAT: \nWHAT", "to" ),    # replaced by a command
"babble":   ( SIMP, ( "incoherently", "'something" ), "babble$ \nMSG \nHOW \nAT", "to" ),
"chant":    ( SIMP, ( None, "Hare Krishna Krishna Hare Hare" ), " \nHOW chant$: \nWHAT", "" ),
"sing":     ( SIMP, None, "sing$ \nWHAT \nHOW \nAT", "to" ),
"hiss":     ( QUAD, None, "hiss \nMSG \nHOW", "hisses \nMSG \nHOW", "hiss \nMSG to \nWHO \nHOW", "hisses \nMSG to \nWHO \nHOW", ),
"answer":   ( SIMP, (None, "ehh..."), " \nHOW answer$ \nAT: \nWHAT", "" ),
"reply":    ( QUAD, (None, "ehh..."), " \nHOW reply: \nWHAT", " \nHOW replies: \nWHAT", " \nHOW reply to \nWHO: \nWHAT", " \nHOW replies to \nWHO: \nWHAT" ),
"exclaim":  ( SIMP, (None, "no way"), " \nHOW exclaim$ \nAT: \nWHAT!", "" ),
"quote":    ( SIMP, None, " \nHOW quote$ \nAT \nMSG", "to" ),
"ask":      ( SIMP, (None, "ehh..."), " \nHOW ask$ \nAT: \nWHAT?", "" ),
"request":  ( SIMP, (None, "a moment"), " \nHOW request$ \nAT \nWHAT", "" ),
"consult":  ( SIMP, None, " \nHOW consult$ \nAT \nWHAT", "" ),
"mumble":   ( SIMP, None, "mumble$ \nMSG \nHOW \nAT", "to" ),
"murmur":   ( SIMP, None, "murmur$ \nMSG \nHOW \nAT", "to" ),
"scream":   ( SIMP, ( "loudly", ), "scream$ \nMSG \nHOW \nAT", "at" ),
# "yell":     ( SIMP, ( "in a high pitched voice", ), "yell$ \nMSG \nHOW \nAT", "at" ),    # replaced by a command
"command":  ( SIMP, (None, "follow orders"), "command$ \nWHO \nHOW to \nWHAT" ),
"utter":    ( SIMP, (None, "ehh..."), " \nHOW utter$ \nMSG \nAT", "to" ),
"whisper":  ( SIMP, None, "whisper$ \nMSG \nHOW \nAT", "to" ),
# "emote":    ( DEUX, None, "emote: player \nWHAT", " \nWHAT"),   # replaced by a command

# Verbs that require a person
"glance":   ( SIMP, None, "glance$ \nHOW at \nWHO" ),
"hide":     ( SIMP, None, "hide$ \nHOW behind \nWHO" ),
"finger":   ( SIMP, None, "give$ \nWHO the finger" ),
"mercy":    ( SIMP, None, "beg$ \nWHO for mercy" ),
"jerk":     ( SIMP, ( "briskly", ), "jerk$ \nWHO \nHOW", "" ),
"insult":   ( SIMP, ( "angrily", ), " \nHOW spew$ profanities at \nWHO" ),
"gripe":    ( PREV, None, "to" ),
"peer":     ( PREV, None, "at" ),
"gaze":     ( PREV, None, "at" ),
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
"handshake":( SIMP, None, "shake$ hands with \nWHO", "" ),
"tickle":   ( PREV, None, "" ),
"worship":  ( PREV, None, "" ),
"admire":   ( PREV, None, "" ),
"mock":     ( PREV, None, "" ),
"tease":    ( PREV, None, "" ),
"taunt":    ( PREV, None, "" ),
"strangle": ( PREV, None, "" ),
"hate":     ( PREV, None, "" ),
"kill":     ( PREV, None, "" ),
"attack":   ( PREV, None, "" ),
"fight":    ( PREV, None, "" ),
"fondle":   ( PREV, None, "" ),
"nominate": ( PREV, None, "" ),
"startle":  ( PREV, None, "" ),
# "lift":     ( PREV, ( "from the floor", ), "" ),   # doesn't fit game mechanics
"turn":     ( PREV, None, "\nYOUR head towards" ),
"squeeze":  ( PREV, ( "fondly", ), "" ),
"comfort":  ( PREV, None, "" ),
"nudge":    ( PHYS, ( "suggestively", ), "" ),
"slap":     ( PHYS, ( None, None, "in the face" ), "" ),
"hit":      ( PHYS, ( None, None, "in the face" ), "" ),
"kick":     ( PHYS, ( "hard", ), "" ),
"tackle":   ( SIMP, None, "tackle$ \nWHO \nHOW", "" ),
# "tell":     ( SIMP, None, "tell$ \nWHO \nMSG", "" ),     # replaced by a command
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
"halt!":    ( DEUX, None, "go 'Halt! Hammerzeit!' \nHOW", "goes 'Halt! Hammerzeit!' \nHOW" ),
"stop!":    ( DEUX, None, "go 'Stop! Hammertime!' \nHOW", "goes 'Stop! Hammertime!' \nHOW" ),
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
# "sleep":    ( DEUX, ( "soundly", ), "fall asleep \nHOW", "falls asleep \nHOW" ),
"sleep":    ( SIMP, None, "yawn$ sleepily" ),
# "wake":     ( SIMP, ( "groggily", ), "awake$ \nHOW" ),
"wake":     ( DEUX, None, "are awake", "is awake" ),
# "awake":    ( SIMP, ( "groggily", ), "awake$ \nHOW" ),
"awake":    ( DEUX, None, "are awake", "is awake" ),
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

assert all(v[1] is None or type(v[1]) is tuple for v in VERBS.values()), "Second specifier in verb list must be None or tuple, not str"

AGGRESSIVE_VERBS = {
    "attack", "barf", "bitch", "bite", "bonk", "bop", "bump", "burp", "caress", "chase", "curse", "feel", "fight", "finger", "fondle", "french",
    "grease", "grimace", "grope", "growl", "guffaw", "handshake", "hit", "hold", "hug", "insult", "jerk", "jiggle", "kick", "kill", "kiss", "knee",
    "knock", "lick", "mock", "nibble", "nudge", "oil", "pat", "pet", "pinch", "poke", "pounce", "puke", "push", "pull",
    "punch", "rotate", "rub", "ruffle", "scowl", "scratch", "shake", "shove", "slap", "smooch", "sneer", "snigger",
    "snuggle", "spank", "spill", "spit", "spray", "squeeze", "startle", "stomp", "strangle", "stroke", "surprise",
    "swing", "tackle", "tap", "taunt", "tease", "tickle", "tongue", "touch", "wiggle", "wobble", "wrinkle"
}

assert AGGRESSIVE_VERBS.issubset(VERBS.keys())

NONLIVING_OK_VERBS = {
    "admire", "adore", "answer", "argh", "ask", "babble", "barf", "bark", "beam",
    "bite", "blink", "bow", "breathe", "bump", "cackle", "caper", "capitulate",
    "chuckle", "complain", "cuddle", "curse", "drool", "embrace", "eye", "fear",
    "feel", "finger", "fondle", "gaze", "giggle", "glare", "glance", "grimace", "grin", "groan",
    "grope", "growl", "grunt", "guffaw", "hate", "headshake", "hide", "hiss",
    "hmm", "ignore", "jerk", "judge", "kick", "laugh", "leer", "lick", "like", "listen",
    "love", "lust", "meow", "moan", "mumble", "murmur", "mutter", "nod", "nominate",
    "ogle", "peer", "point", "puke", "pull", "push", "purr", "puzzle", "quote",
    "raise", "recoil", "reply", "rotate", "scowl", "scream", "shake",
    "shove", "sing", "smile", "snap", "snarl", "sneer", "sneeze", "smell", "sniff",
    "snigger", "snort", "spill", "spin", "spit", "spray", "stare", "surrender",
    "swing", "tongue", "touch", "trust", "turn", "understand", "utter", "want",
    "watch", "wave", "wiggle", "wobble", "worship", "wrinkle", "yawn"
}

assert NONLIVING_OK_VERBS.issubset(VERBS.keys())

MOVEMENT_VERBS = {"enter", "climb", "crawl", "go", "run", "move"}     # used to move through an exit


def adjust_available_verbs(allowed_verbs=None, remove_verbs=[], add_verbs={}):
    """Adjust the available verbs"""
    global VERBS, AGGRESSIVE_VERBS, NONLIVING_OK_VERBS, MOVEMENT_VERBS
    if allowed_verbs is not None:
        for v in allowed_verbs:
            if v not in VERBS:
                raise KeyError(v)
        allowed_verbs = set(allowed_verbs)
        VERBS = {v: k for v, k in VERBS.items() if v in allowed_verbs}
        AGGRESSIVE_VERBS &= allowed_verbs
        NONLIVING_OK_VERBS &= allowed_verbs
        MOVEMENT_VERBS &= allowed_verbs
    for v in remove_verbs:
        del VERBS[v]
        AGGRESSIVE_VERBS.discard(v)
        NONLIVING_OK_VERBS.discard(v)
        MOVEMENT_VERBS.discard(v)
    VERBS.update(add_verbs)


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

NEGATING_QUALIFIERS = {"fail", "pretend", "dont", "don't", "attempt"}

assert NEGATING_QUALIFIERS.issubset(ACTION_QUALIFIERS.keys())

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


_quoted_message_regex = re.compile(r"('(?P<msg1>.*)')|(\"(?P<msg2>.*)\")")    # greedy single-or-doublequoted string match
_skip_words = {"and", "&", "at", "to", "before", "in", "into", "on", "off", "onto",
               "the", "with", "from", "after", "before", "under", "above", "next"}


class WhoInfo(object):
    __slots__ = ("sequence", "previous_word")

    def __init__(self, sequence=0):
        self.sequence = sequence
        self.previous_word = None

    def __str__(self):
        return "[sequence=%d, prev_word=%s]" % (self.sequence, self.previous_word)


class ParseResult(object):
    __slots__ = ("verb", "adverb", "message", "bodypart", "qualifier", "who_info", "who_order", "args", "unrecognized", "unparsed")

    def __init__(self, verb, adverb=None, message=None, bodypart=None, qualifier=None, args=None, who_info=None, who_order=None, unrecognized=None, unparsed=""):
        self.verb = verb
        self.adverb = adverb
        self.message = message
        self.bodypart = bodypart
        self.qualifier = qualifier
        self.who_info = who_info or {}      # WhoInfo for all objects parsed  (note: who-objects can be items, livings, and exits!)
        self.who_order = who_order or []    # the order of the occurrence of the objects in the input text
        self.args = args or []
        self.unrecognized = unrecognized or []
        self.unparsed = unparsed
        if self.who_order and not self.who_info:
            self.recalc_who_info()

    def recalc_who_info(self):
        self.who_info = {}
        for sequence, who in enumerate(self.who_order):
            self.who_info[who] = WhoInfo(sequence)

    def __str__(self):
        who_info_str = [" %s->%s" % (living.name, info) for living, info in self.who_info.items()]
        s = [
            "ParseResult:",
            " verb=%s" % self.verb,
            " qualifier=%s" % self.qualifier,
            " adverb=%s" % self.adverb,
            " bodypart=%s" % self.bodypart,
            " message=%s" % self.message,
            " args=%s" % self.args,
            " unrecognized=%s" % self.unrecognized,
            " who_info=%s" % "\n   ".join(who_info_str),
            " who_order=%s" % self.who_order,
            " unparsed=%s" % self.unparsed
        ]
        return "\n".join(s)


def check_name_with_spaces(words, index, all_livings, all_items):
    wordcount = 1
    name = words[index]
    try:
        while wordcount < 6:    # an upper bound for the number of words to concatenate to avoid long runtime
            if name in all_livings:
                return all_livings[name], name, wordcount
            if name in all_items:
                return all_items[name], name, wordcount
            name = name + " " + words[index + wordcount]
            wordcount += 1
    except IndexError:
        pass
    return None, None, 0


class Soul(object):
    """
    The 'soul' of a Player. Handles the high level verb actions and allows for social player interaction.
    Verbs that actually do something in the environment (not purely social messages) are implemented elsewhere.
    """
    def __init__(self):
        self.previously_parsed = None

    def is_verb(self, verb):
        return verb in VERBS

    def process_verb(self, player, commandstring, external_verbs=frozenset()):
        """
        Parse a command string and return a tuple containing the main verb (tickle, ponder, ...)
        and another tuple containing the targets of the action and the various action messages.
        Any action qualifier is added to the verb string if it is present ("fail kick").
        """
        parsed = self.parse(player, commandstring, external_verbs)
        if parsed.verb in external_verbs:
            raise NonSoulVerb(parsed)
        result = self.process_verb_parsed(player, parsed)
        if parsed.qualifier:
            verb = parsed.qualifier + " " + parsed.verb
        else:
            verb = parsed.verb
        return verb, result

    def process_verb_parsed(self, player, parsed):
        """
        This function takes a verb and the arguments given by the user,
        creates various display messages that can be sent to the players and room,
        and returns a tuple: (targets-without-player, playermessage, roommessage, targetmessage)
        """
        if not player:
            raise SoulException("no player in process_verb_parsed")
        verbdata = VERBS.get(parsed.verb)
        if not verbdata:
            raise UnknownVerbException(parsed.verb, None, parsed.qualifier)

        message = parsed.message
        adverb = parsed.adverb

        vtype = verbdata[0]
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
        if parsed.bodypart:
            where = " " + BODY_PARTS[parsed.bodypart]
        elif not parsed.bodypart and verbdata[1] and len(verbdata[1]) > 2 and verbdata[1][2]:
            where = " " + verbdata[1][2]  # replace bodyparts string by specific one from verbs table
        how = spacify(adverb)

        def result_messages(action, action_room):
            action = action.strip()
            action_room = action_room.strip()
            if parsed.qualifier:
                qual_action, qual_room, use_room_default = ACTION_QUALIFIERS[parsed.qualifier]
                action_room = qual_room % action_room if use_room_default else qual_room % action
                action = qual_action % action
            # construct message seen by player
            targetnames = [who_replacement(player, target, player) for target in parsed.who_order]
            player_msg = action.replace(" \nWHO", " " + lang.join(targetnames))
            player_msg = player_msg.replace(" \nYOUR", " your")
            player_msg = player_msg.replace(" \nMY", " your")
            # construct message seen by room
            targetnames = [who_replacement(player, target, None) for target in parsed.who_order]
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
            if len(parsed.who_order) == 1:
                only_living = parsed.who_order[0]
                subjective = getattr(only_living, "subjective", "it")  # if no subjective attr, use "it"
                player_msg = player_msg.replace(" \nIS", " is")
                player_msg = player_msg.replace(" \nSUBJ", " " + subjective)
                player_msg = player_msg.replace(" \nPOSS", " " + poss_replacement(player, only_living, player))
                room_msg = room_msg.replace(" \nIS", " is")
                room_msg = room_msg.replace(" \nSUBJ", " " + subjective)
                room_msg = room_msg.replace(" \nPOSS", " " + poss_replacement(player, only_living, None))
            else:
                targetnames_player = lang.join([poss_replacement(player, living, player) for living in parsed.who_order])
                targetnames_room = lang.join([poss_replacement(player, living, None) for living in parsed.who_order])
                player_msg = player_msg.replace(" \nIS", " are")
                player_msg = player_msg.replace(" \nSUBJ", " they")
                player_msg = player_msg.replace(" \nPOSS", " " + lang.possessive(targetnames_player))
                room_msg = room_msg.replace(" \nIS", " are")
                room_msg = room_msg.replace(" \nSUBJ", " they")
                room_msg = room_msg.replace(" \nPOSS", " " + lang.possessive(targetnames_room))
            # add fullstops at the end
            player_msg = lang.fullstop("You " + player_msg)
            room_msg = lang.capital(lang.fullstop(player.title + " " + room_msg))
            target_msg = lang.capital(lang.fullstop(player.title + " " + target_msg))
            if player in parsed.who_info:
                who = set(parsed.who_info)
                who.remove(player)  # the player should not be part of the remaining targets.
                who = frozenset(who)
            else:
                who = frozenset(parsed.who_info)
            return who, player_msg, room_msg, target_msg

        # construct the action string
        action = None
        if vtype == DEUX:
            action = verbdata[2]
            action_room = verbdata[3]
            if not check_person(action, parsed.who_order):
                raise ParseError("The verb %s needs a person." % parsed.verb)
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
            if parsed.who_info:
                action = verbdata[4]
                action_room = verbdata[5]
            else:
                action = verbdata[2]
                action_room = verbdata[3]
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
            action = parsed.verb + "$ \nHOW \nAT"
        elif vtype == PREV:
            action = parsed.verb + "$" + spacify(verbdata[2]) + " \nWHO \nHOW"
        elif vtype == PHYS:
            action = parsed.verb + "$" + spacify(verbdata[2]) + " \nWHO \nHOW \nWHERE"
        elif vtype == SHRT:
            action = parsed.verb + "$" + spacify(verbdata[2]) + " \nHOW"
        elif vtype == PERS:
            action = verbdata[3] if parsed.who_order else verbdata[2]
        elif vtype == SIMP:
            action = verbdata[2]
        else:
            raise SoulException("invalid vtype " + vtype)

        if parsed.who_info and len(verbdata) > 3:
            action = action.replace(" \nAT", spacify(verbdata[3]) + " \nWHO")
        else:
            action = action.replace(" \nAT", "")

        if not check_person(action, parsed.who_order):
            raise ParseError("The verb %s needs a person." % parsed.verb)

        action = action.replace(" \nHOW", how)
        action = action.replace(" \nWHERE", where)
        action = action.replace(" \nWHAT", message)
        action = action.replace(" \nMSG", msg)
        action_room = action
        action = action.replace("$", "")
        action_room = action_room.replace("$", "s")
        return result_messages(action, action_room)

    def parse(self, player, cmd, external_verbs=frozenset()):
        """Parse a command string, returns a ParseResult object."""
        qualifier = None
        message_verb = False  # does the verb expect a message?
        external_verb = False  # is it a non-soul verb?
        adverb = None
        message = []
        bodypart = None
        arg_words = []
        unrecognized_words = []
        who_info = defaultdict(WhoInfo)
        who_order = []
        who_sequence = 0
        unparsed = cmd

        # a substring enclosed in quotes will be extracted as the message
        m = _quoted_message_regex.search(cmd)
        if m:
            message = [(m.group("msg1") or m.group("msg2")).strip()]
            cmd = cmd[:m.start()] + cmd[m.end():]

        if not cmd:
            raise ParseError("What?")
        words = cmd.split()
        if words[0] in ACTION_QUALIFIERS:     # suddenly, fail, ...
            qualifier = words.pop(0)
            unparsed = unparsed[len(qualifier):].lstrip()
            if qualifier == "dont":
                qualifier = "don't"  # little spelling suggestion
            # note: don't add qualifier to arg_words
        if words and words[0] in _skip_words:
            skipword = words.pop(0)
            unparsed = unparsed[len(skipword):].lstrip()

        if not words:
            raise ParseError("What?")
        verb = None
        if words[0] in external_verbs:    # external verbs have priority above soul verbs
            verb = words.pop(0)
            external_verb = True
            # note: don't add verb to arg_words
        elif words[0] in VERBS:
            verb = words.pop(0)
            verbdata = VERBS[verb][2]
            message_verb = "\nMSG" in verbdata or "\nWHAT" in verbdata
            # note: don't add verb to arg_words
        elif player.location.exits:
            # check if the words are the name of a room exit.
            move_action = None
            if words[0] in MOVEMENT_VERBS:
                move_action = words.pop(0)
                if not words:
                    raise ParseError("%s where?" % lang.capital(move_action))
            exit, exit_name, wordcount = check_name_with_spaces(words, 0, player.location.exits, {})
            if exit:
                if wordcount != len(words):
                    raise ParseError("What do you want to do with that?")
                unparsed = unparsed[len(exit_name):].lstrip()
                raise NonSoulVerb(ParseResult(verb=exit_name, who_order=[exit], qualifier=qualifier, unparsed=unparsed))
            elif move_action:
                raise ParseError("You can't %s there." % move_action)
            else:
                # can't determine verb at this point, just continue with verb=None
                pass
        else:
            # can't determine verb at this point, just continue with verb=None
            pass

        if verb:
            unparsed = unparsed[len(verb):].lstrip()
        include_flag = True
        collect_message = False
        all_livings = {}  # livings in the room (including player) by name + aliases
        all_items = {}  # all items in the room or player's inventory, by name + aliases
        for living in player.location.livings:
            all_livings[living.name] = living
            for alias in living.aliases:
                all_livings[alias] = living
        for item in player.location.items:
            all_items[item.name] = item
            for alias in item.aliases:
                all_items[alias] = item
        for item in player.inventory:
            all_items[item.name] = item
            for alias in item.aliases:
                all_items[alias] = item
        previous_word = None
        words_enumerator = enumerate(words)
        for index, word in words_enumerator:
            if collect_message:
                message.append(word)
                arg_words.append(word)
                previous_word = word
                continue
            if not message_verb and not collect_message:
                word = word.rstrip(",")
            if word in ("them", "him", "her", "it"):
                if self.previously_parsed:
                    # try to connect the pronoun to a previously parsed item/living
                    who_list = self.match_previously_parsed(player, word)
                    if who_list:
                        for who, name in who_list:
                            if include_flag:
                                who_info[who].sequence = who_sequence
                                who_info[who].previous_word = previous_word
                                who_sequence += 1
                                who_order.append(who)
                            else:
                                del who_info[who]
                                who_order.remove(who)
                            arg_words.append(name)  # put the replacement-name in the args instead of the pronoun
                    previous_word = None
                    continue
                raise ParseError("It is not clear who you mean.")
            if word in ("me", "myself", "self"):
                if include_flag:
                    who_info[player].sequence = who_sequence
                    who_info[player].previous_word = previous_word
                    who_sequence += 1
                    who_order.append(player)
                elif player in who_info:
                    del who_info[player]
                    who_order.remove(player)
                arg_words.append(word)
                previous_word = None
                continue
            if word in BODY_PARTS:
                if bodypart:
                    raise ParseError("You can't do that both %s and %s." % (BODY_PARTS[bodypart], BODY_PARTS[word]))
                bodypart = word
                arg_words.append(word)
                continue
            if word in ("everyone", "everybody", "all"):
                if include_flag:
                    if not all_livings:
                        raise ParseError("There is nobody here.")
                    # include every *living* thing visible, don't include items, and skip the player itself
                    for living in player.location.livings:
                        if living is not player:
                            who_info[living].sequence = who_sequence
                            who_info[living].previous_word = previous_word
                            who_sequence += 1
                            who_order.append(living)
                else:
                    who_info = {}
                    who_order = []
                    who_sequence = 0
                arg_words.append(word)
                previous_word = None
                continue
            if word == "everything":
                raise ParseError("You can't do something to everything around you, be more specific.")
            if word in ("except", "but"):
                include_flag = not include_flag
                arg_words.append(word)
                continue
            if word in lang.ADVERBS:
                if adverb:
                    raise ParseError("You can't do that both %s and %s." % (adverb, word))
                adverb = word
                arg_words.append(word)
                continue
            if word in all_livings:
                living = all_livings[word]
                if include_flag:
                    who_info[living].sequence = who_sequence
                    who_info[living].previous_word = previous_word
                    who_sequence += 1
                    who_order.append(living)
                elif living in who_info:
                    del who_info[living]
                    who_order.remove(living)
                arg_words.append(word)
                previous_word = None
                continue
            if word in all_items:
                item = all_items[word]
                if include_flag:
                    who_info[item].sequence = who_sequence
                    who_info[item].previous_word = previous_word
                    who_sequence += 1
                    who_order.append(item)
                elif item in who_info:
                    del who_info[item]
                    who_order.remove(item)
                arg_words.append(word)
                previous_word = None
                continue
            if player.location:
                exit, exit_name, wordcount = check_name_with_spaces(words, index, player.location.exits, {})
                if exit:
                    who_info[exit].sequence = who_sequence
                    who_info[exit].previous_word = previous_word
                    previous_word = None
                    who_sequence += 1
                    who_order.append(exit)
                    arg_words.append(exit_name)
                    while wordcount > 1:
                        next_iter(words_enumerator)
                        wordcount -= 1
                    continue
            item, full_name, wordcount = check_name_with_spaces(words, index, all_livings, all_items)
            if item:
                while wordcount > 1:
                    next_iter(words_enumerator)
                    wordcount -= 1
                if include_flag:
                    who_info[item].sequence = who_sequence
                    who_info[item].previous_word = previous_word
                    who_sequence += 1
                    who_order.append(item)
                elif item in who_info:
                    del who_info[item]
                    who_order.remove(item)
                arg_words.append(full_name)
                previous_word = None
                continue
            if message_verb and not message:
                collect_message = True
                message.append(word)
                arg_words.append(word)
                continue
            if word not in _skip_words:
                # unrecognized word, check if it could be a person's name or an item. (prefix)
                if not who_order:
                    for name in all_livings:
                        if name.startswith(word):
                            raise ParseError("Perhaps you meant %s?" % name)
                    for name in all_items:
                        if name.startswith(word):
                            raise ParseError("Perhaps you meant %s?" % name)
                if not external_verb:
                    if not verb:
                        raise UnknownVerbException(word, words, qualifier)
                    # check if it is a prefix of an adverb, if so, suggest a few adverbs
                    adverbs = lang.adverb_by_prefix(word)
                    if len(adverbs) == 1:
                        word = adverbs[0]
                        if adverb:
                            raise ParseError("You can't do that both %s and %s." % (adverb, word))
                        adverb = word
                        arg_words.append(word)
                        previous_word = word
                        continue
                    elif len(adverbs) > 1:
                        raise ParseError("What adverb did you mean: %s?" % lang.join(adverbs, conj="or"))

                if external_verb:
                    arg_words.append(word)
                    unrecognized_words.append(word)
                else:
                    if word in VERBS or word in ACTION_QUALIFIERS or word in BODY_PARTS:
                        # in case of a misplaced verb, qualifier or bodypart give a little more specific error
                        raise ParseError("The word %s makes no sense at that location." % word)
                    else:
                        # no idea what the user typed, generic error
                        raise ParseError("It's not clear what you mean by '%s'." % word)
            previous_word = word

        message = " ".join(message)
        if not verb:
            # This is interesting: there's no verb.
            # but maybe the thing the user typed refers to an object or creature.
            # In that case, set the verb to that object's default verb.
            if len(who_order) == 1:
                try:
                    verb = who_order[0].default_verb
                except AttributeError:
                    verb = "examine"   # fallback for everything that hasn't explicitly set a default_verb
            else:
                raise UnknownVerbException(words[0], words, qualifier)
        return ParseResult(verb, who_info=who_info, who_order=who_order,
                           adverb=adverb, message=message, bodypart=bodypart, qualifier=qualifier,
                           args=arg_words, unrecognized=unrecognized_words, unparsed=unparsed)

    def match_previously_parsed(self, player, pronoun):
        """
        Try to connect the pronoun (it, him, her, them) to a previously parsed item/living.
        Returns a list of (who, replacement-name) tuples.
        The reason we return a replacement-name is that the parser can replace the
        pronoun by the proper name that would otherwise have been used in that place.
        """
        if pronoun == "them":
            # plural (any item/living qualifies)
            matches = list(self.previously_parsed.who_order)
            for who in matches:
                if not player.search_item(who.name) and who not in player.location.livings:
                    player.tell("<dim>(By '%s', it is assumed you meant %s.)</>" % (pronoun, who.title))
                    raise ParseError("%s is no longer around." % lang.capital(who.subjective))
            if matches:
                player.tell("<dim>(By '%s', it is assumed you mean: %s.)" % (pronoun, lang.join(who.title for who in matches)))
                return [(who, who.name) for who in matches]
            else:
                raise ParseError("It is not clear who you're referring to.")
        for who in self.previously_parsed.who_order:
            # first see if it is an exit
            if pronoun == "it":
                for direction, exit in player.location.exits.items():
                    if exit is who:
                        player.tell("<dim>(By '%s', it is assumed you mean '%s'.)</>" % (pronoun, direction))
                        return [(who, direction)]
            # not an exit, try an item or a living
            if pronoun == who.objective:
                if player.search_item(who.name) or who in player.location.livings:
                    player.tell("<dim>(By '%s', it is assumed you mean %s.)</>" % (pronoun, who.title))
                    return [(who, who.name)]
                player.tell("<dim>(By '%s', it is assumed you meant %s.)</>" % (pronoun, who.title))
                raise ParseError("%s is no longer around." % lang.capital(who.subjective))
        raise ParseError("It is not clear who you're referring to.")
