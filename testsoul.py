import mudlib.player
import mudlib.baseobjects
import mudlib.languagetools as lang
from mudlib.soul import ParseException, UnknownVerbException

player = mudlib.player.Player("fritz", "m", "human")
player.location = mudlib.baseobjects.Location("somewhere")
player.location.livings = { mudlib.baseobjects.Living("max","m", title="mad Max", description="he seems a bit mad"),
                            mudlib.baseobjects.Living("julie","f", title="attractive Julie", description="she is quite stunning"),
                            player }

def ask_user_input():
    cmd = raw_input("command?> ")
    verb, (who, player_message, room_message, target_message) = player.socialize(cmd)
    print "PLAYER:", player_message
    print "ROOM:", room_message
    targets = ", ".join([target.name for target in who])
    print "TARGETS %s: %s" % (targets, target_message)

def examine(words):
    if len(words)<=1:
        print "YOU SEE:", lang.join([living.title for living in player.location.livings if living is not player])
    else:
        for living in player.location.livings:
            if living.name == words[1]:
                print "%s; %s" % (living.title, living.description)
                found = True
        if not found:
            print "* %s isn't here." % words[1]

if __name__ == "__main__":
    while True:
        try:
            ask_user_input()
        except UnknownVerbException,x:
            if x.verb in ("who", "look", "exa", "examine"):
                examine(x.words)
            elif x.verb=="quit":
                break
            else:
                print "* I don't understand the verb %s." % x.verb
        except ParseException,x:
            print "*",x.message
        print

