import unittest
import mudlib.player
import mudlib.npc
import mudlib.soul
import mudlib.baseobjects


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
        with self.assertRaises(mudlib.soul.UnknownVerbException) as ex:
            soul.process_verb_parsed(player, "_unknown_verb_")
        self.assertEqual("_unknown_verb_", ex.exception.message)
        self.assertEqual("_unknown_verb_", ex.exception.verb)
        self.assertEqual(None, ex.exception.words)
        self.assertEqual(None, ex.exception.qualifier)
        with self.assertRaises(mudlib.soul.UnknownVerbException) as ex:
            soul.process_verb(player, "fail _unknown_verb_ herp derp")
        self.assertEqual("_unknown_verb_", ex.exception.message)
        self.assertEqual("_unknown_verb_", ex.exception.verb)
        self.assertEqual(["_unknown_verb_", "herp", "derp"], ex.exception.words)
        self.assertEqual("fail", ex.exception.qualifier)

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
        self.assertEqual("Fritz",    mudlib.soul.who_replacement(julie, player, harry))   # julie kicks fritz
        self.assertEqual("harry",    mudlib.soul.who_replacement(julie, harry, player))   # julie kicks harry
        self.assertEqual("you",      mudlib.soul.who_replacement(julie, harry, harry))    # julie kicks you
        self.assertEqual("harry",    mudlib.soul.who_replacement(julie, harry, None))     # julie kicks harry

    def testPoss(self):
        player = mudlib.player.Player("fritz","m")
        julie = mudlib.baseobjects.Living("julie", "f")
        harry = mudlib.baseobjects.Living("harry", "m")
        self.assertEqual("your own", mudlib.soul.poss_replacement(player, player, player))  # your own foot
        self.assertEqual("his own",  mudlib.soul.poss_replacement(player, player, julie))   # his own foot
        self.assertEqual("harrys",   mudlib.soul.poss_replacement(player, harry, player))   # harrys foot
        self.assertEqual("harrys",   mudlib.soul.poss_replacement(player, harry, julie))    # harrys foot
        self.assertEqual("harrys",   mudlib.soul.poss_replacement(player, harry, None))     # harrys foot
        self.assertEqual("your",     mudlib.soul.poss_replacement(julie, player, player))   # your foot
        self.assertEqual("Fritz'",   mudlib.soul.poss_replacement(julie, player, harry))    # fritz' foot
        self.assertEqual("harrys",   mudlib.soul.poss_replacement(julie, harry, player))    # harrys foot
        self.assertEqual("your",     mudlib.soul.poss_replacement(julie, harry, harry))     # your foot
        self.assertEqual("harrys",   mudlib.soul.poss_replacement(julie, harry, None))      # harrys foot

    def testGender(self):
        soul = mudlib.soul.Soul()
        with self.assertRaises(KeyError):
            mudlib.player.Player("player", "x")
        player = mudlib.player.Player("julie", "f")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "stomp")
        self.assertEqual("Julie stomps her foot.", room_msg)
        player = mudlib.player.Player("fritz", "m")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "stomp")
        self.assertEqual("Fritz stomps his foot.", room_msg)
        player = mudlib.player.Player("zyzzy", "n")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "stomp")
        self.assertEqual("Zyzzy stomps its foot.", room_msg)

    def testMultiTarget(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m"), mudlib.npc.NPC("kate","f",title="Kate"), mudlib.npc.NPC("cat", "n", title="the hairy cat")]
        # peer
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "peer", targets)
        self.assertEqual(targets, who)
        self.assertEqual("You peer at max, Kate, and the hairy cat.", player_msg)
        self.assertEqual("Julie peers at max, Kate, and the hairy cat.", room_msg)
        self.assertEqual("Julie peers at you.", target_msg)
        # all/everyone
        player.location = mudlib.baseobjects.Location("somewhere")
        livings = set(targets)
        livings.add(player)
        player.location.livings = livings
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "smile confusedly at everyone")
        self.assertEqual("smile", verb)
        self.assertEqual(3, len(who))
        self.assertEqual(set(targets), set(who), "player should not be in targets")
        self.assertTrue("max" in player_msg and "the hairy cat" in player_msg and "Kate" in player_msg and "yourself" in player_msg)
        self.assertTrue("max" in room_msg and "the hairy cat" in room_msg and "Kate" in room_msg and "herself" in room_msg)
        self.assertEqual("Julie smiles confusedly at you.", target_msg)

    def testVerbTarget(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        player.location = mudlib.baseobjects.Location("somewhere")
        player.location.livings = { mudlib.npc.NPC("max","m"), player }
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "grin")
        self.assertEqual("grin", verb)
        self.assertTrue(len(who)==0)
        self.assertEqual("You grin evilly.", player_msg)
        self.assertEqual("Julie grins evilly.", room_msg)
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "grin at max")
        self.assertEqual("grin", verb)
        self.assertTrue(len(who)==1)
        self.assertEqual("max", who[0].name)
        self.assertEqual("You grin evilly at max.", player_msg)
        self.assertEqual("Julie grins evilly at max.", room_msg)
        self.assertEqual("Julie grins evilly at you.", target_msg)

    def testMessageQuote(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        # babble
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "babble")
        self.assertEqual("You babble something incoherently.", player_msg)
        self.assertEqual("Julie babbles something incoherently.", room_msg)
        # babble with message
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "babble", message="blurp")
        self.assertEqual("You babble 'blurp' incoherently.", player_msg)
        self.assertEqual("Julie babbles 'blurp' incoherently.", room_msg)

    def testBodypart(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "beep", targets)
        self.assertEqual("You triumphantly beep max on the nose.", player_msg)
        self.assertEqual("Julie triumphantly beeps max on the nose.", room_msg)
        self.assertEqual("Julie triumphantly beeps you on the nose.", target_msg)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "beep", targets, bodypart="arm")
        self.assertEqual("You triumphantly beep max on the arm.", player_msg)
        self.assertEqual("Julie triumphantly beeps max on the arm.", room_msg)
        self.assertEqual("Julie triumphantly beeps you on the arm.", target_msg)
        # check handling of more than one bodypart
        with self.assertRaises(mudlib.soul.ParseException) as ex:
            soul.process_verb(player, "kick max side knee")
        self.assertEqual("You can't do that both in the side and on the knee.", ex.exception.message)

    def testQualifier(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "tickle", targets, qualifier="fail")
        self.assertEqual("You try to tickle max, but fail miserably.", player_msg)
        self.assertEqual("Julie tries to tickle max, but fails miserably.", room_msg)
        self.assertEqual("Julie tries to tickle you, but fails miserably.", target_msg)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "tickle", targets, qualifier="don't")
        self.assertEqual("You don't tickle max.", player_msg)
        self.assertEqual("Julie doesn't tickle max.", room_msg)
        self.assertEqual("Julie doesn't tickle you.", target_msg)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "tickle", targets, qualifier="suddenly")
        self.assertEqual("You suddenly tickle max.", player_msg)
        self.assertEqual("Julie suddenly tickles max.", room_msg)
        self.assertEqual("Julie suddenly tickles you.", target_msg)

    def testAdverbs(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f", "human")
        # check handling of more than one adverb
        with self.assertRaises(mudlib.soul.ParseException) as ex:
            soul.process_verb(player, "cough sickly and noisily")
        self.assertEqual("You can't do that both sickly and noisily.", ex.exception.message)
        # check handling of adverb prefix where there is 1 unique result
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "cough sic")
        self.assertEqual("You cough sickly.", player_msg)
        self.assertEqual("Julie coughs sickly.", room_msg)
        # check handling of adverb prefix where there are more results
        with self.assertRaises(mudlib.soul.ParseException) as ex:
            soul.process_verb(player, "cough si")
        self.assertEqual("What adverb did you mean: sickly, sideways, signally, significantly, or silently?", ex.exception.message)

    def testUnrecognisedWord(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f", "human")
        with self.assertRaises(mudlib.soul.ParseException):
            soul.process_verb(player, "cough hubbabubba")

    def testParse(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f", "human")
        player.location = mudlib.baseobjects.Location("somewhere")
        targets = { mudlib.npc.NPC("max","m"), mudlib.npc.NPC("kate","f"), mudlib.npc.NPC("the cat", "n") }
        player.location.livings = targets
        qualifier, verb, who, adverb, message, bodypart = soul.parse(player, "fail grin sickly at everyone head")
        self.assertEqual("fail", qualifier)
        self.assertEqual("grin", verb)
        self.assertEqual("sickly", adverb)
        self.assertEqual("head", bodypart)
        self.assertEqual("", message)
        self.assertTrue(len(who)==3)
        self.assertTrue(all(type(x) is str for x in who), "parse must return only strings")
        self.assertEqual({"max","kate","the cat"}, who)
        qualifier, verb, who, adverb, message, bodypart = soul.parse(player, "slap myself")
        self.assertTrue(all(type(x) is str for x in who), "parse must return only strings")
        self.assertEqual(None, qualifier)
        self.assertEqual("slap", verb)
        self.assertEqual(None, adverb)
        self.assertEqual(None, bodypart)
        self.assertEqual("", message)
        self.assertTrue(len(who)==1)
        self.assertEqual({"julie"}, who)

    def testDEFA(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        # grin
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "grin")
        self.assertEqual("You grin evilly.", player_msg)
        self.assertEqual("Julie grins evilly.", room_msg)
        # drool
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "drool", targets)
        self.assertEqual("You drool on max.", player_msg)
        self.assertEqual("Julie drools on max.", room_msg)
        self.assertEqual("Julie drools on you.", target_msg)

    def testPREV(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        # peer
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "peer", targets)
        self.assertEqual("You peer at max.", player_msg)
        self.assertEqual("Julie peers at max.", room_msg)
        self.assertEqual("Julie peers at you.", target_msg)
        # tease
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "tease", targets)
        self.assertEqual("You tease max.", player_msg)
        self.assertEqual("Julie teases max.", room_msg)
        self.assertEqual("Julie teases you.", target_msg)

    def testPHYS(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        # require person
        with self.assertRaises(mudlib.soul.SoulException):
            soul.process_verb_parsed(player, "bonk")
        # pounce
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "pounce", targets)
        self.assertEqual("You pounce max playfully.", player_msg)
        self.assertEqual("Julie pounces max playfully.", room_msg)
        self.assertEqual("Julie pounces you playfully.", target_msg)
        # hold
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "hold", targets)
        self.assertEqual("You hold max in your arms.", player_msg)
        self.assertEqual("Julie holds max in her arms.", room_msg)
        self.assertEqual("Julie holds you in her arms.", target_msg)

    def testSHRT(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        # faint
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "faint", adverb="slowly")
        self.assertEqual("You faint slowly.", player_msg)
        self.assertEqual("Julie faints slowly.", room_msg)
        # cheer
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "cheer")
        self.assertEqual("You cheer enthusiastically.", player_msg)
        self.assertEqual("Julie cheers enthusiastically.", room_msg)

    def testPERS(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        # fear1
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "fear")
        self.assertEqual("You shiver with fear.", player_msg)
        self.assertEqual("Julie shivers with fear.", room_msg)
        # fear2
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "fear", targets)
        self.assertEqual("You fear max.", player_msg)
        self.assertEqual("Julie fears max.", room_msg)
        self.assertEqual("Julie fears you.", target_msg)

    def testSIMP(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]

        # yell 1
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "yell")
        self.assertEqual("You yell in a high pitched voice.", player_msg)
        self.assertEqual("Julie yells in a high pitched voice.", room_msg)
        # yell 2
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "yell", targets, adverb="angrily", message="why")
        self.assertEqual("You yell 'why' angrily at max.", player_msg)
        self.assertEqual("Julie yells 'why' angrily at max.", room_msg)
        self.assertEqual("Julie yells 'why' angrily at you.", target_msg)
        # ask
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "ask", targets, message="are you happy")
        self.assertEqual("You ask max: are you happy?", player_msg)
        self.assertEqual("Julie asks max: are you happy?", room_msg)
        self.assertEqual("Julie asks you: are you happy?", target_msg)
        # puzzle1
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "puzzle")
        self.assertEqual("You look puzzled.", player_msg)
        self.assertEqual("Julie looks puzzled.", room_msg)
        # puzzle2
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "puzzle", targets)
        self.assertEqual("You look puzzled at max.", player_msg)
        self.assertEqual("Julie looks puzzled at max.", room_msg)
        self.assertEqual("Julie looks puzzled at you.", target_msg)
        # chant1
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "chant", adverb="merrily", message="tralala")
        self.assertEqual("You merrily chant: tralala.", player_msg)
        self.assertEqual("Julie merrily chants: tralala.", room_msg)
        # chant2
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "chant")
        self.assertEqual("You chant: Hare Krishna Krishna Hare Hare.", player_msg)
        self.assertEqual("Julie chants: Hare Krishna Krishna Hare Hare.", room_msg)

    def testDEUX(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        # die
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "die", adverb="suddenly")
        self.assertEqual("You suddenly fall down and play dead.", player_msg)
        self.assertEqual("Julie suddenly falls to the ground, dead.", room_msg)
        # go1
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "go", adverb="rudely", message="blurp")
        self.assertEqual("You go 'blurp' rudely.", player_msg)
        self.assertEqual("Julie goes 'blurp' rudely.", room_msg)
        # go2
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "go")
        self.assertEqual("You go 'ah'.", player_msg)
        self.assertEqual("Julie goes 'ah'.", room_msg)

    def testQUAD(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = [mudlib.npc.NPC("max","m")]
        # watch1
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "watch")
        self.assertEqual("You watch the surroundings carefully.", player_msg)
        self.assertEqual("Julie watches the surroundings carefully.", room_msg)
        # watch2
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "watch", targets)
        self.assertEqual("You watch max carefully.", player_msg)
        self.assertEqual("Julie watches max carefully.", room_msg)
        self.assertEqual("Julie watches you carefully.", target_msg)
        # ayt
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "ayt", targets)
        self.assertEqual(targets, who)
        self.assertEqual("You wave your hand in front of max' face, is he there?", player_msg)
        self.assertEqual("Julie waves her hand in front of max' face, is he there?", room_msg)
        self.assertEqual("Julie waves her hand in front of your face, are you there?", target_msg)
        # ayt
        targets2 = [mudlib.npc.NPC("max","m"), player]
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, "ayt", targets2)
        self.assertEqual("You wave your hand in front of max' and your own face, are they there?", player_msg)
        self.assertEqual("Julie waves her hand in front of max' and her own face, are they there?", room_msg)
        self.assertEqual("Julie waves her hand in front of your face, are you there?", target_msg)

    def testFULL(self):
        pass  # FULL is not yet used


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()



