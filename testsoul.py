import mudlib.player
import mudlib.baseobjects

def test():
    verb = raw_input("verb?")
    who = raw_input("who (comma-separated list)?").strip()
    if not who:
        who = None
    else:
        who = [mudlib.baseobjects.Living(name, "m") for name in who.split(",")]
    adverbs = raw_input("adverbs (comma-separated list)?")
    if not adverbs:
        adverbs = None
    else:
        adverbs = adverbs.split(",")
    message = raw_input("message?")
    bodyparts = raw_input("bodyparts (comma-separated list)?")
    if not bodyparts:
        bodyparts = None
    else:
        bodyparts = bodyparts.split(",")
    player = mudlib.player.Player("<playername>", "f")
    who, player_message, room_message, target_message = player.socialize_parsed(verb, who, adverbs, message, bodyparts)
    print "PLAYER:", player_message
    print "ROOM:", room_message
    for target in who:
        print "TARGET %s: %s" % (target.name, target_message)

if __name__ == "__main__":
    test()

