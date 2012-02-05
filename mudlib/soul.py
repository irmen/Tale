"""
A player's 'soul', which provides a lot of possible emotes (verbs).

Written by Irmen de Jong (irmen@razorvine.net)
Based on soul.c written in LPC by profezzorn@nannymud

MISSING: whisper, tell
These are special in the sense that all user input is directed only at the given target.

BUG: PHYS crashes
BUG: msg-adverb in verbdata doesn't work, for instance with chant
BUG: multiple adverbs don't work?

"""

import mudlib.languagetools as lang


class SoulException(Exception): pass


DEFA = 1  # adds HOW+AT   (you smile happily at Fritz)
PREV = 2  # adds a WHO+HOW   (you ignore Fritz completely)
PHYS = 3  # adds a WHO+HOW+WHERE  (you stroke Anna softly on the shoulder)
SHRT = 4  # just adds a HOW, won't show a target  (you sweat profusely)
PERS = 5  # provide an alternate WHO text  (you shiver with fear / you fear Fritz)
SIMP = 6  # don't add stuff, the text itself has all escapes  (you snap your fingers at Fritz)
DEUX = 7  # a room text is provided with alternate spelling or wording  (you fall down and play dead / Player falls to the ground, dead)
QUAD = 8  # like DEUX, but also provides two more texts for when a target is used
FULL = 9  # not used yet

# escapes used: AT, HOW, IS, MSG, MY, OBJ, POSS, SUBJ, THEIR, WHAT, WHERE, WHO, YOUR

VERBS = {
"flex":      ( DEUX, None, "flex \nYOUR muscles \nHOW", "flexes \nYOUR muscles \nHOW"),
"snort":     ( SIMP, None, "snort$ \nHOW \nAT", "at"),
"pant":      ( SIMP, ( "heavily", ), "pant$ \nHOW \nAT", "at"),
"hmm":       ( SIMP, None, "hmm$ \nHOW \nAT", "at"),
"ack":       ( SIMP, None, "ack$ \nHOW \nAT", "at"),
"guffaw":    ( SIMP, None, "guffaw$ \nHOW \nAT", "at"),
"raise":     ( SIMP, None, " \nHOW raise$ an eyebrow \nAT", "at"),
"snap":      ( SIMP, None, "snap$ \nYOUR fingers \nAT", "at"),
"lust":      ( DEFA, None, "", "for"),
"burp":      ( DEFA, ( "rudely", ), "", "at"),
"bump":      ( DEFA, ( "clumsily", ), "", "into"),
"wink":      ( DEFA, ( "suggestively", ), "", "at"),
"smile":     ( DEFA, ( "happily", ), "", "at"),
"yawn":      ( DEFA, None, "", "at"),
"swoon":     ( DEFA, ( "romantically", ), "", "at"),
"sneer":     ( DEFA, ( "disdainfully", ), "", "at"),
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
"flirt":     ( DEFA, None, "", "with" ),
"meow":      ( DEFA, None, "", "at" ),
"bark":      ( DEFA, None, "", "at" ),
"ogle":      ( PREV, None, "" ),
"pet":       ( SIMP, None, "pet$ \nWHO \nHOW \nWHERE" ),
"barf":      ( DEFA, None, "", "on" ),
"listen":    ( DEFA, None, "", "to" ),
"purr":      ( DEFA, None, "", "at" ),
"curtsy":    ( DEFA, None, "", "before" ),
"puzzle":    ( SIMP, None, "look$ \nHOW puzzled \nAT", "at" ),
"grovel":    ( DEFA, None, "", "before" ),
"tongue":    ( SIMP, None, "stick$ \nYOUR tongue out \nHOW \nAT", "at" ),
"apologize": ( DEFA, None, "", "to" ),
"complain":  ( DEFA, None, "", "about" ),
"rotate":    ( PERS, None, "rotate$ \nHOW", "rotate$ \nWHO \nHOW" ),
"excuse":    ( PERS, None, " \nHOW excuse$ \nMYself", " \nHOW excuse$ \nMYself to \nWHO" ),
"beg":       ( PERS, None, "beg$ \nHOW", "beg$ \nWHO for mercy \nHOW" ),
"fear":      ( PERS, None, "shiver$ \nHOW with fear", "fear$ \nWHO \nHOW" ),
"headshake": ( SIMP, None, "shake$ \nYOUR head \nAT \nHOW", "at" ),
"shake":     ( SIMP, ( "like a bowlful of jello", ), "shake$ \nAT \nHOW", "" ),
"stink":     ( DEUX, None, "smell \nYOUR armpits. Eeew!", "smells \nYOUR armpits. Eeew!"),
"grimace":   ( SIMP, None, " \nHOW make$ an awful face \nAT", "at" ),
"stomp":     ( PERS, None, "stomp$ \nYOUR foot \nHOW", "stomp$ on \nPOSS foot \nHOW" ),
"snigger":   ( DEFA, ( "jeeringly", ), "", "at" ),
"watch":     ( QUAD, ( "carefully", ), "watch the surroundings \nHOW", "watches the surroundings \nHOW", "watch \nWHO \nHOW",  "watches \nWHO \nHOW", ),
"scratch":   ( QUAD, ( None, None, "on the head" ), "scratch \nMYself \nHOW \nWHERE", "scratches \nMYself \nHOW \nWHERE", "scratch \nWHO \nHOW \nWHERE", "scratches \nWHO \nHOW \nWHERE",    ),
"tap":       ( PERS, ( "impatiently", None, "on the shoulder" ), "tap$ \nYOUR foot \nHOW", "tap$ \nWHO \nWHERE" ),
"wobble":    ( SIMP, None, "wobble$ \nAT \nHOW", "" ),
"yodel":     ( SIMP, None, "yodel$ a merry tune \nHOW", "" ),

# Message-based verbs
"curse":    ( PERS, None, "curse$ \nWHAT \nHOW", "curse$ \nWHO \nHOW" ),
"swear":    ( SIMP, None, "swear$ \nWHAT \nAT \nHOW", "before" ),
"criticize": ( PERS, None, "criticize$ \nWHAT \nHOW", "criticize$ \nWHO \nHOW" ),
"lie":      ( PERS, None, "lie$ \nMSG \nHOW", "lie$ to \nWHO \nHOW" ),
"mutter":   ( PERS, None, "mutter$ \nMSG \nHOW", "mutter$ to \nWHO \nHOW" ),
"say":      ( SIMP, ( None, "'nothing" ), " \nHOW say$ \nMSG \nAT", "to" ),
"babble":   ( SIMP, ( "incoherently", "'something" ), "babble$ \nMSG \nHOW \nAT", "to" ),
"chant":    ( SIMP, ( None, "Hare Krishna Krishna Hare Hare" ), " \nHOW chant$: \nWHAT", "" ),
"sing":     ( SIMP, None, "sing$ \nWHAT \nHOW \nAT", "to" ),
"go":       ( DEUX, ( None, "ah" ), "go \nMSG \nHOW", "goes \nMSG \nHOW" ),
"hiss":     ( QUAD, None, "hiss \nMSG \nHOW", "hisses \nMSG \nHOW", "hiss \nMSG to \nWHO \nHOW", "hisses \nMSG to \nWHO \nHOW",  ),
"exclaim":  ( SIMP, None, " \nHOW exclaim$ \nAT: \nWHAT!", "" ),
"quote":    ( SIMP, None, " \nHOW quote$ \nAT \nMSG", "to" ),
"ask":      ( SIMP, None, " \nHOW ask$ \nAT: \nWHAT?", "" ),
"request":  ( SIMP, None, " \nHOW request$ \nAT \nWHAT", "" ),
"consult":  ( SIMP, None, " \nHOW consult$ \nAT \nWHAT", "" ),
"mumble":   ( SIMP, None, "mumble$ \nMSG \nHOW \nAT", "to" ),
"murmur":   ( SIMP, None, "murmur$ \nMSG \nHOW \nAT", "to" ),
"scream":   ( SIMP, ( "loudly", ), "scream$ \nMSG \nHOW \nAT", "at" ),
"yell":     ( SIMP, ( "in a high pitched voice", ), "yell$ \nMSG \nHOW \nAT", "at" ),
"utter":    ( SIMP, None, " \nHOW utter$ \nMSG \nAT", "to" ),

# Verbs that require a person
"hide":     ( SIMP, None, "hide$ \nHOW behind \nWHO" ),
"finger":   ( SIMP, None, "give$ \nWHO the finger" ),
"mercy":    ( SIMP, None, "beg$ \nWHO for mercy" ),
"gripe":    ( PREV, None, "to" ),
"peer":     ( PREV, None, "at" ),
"remember": ( SIMP, None, "remember$ \nAT \nHOW", "" ),
"surprise": ( PREV, None, "" ),
"pounce":   ( PHYS, ( "playfully", ), "" ),
"bite":     ( PERS, None, " \nHOW bite$ \nYOUR lip", "bite$ \nWHO \nHOW \nWHERE" ),
"lick":     ( SIMP, None, "lick$ \nWHO \nHOW \nWHERE" ),
"caper":    ( PERS, ( "merrily", ), "caper$ \nHOW about", "caper$ around \nWHO \nHOW" ),
"beep":     ( PERS, ( "triumphantly", None, "on the nose" ), " \nHOW beep$ \nMYself \nWHERE", " \nHOW beep$ \nWHO \nWHERE" ),
"blink":    ( PERS, None, "blink$ \nHOW", "blink$ \nHOW at \nWHO" ),
"knock":    ( PHYS, ( None, None, "on the head" ), "" ),
"bonk":     ( PHYS, ( None, None, "on the head" ), "" ),
"bop":      ( PHYS, ( None, None, "on the head" ), "" ),
"stroke":   ( PHYS, ( None, None, "on the cheek" ), "" ),
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
"turn":     ( PREV, None, "\nYOUR head towards" ),
"squeeze":  ( PREV, ( "fondly", ), "" ),
"comfort":  ( PREV, None, "" ),
"nudge":    ( PHYS, ( "suggestively", ), "" ),
"slap":     ( PHYS, ( None, None, "in the face" ), "" ),
"hit":      ( PHYS, ( None, None, "in the face" ), "" ),
"kick":     ( PHYS, ( "hard", ), "" ),
"tackle":   ( SIMP, None, "tackle$ \nWHO \nHOW", "" ),
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
"die":      ( DEUX, None, "fall \nHOW down and play dead", "falls \nHOW to the ground, dead" ),
"sleep":    ( DEUX, ( "soundly", ), "fall asleep \nHOW", "falls asleep \nHOW" ),
"stumble":  ( SHRT, None, "" ),
"bounce":   ( SHRT, None, "" ),
"sulk":     ( SHRT, ( "in the corner", ), "" ),
"strut":    ( SHRT, ( "proudly", ), "" ),
"sniff":    ( SHRT, None, "" ),
"snivel":   ( SHRT, ( "pathetically", ), "" ),
"snore":    ( SHRT, None, "" ),
"clue":     ( SIMP, None, "need$ a clue \nHOW" ),
"stupid":   ( SIMP, None, "look$ \nHOW stupid" ),
"bored":    ( SIMP, None, "look$ \nHOW bored" ),
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

ADJECTIVES = { "bored", "confused", "curious", "sad", "surprised", "tired"}

HOW = { "very", "quite", "barely", "extremely", "somewhat", "almost"}

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

ACTION_QUALIFIERS = { "help", "fail", "again", "dont", "don't", "feeling", "suddenly"}




def insert_targetnames(message, who):
    targetnames = lang.join([t.name for t in who or []])
    return message.replace(" \nWHO", " " + targetnames)


def room_message(player, message, who):
    print "*room_message:", repr(message)  # XXX
    message = insert_targetnames(message, who)
    message = message.replace(" \nYOUR", " " + player.possessive)
    return lang.fullstop(player.name + " " + message.strip())


def target_message(player, message):
    print "*target_message:", repr(message)  # XXX
    message = message.replace(" \nWHO", " you")
    message = message.replace(" \nYOUR", " " + player.possessive)
    return lang.fullstop(player.name + " " + message.strip())


def player_message(message, who):
    print "*player_message:", repr(message)  # XXX
    message = insert_targetnames(message, who)
    message = message.replace(" \nYOUR", " your")
    return lang.fullstop("you " + message.strip())


def check_person(action, who):
    if not who and ("\nWHO" in action or "\nPOSS" in action or "\nTHEIR" in action or "\nOBJ" in action):
        return False
    return True


def spacify(string):
    """returns string prefixed with a space, if it has contents. If it is empty, prefix nothing"""
    return " " + string.lstrip() if string else ""


def reduce_verb(player, verb, who, adverbs, message, bodyparts):
    """
    This function takes a verb and the arguments given by
    the user and converts it to an internal representation:
    (targets, playermessage, roommessage, targetmessage)
    """
    verbdata = VERBS[verb]
    vtype = verbdata[0]
    who = who or []
    bodyparts = bodyparts or []
    if message:
        msg = " '" + message + "'"
        message = " " + message
    else:
        msg = ""
    adverbs = adverbs or verbdata[1] or []
    print "*ADVERBS=", adverbs  # XXX
    # XXX adverbs in verbdata: (normal-adverb, adverb-for-message, adverb-for-bodypart)
    if bodyparts and len(adverbs) > 2 and adverbs[2]:
        where = " " + adverbs[2]  # replace bodyparts string by specific ones from verbs table
    else:
        where = " " + lang.join([BODY_PARTS[part] for part in bodyparts])
    how = "" if not adverbs else adverbs[0]  # normal-adverb
    how = spacify(how or "")
    print "*HOW=", how  # XXX
    print "*WHERE=", where  # XXX

    def result_messages(action, action_room):
        return who, \
               player_message(action, who), \
               room_message(player, action_room, who), \
               target_message(player, action_room)

    # construct the action string
    action = None
    if vtype == DEUX:
        action = verbdata[2]
        action_room = verbdata[3]
        if not check_person(action, who):
            raise SoulException("Need person for verb " + verb)
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
        raise NotImplementedError("vtype FULL")  # doesn't matter, FULL is not used yet anyway
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
        raise NotImplementedError("Unknown vtype " + vtype)

    if who and len(verbdata) > 3:
        action = action.replace(" \nAT", spacify(verbdata[3]) + " \nWHO")
    else:
        action = action.replace(" \nAT", "")

    if not check_person(action, who):
        raise SoulException("Need person for verb " + verb)

    action = action.replace(" \nHOW", how)
    action = action.replace(" \nWHERE", where)
    action = action.replace(" \nWHAT", message)
    action = action.replace(" \nMSG", msg)
    action_room = action
    action = action.replace("$", "")
    action_room = action_room.replace("$", "s")
    return result_messages(action, action_room)


class Soul(object):
    """
    The 'soul' of a Player. Handles the highlevel verb actions and allows for the social player interaction.
    """
    def __init__(self):
        pass

    def process_verb(self, player, commandstring):
        verb = ""
        who = None
        adverbs = None
        message = None
        bodyparts = None
        raise NotImplementedError("command string parser")   # @TODO: add command string parser...
        return self.process_verb_parsed(player, verb, who, adverbs, message, bodyparts)

    def process_verb_parsed(self, player, verb, who=None, adverbs=None, message="", bodyparts=None):
        who, player_message, room_message, target_message = reduce_verb(player, verb, who, adverbs, message, bodyparts)
        return who, player_message, room_message, target_message
