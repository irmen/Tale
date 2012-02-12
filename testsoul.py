import mudlib.player
import mudlib.baseobjects

def test():
    verb = raw_input("verb?")
    who = raw_input("who (comma-separated list)?").strip()
    if not who:
        who = None
    else:
        who = [mudlib.baseobjects.Living(name, "m") for name in who.split(",")]
    adverb = raw_input("adverb?")
    message = raw_input("message?")
    bodypart = raw_input("bodypart?")
    player = mudlib.player.Player("<playername>", "f")
    who, player_message, room_message, target_message = player.socialize_parsed(verb, who, adverb, message, bodypart)
    print "PLAYER:", player_message
    print "ROOM:", room_message
    for target in who:
        if target is player:
            continue
        print "TARGET %s: %s" % (target.name, target_message)

def test2():
    cmd = raw_input("cmd?> ")
    player = mudlib.player.Player("fritz", "m")
    player.location = mudlib.baseobjects.Location("somewhere")
    player.location.all_livings["max"] = mudlib.baseobjects.Living("max","m")
    player.location.all_livings["julie"] = mudlib.baseobjects.Living("julie","f")
    player.location.all_livings[player.name] = player
    verb, (who, player_message, room_message, target_message) = player.socialize(cmd)
    print "VERB:", verb
    print "PLAYER:", player_message
    print "ROOM:", room_message
    for target in who:
        if target is player:
            continue
        print "TARGET %s: %s" % (target.name, target_message)

if __name__ == "__main__":
    while True:
        test2()
        print

