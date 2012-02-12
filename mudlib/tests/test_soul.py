import unittest
import mudlib.player
import mudlib.npc
import mudlib.soul
import mudlib.baseobjects
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
    def testAdverbs(self):
        self.assertTrue(len(mudlib.languagetools.ADVERB_LIST)>0)
        self.assertTrue("noisily" in mudlib.languagetools.ADVERBS)
        self.assertFalse("zzzzzzzzzz" in mudlib.languagetools.ADVERBS)
        self.assertEqual(['nobly', 'nocturnally', 'noiselessly', 'noisily', 'nominally'], mudlib.languagetools.adverb_by_prefix("no", 5))
        self.assertEqual(['nobly'], mudlib.languagetools.adverb_by_prefix("no", 1))
        self.assertEqual(["acapella"], mudlib.languagetools.adverb_by_prefix("a",1))
        self.assertEqual([], mudlib.languagetools.adverb_by_prefix("zzzzzzzzzz"))


class TestSoul(unittest.TestCase):
    def testSpacify(self):
        soul = mudlib.soul.Soul()
        self.assertEqual("", mudlib.soul.spacify(""))
        self.assertEqual(" abc", mudlib.soul.spacify("abc"))
        self.assertEqual(" abc", mudlib.soul.spacify(" abc"))
        self.assertEqual(" abc", mudlib.soul.spacify("  abc"))

    def testUnknownVerb(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        with self.assertRaises(mudlib.soul.UnknownVerbException):
            soul.process_verb_parsed(player, "_unknown_verb_")

    def testWho(self):
        player = mudlib.player.Player("fritz","m")
        julie = mudlib.baseobjects.Living("julie", "f")
        harry = mudlib.baseobjects.Living("harry", "m")
        self.assertEqual("yourself", mudlib.soul.who_replacement(player, player, player))  # you kick yourself
        self.assertEqual("himself",  mudlib.soul.who_replacement(player, player, julie))   # fritz kicks himself
        self.assertEqual("harry",    mudlib.soul.who_replacement(player, harry, player))   # you kick harry
        self.assertEqual("harry",    mudlib.soul.who_replacement(player, harry, julie))    # fritz kicks harry
        self.assertEqual("harry",    mudlib.soul.who_replacement(player, harry, None))     # fritz kicks harry
        self.assertEqual("you",      mudlib.soul.who_replacement(julie, player, player))  # julie kicks you
        self.assertEqual("fritz",    mudlib.soul.who_replacement(julie, player, harry))   # julie kicks fritz
        self.assertEqual("harry",    mudlib.soul.who_replacement(julie, harry, player))   # julie kicks harry
        self.assertEqual("you",      mudlib.soul.who_replacement(julie, harry, harry))    # julie kicks you
        self.assertEqual("harry",    mudlib.soul.who_replacement(julie, harry, None))     # julie kicks harry

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

    def testMultiTarget(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m"), mudlib.npc.NPC("kate","f"), mudlib.npc.NPC("the cat", "n")]
        # peer
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "peer", targets)
        self.assertEqual(targets, who)
        self.assertEqual("you peer at max, kate, and the cat.", player_message)
        self.assertEqual("julie peers at max, kate, and the cat.", room_message)
        self.assertEqual("julie peers at you.", target_message)

    def testVerbTarget(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        player.location = mudlib.baseobjects.Location("somewhere")
        player.location.all_livings = {"max": mudlib.npc.NPC("max","m")}
        verb, (who, player_message, room_message, target_message) = soul.process_verb(player, "grin")
        self.assertEqual("grin", verb)
        self.assertTrue(len(who)==0)
        self.assertEqual("you grin evilly.", player_message)
        self.assertEqual("julie grins evilly.", room_message)
        verb, (who, player_message, room_message, target_message) = soul.process_verb(player, "grin at max")
        self.assertEqual("grin", verb)
        self.assertTrue(len(who)==1)
        self.assertEqual("max", who[0].name)
        self.assertEqual("you grin evilly at max.", player_message)
        self.assertEqual("julie grins evilly at max.", room_message)
        self.assertEqual("julie grins evilly at you.", target_message)

    def testMessageQuote(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m"), mudlib.npc.NPC("kate","f"), mudlib.npc.NPC("the cat", "n")]
        # babble
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "babble")
        self.assertEqual("you babble something incoherently.", player_message)
        self.assertEqual("julie babbles something incoherently.", room_message)
        # babble with message
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "babble", message="blurp")
        self.assertEqual("you babble 'blurp' incoherently.", player_message)
        self.assertEqual("julie babbles 'blurp' incoherently.", room_message)

    def testBodypart(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "beep", targets)
        self.assertEqual("you triumphantly beep max on the nose.", player_message)
        self.assertEqual("julie triumphantly beeps max on the nose.", room_message)
        self.assertEqual("julie triumphantly beeps you on the nose.", target_message)
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "beep", targets, bodypart="arm")
        self.assertEqual("you triumphantly beep max on the arm.", player_message)
        self.assertEqual("julie triumphantly beeps max on the arm.", room_message)
        self.assertEqual("julie triumphantly beeps you on the arm.", target_message)

    def testQualifier(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "tickle", targets, qualifier="fail")
        self.assertEqual("you try to tickle max, but fail miserably.", player_message)
        self.assertEqual("julie tries to tickle max, but fails miserably.", room_message)
        self.assertEqual("julie tries to tickle you, but fails miserably.", target_message)
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "tickle", targets, qualifier="don't")
        self.assertEqual("you don't tickle max.", player_message)
        self.assertEqual("julie doesn't tickle max.", room_message)
        self.assertEqual("julie doesn't tickle you.", target_message)
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "tickle", targets, qualifier="suddenly")
        self.assertEqual("you suddenly tickle max.", player_message)
        self.assertEqual("julie suddenly tickles max.", room_message)
        self.assertEqual("julie suddenly tickles you.", target_message)

    def testDEFA(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        # grin
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "grin")
        self.assertEqual("you grin evilly.", player_message)
        self.assertEqual("julie grins evilly.", room_message)
        # drool
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "drool", targets)
        self.assertEqual("you drool on max.", player_message)
        self.assertEqual("julie drools on max.", room_message)
        self.assertEqual("julie drools on you.", target_message)

    def testPREV(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        # peer
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "peer", targets)
        self.assertEqual(targets, who)
        self.assertEqual("you peer at max.", player_message)
        self.assertEqual("julie peers at max.", room_message)
        self.assertEqual("julie peers at you.", target_message)
        # tease
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "tease", targets)
        self.assertEqual(targets, who)
        self.assertEqual("you tease max.", player_message)
        self.assertEqual("julie teases max.", room_message)
        self.assertEqual("julie teases you.", target_message)

    def testPHYS(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        # require person
        with self.assertRaises(mudlib.soul.SoulException):
            soul.process_verb_parsed(player, "bonk")
        # pounce
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "pounce", targets)
        self.assertEqual(targets, who)
        self.assertEqual("you pounce max playfully.", player_message)
        self.assertEqual("julie pounces max playfully.", room_message)
        self.assertEqual("julie pounces you playfully.", target_message)
        # hold
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "hold", targets)
        self.assertEqual(targets, who)
        self.assertEqual("you hold max in your arms.", player_message)
        self.assertEqual("julie holds max in her arms.", room_message)
        self.assertEqual("julie holds you in her arms.", target_message)

    def testSHRT(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        # faint
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "faint", adverb="slowly")
        self.assertTrue(len(who)==0)
        self.assertEqual("you faint slowly.", player_message)
        self.assertEqual("julie faints slowly.", room_message)
        # cheer
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "cheer")
        self.assertTrue(len(who)==0)
        self.assertEqual("you cheer enthusiastically.", player_message)
        self.assertEqual("julie cheers enthusiastically.", room_message)

    def testPERS(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        # fear1
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "fear")
        self.assertTrue(len(who)==0)
        self.assertEqual("you shiver with fear.", player_message)
        self.assertEqual("julie shivers with fear.", room_message)
        # fear2
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "fear", targets)
        self.assertEqual(targets, who)
        self.assertEqual("you fear max.", player_message)
        self.assertEqual("julie fears max.", room_message)
        self.assertEqual("julie fears you.", target_message)

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
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "yell", targets, adverb="angrily", message="why")
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
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "chant", adverb="merrily", message="tralala")
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
        player = mudlib.player.Player("julie", "f")
        # die
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "die", adverb="suddenly")
        self.assertTrue(len(who)==0)
        self.assertEqual("you suddenly fall down and play dead.", player_message)
        self.assertEqual("julie suddenly falls to the ground, dead.", room_message)
        # go1
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "go", adverb="rudely", message="blurp")
        self.assertTrue(len(who)==0)
        self.assertEqual("you go 'blurp' rudely.", player_message)
        self.assertEqual("julie goes 'blurp' rudely.", room_message)
        # go2
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "go")
        self.assertTrue(len(who)==0)
        self.assertEqual("you go 'ah'.", player_message)
        self.assertEqual("julie goes 'ah'.", room_message)

    def testQUAD(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        # watch1
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "watch")
        self.assertTrue(len(who)==0)
        self.assertEqual("you watch the surroundings carefully.", player_message)
        self.assertEqual("julie watches the surroundings carefully.", room_message)
        # watch2
        who, player_message, room_message, target_message = soul.process_verb_parsed(player, "watch", targets)
        self.assertEqual(targets, who)
        self.assertEqual("you watch max carefully.", player_message)
        self.assertEqual("julie watches max carefully.", room_message)
        self.assertEqual("julie watches you carefully.", target_message)

    def testFULL(self):
        pass  # FULL is not yet used


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()



