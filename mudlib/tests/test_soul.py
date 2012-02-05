import unittest
import mudlib.player
import mudlib.npc
import mudlib.soul
import mudlib.languagetools

class TestLanguagetools(unittest.TestCase):
    def testA(self):
        self.assertEqual("a house", mudlib.languagetools.a("house"))
        self.assertEqual("an egg", mudlib.languagetools.a("egg"))
        self.assertEqual("a university", mudlib.languagetools.a("university"))
        self.assertEqual("an unindent", mudlib.languagetools.a("unindent"))
        self.assertEqual("a history", mudlib.languagetools.a("history"))
    def testFullstop(self):
        self.assertEqual("a.", mudlib.languagetools.fullstop("a"))
        self.assertEqual("a.", mudlib.languagetools.fullstop("a "))
        self.assertEqual("a.", mudlib.languagetools.fullstop("a."))
        self.assertEqual("a?", mudlib.languagetools.fullstop("a?"))
        self.assertEqual("a!", mudlib.languagetools.fullstop("a!"))
        self.assertEqual("a;", mudlib.languagetools.fullstop("a", punct=";"))
    def testJoin(self):
        self.assertEqual("a", mudlib.languagetools.join(["a"]))
        self.assertEqual("a and b", mudlib.languagetools.join(["a", "b"]))
        self.assertEqual("a, b, and c", mudlib.languagetools.join(["a", "b", "c"]))
        self.assertEqual("a, b, or c", mudlib.languagetools.join(["a", "b", "c"], conj="or"))


class TestSoul(unittest.TestCase):
    def testSpacify(self):
        soul = mudlib.soul.Soul()
        self.assertEqual("", mudlib.soul.spacify(""))
        self.assertEqual(" abc", mudlib.soul.spacify("abc"))
        self.assertEqual(" abc", mudlib.soul.spacify(" abc"))
        self.assertEqual(" abc", mudlib.soul.spacify("  abc"))

    def testGender(self):
        soul = mudlib.soul.Soul()
        with self.assertRaises(KeyError):
            mudlib.player.Player("player", "x")
        player = mudlib.player.Player("julie", "f")
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "stomp")
        self.assertEqual("julie stomps her foot.", room_message)
        player = mudlib.player.Player("fritz", "m")
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "stomp")
        self.assertEqual("fritz stomps his foot.", room_message)
        player = mudlib.player.Player("zyzzy", "n")
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "stomp")
        self.assertEqual("zyzzy stomps its foot.", room_message)

    def testDEFA(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("player", "f")
        who = [mudlib.npc.NPC("fritz", "m"), mudlib.npc.NPC("julie", "f")]
        adverbs1 = ["xly"]
        bodyparts1 = ["knee"]
        adverbs2 = ["xly", "zly"]
        bodyparts2 = ["head", "knee"]
        soul.process_verb_parsed(player, "fart", who, adverbs2, "message", bodyparts2)

    def testPREV(self):
        soul = mudlib.soul.Soul()

    def testPHYS(self):
        soul = mudlib.soul.Soul()

    def testSHRT(self):
        soul = mudlib.soul.Soul()

    def testPERS(self):
        soul = mudlib.soul.Soul()

    def testSIMP(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]

        # yell 1
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "yell")
        self.assertTrue(len(who)==0)
        self.assertEqual("you yell in a high pitched voice.", player_message)
        self.assertEqual("julie yells in a high pitched voice.", room_message)
        # yell 2
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "yell", targets, adverbs=["angrily"], message="why")
        self.assertEqual(targets, who)
        self.assertEqual("you yell 'why' angrily at max.", player_message)
        self.assertEqual("julie yells 'why' angrily at max.", room_message)
        self.assertEqual("julie yells 'why' angrily at you.", target_message)
        # ask
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "ask", targets, message="are you happy")
        self.assertEqual(targets, who)
        self.assertEqual("you ask max: are you happy?", player_message)
        self.assertEqual("julie asks max: are you happy?", room_message)
        self.assertEqual("julie asks you: are you happy?", target_message)
        # puzzle1
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "puzzle")
        self.assertTrue(len(who)==0)
        self.assertEqual("you look puzzled.", player_message)
        self.assertEqual("julie looks puzzled.", room_message)
        # puzzle2
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "puzzle", targets)
        self.assertEqual(targets, who)
        self.assertEqual("you look puzzled at max.", player_message)
        self.assertEqual("julie looks puzzled at max.", room_message)
        self.assertEqual("julie looks puzzled at you.", target_message)
        # chant1
        # "chant":    ( SIMP, ( None, "Hare Krishna Krishna Hare Hare" ), " \nHOW chant$: \nWHAT", "" ),
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "chant", adverbs=["merrily"], message="tralala")
        self.assertTrue(len(who)==0)
        self.assertEqual("you merrily chant: tralala.", player_message)
        self.assertEqual("julie merrily chants: tralala.", room_message)
        # chant2
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "chant")
        self.assertTrue(len(who)==0)
        self.assertEqual("you chant: Hare Krishna Krishna Hare Hare.", player_message)
        self.assertEqual("julie chants: Hare Krishna Krishna Hare Hare.", room_message)


    def testDEUX(self):
        soul = mudlib.soul.Soul()

    def testQUAD(self):
        soul = mudlib.soul.Soul()

    def testFULL(self):
        soul = mudlib.soul.Soul()



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()



