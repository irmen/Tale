import mudlib.player
import mudlib.baseobjects
from mudlib.soul import ParseException, UnknownVerbException

def test():
    cmd = raw_input("cmd?> ")
    player = mudlib.player.Player("fritz", "m", "human")
    player.location = mudlib.baseobjects.Location("somewhere")
    player.location.livings = { mudlib.baseobjects.Living("max","m"),
                                mudlib.baseobjects.Living("julie","f"),
                                player }
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
        try:
            test()
        except UnknownVerbException,x:
            print "* I don't understand the verb %s." % x.message
        except ParseException,x:
            print "*",x.message
        print

