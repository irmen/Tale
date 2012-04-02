"""
Unit tests for the Soul

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import unittest
import mudlib.player
import mudlib.npc
import mudlib.soul
import mudlib.base
import mudlib.errors

class TestSoul(unittest.TestCase):
    def testSpacify(self):
        soul = mudlib.soul.Soul()
        self.assertEqual("", mudlib.soul.spacify(""))
        self.assertEqual(" abc", mudlib.soul.spacify("abc"))
        self.assertEqual(" abc", mudlib.soul.spacify(" abc"))
        self.assertEqual(" abc", mudlib.soul.spacify("  abc"))
        self.assertEqual(" abc", mudlib.soul.spacify("  \t\tabc"))
        self.assertEqual(" \nabc", mudlib.soul.spacify("  \nabc"))

    def testUnknownVerb(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        with self.assertRaises(mudlib.soul.UnknownVerbException) as ex:
            parsed = mudlib.soul.ParseResults("_unknown_verb_")
            soul.process_verb_parsed(player, parsed)
        self.assertEqual("_unknown_verb_", str(ex.exception))
        self.assertEqual("_unknown_verb_", ex.exception.verb)
        self.assertEqual(None, ex.exception.words)
        self.assertEqual(None, ex.exception.qualifier)
        with self.assertRaises(mudlib.soul.UnknownVerbException) as ex:
            soul.process_verb(player, "fail _unknown_verb_ herp derp")
        self.assertEqual("_unknown_verb_", str(ex.exception))
        self.assertEqual("_unknown_verb_", ex.exception.verb)
        self.assertEqual(["_unknown_verb_", "herp", "derp"], ex.exception.words)
        self.assertEqual("fail", ex.exception.qualifier)

    def testExternalVerbs(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        with self.assertRaises(mudlib.soul.UnknownVerbException):
            soul.process_verb(player, "externalverb")
        verb, _ = soul.process_verb(player, "sit", external_verbs=set())
        self.assertEqual("sit", verb)
        with self.assertRaises(mudlib.soul.NonSoulVerb) as x:
            soul.process_verb(player, "sit", external_verbs={"sit"})
        self.assertEqual("sit", str(x.exception))
        self.assertEqual("sit", x.exception.parsed.verb)
        with self.assertRaises(mudlib.soul.NonSoulVerb) as x:
            soul.process_verb(player, "externalverb", external_verbs={"externalverb"})
        self.assertIsInstance(x.exception.parsed, mudlib.soul.ParseResults)
        self.assertEqual("externalverb", x.exception.parsed.verb)
        with self.assertRaises(mudlib.soul.NonSoulVerb) as x:
            soul.process_verb(player, "who who", external_verbs={"who"})
        self.assertEqual("who", x.exception.parsed.verb, "who as external verb needs to be processed as normal arg, not as adverb")
        self.assertEqual(["who"], x.exception.parsed.args, "who as external verb needs to be processed as normal arg, not as adverb")

    def testExternalVerbUnknownWords(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        with self.assertRaises(mudlib.soul.ParseError) as x:
            soul.process_verb(player, "sit door1")
        self.assertEqual("It's not clear what you mean by door1.", str(x.exception))
        with self.assertRaises(mudlib.soul.NonSoulVerb) as x:
            soul.process_verb(player, "sit door1 zen", external_verbs={"sit"})
        parsed=x.exception.parsed
        self.assertEqual("sit", parsed.verb)
        self.assertEqual(["door1", "zen"], parsed.args)
        self.assertEqual(["door1", "zen"], parsed.unrecognized)

    def testWho(self):
        player = mudlib.player.Player("fritz", "m")
        julie = mudlib.base.Living("julie", "f")
        harry = mudlib.base.Living("harry", "m")
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
        player = mudlib.player.Player("fritz", "m")
        julie = mudlib.base.Living("julie", "f")
        harry = mudlib.base.Living("harry", "m")
        self.assertEqual("your own", mudlib.soul.poss_replacement(player, player, player))  # your own foot
        self.assertEqual("his own",  mudlib.soul.poss_replacement(player, player, julie))   # his own foot
        self.assertEqual("harry's",   mudlib.soul.poss_replacement(player, harry, player))   # harrys foot
        self.assertEqual("harry's",   mudlib.soul.poss_replacement(player, harry, julie))    # harrys foot
        self.assertEqual("harry's",   mudlib.soul.poss_replacement(player, harry, None))     # harrys foot
        self.assertEqual("your",     mudlib.soul.poss_replacement(julie, player, player))   # your foot
        self.assertEqual("Fritz's",   mudlib.soul.poss_replacement(julie, player, harry))    # fritz' foot
        self.assertEqual("harry's",   mudlib.soul.poss_replacement(julie, harry, player))    # harrys foot
        self.assertEqual("your",     mudlib.soul.poss_replacement(julie, harry, harry))     # your foot
        self.assertEqual("harry's",   mudlib.soul.poss_replacement(julie, harry, None))      # harrys foot

    def testGender(self):
        soul = mudlib.soul.Soul()
        with self.assertRaises(KeyError):
            mudlib.player.Player("player", "x")
        player = mudlib.player.Player("julie", "f")
        parsed = mudlib.soul.ParseResults("stomp")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("Julie stomps her foot.", room_msg)
        player = mudlib.player.Player("fritz", "m")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("Fritz stomps his foot.", room_msg)
        player = mudlib.player.Player("zyzzy", "n")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("Zyzzy stomps its foot.", room_msg)

    def testIgnorewords(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("fritz", "m")
        with self.assertRaises(mudlib.soul.ParseError):
            soul.parse(player, "in")
        with self.assertRaises(mudlib.soul.ParseError):
            soul.parse(player, "and")
        with self.assertRaises(mudlib.soul.ParseError):
            soul.parse(player, "fail")
        with self.assertRaises(mudlib.soul.ParseError):
            soul.parse(player, "fail in")
        with self.assertRaises(mudlib.soul.UnknownVerbException) as x:
            soul.parse(player, "in fail")
        self.assertEqual("fail", x.exception.verb)
        parsed = soul.parse(player, "in sit")
        self.assertIsNone(parsed.qualifier)
        self.assertIsNone(parsed.adverb)
        self.assertEqual("sit", parsed.verb)
        parsed = soul.parse(player, "fail in sit")
        self.assertEqual("fail", parsed.qualifier)
        self.assertIsNone(parsed.adverb)
        self.assertEqual("sit", parsed.verb)

    def testMultiTarget(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        philip = mudlib.npc.NPC("philip", "m")
        kate = mudlib.npc.NPC("kate", "f", title="Kate")
        cat = mudlib.npc.NPC("cat", "n", title="the hairy cat")
        targets = {philip, kate, cat}
        # peer
        parsed = mudlib.soul.ParseResults("peer", who=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual(set(targets), who)
        self.assertTrue(player_msg.startswith("You peer at "))
        self.assertTrue("philip" in player_msg and "hairy cat" in player_msg and "Kate" in player_msg)
        self.assertTrue(room_msg.startswith("Julie peers at "))
        self.assertTrue("philip" in room_msg and "hairy cat" in room_msg and "Kate" in room_msg)
        self.assertEqual("Julie peers at you.", target_msg)
        # all/everyone
        player.move(mudlib.base.Location("somewhere"))
        livings = set(targets)
        livings.add(player)
        player.location.livings = livings
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "smile confusedly at everyone")
        self.assertEqual("smile", verb)
        self.assertEqual(3, len(who))
        self.assertEqual(set(targets), set(who), "player should not be in targets")
        self.assertTrue("philip" in player_msg and "the hairy cat" in player_msg and "Kate" in player_msg and not "yourself" in player_msg)
        self.assertTrue("philip" in room_msg and "the hairy cat" in room_msg and "Kate" in room_msg and not "herself" in room_msg)
        self.assertEqual("Julie smiles confusedly at you.", target_msg)

    def testWhoInfo(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        kate = mudlib.npc.NPC("kate", "f", title="Kate")
        cat = mudlib.npc.NPC("cat", "n", title="the hairy cat")
        player.move(mudlib.base.Location("somewhere"))
        cat.move(player.location)
        kate.move(player.location)
        parsed = soul.parse(player, "smile at cat and kate and myself")
        self.assertEqual(["cat", "kate", "myself"], parsed.args)
        self.assertEqual(3, len(parsed.who))
        self.assertEqual(3, len(parsed.who_info))
        self.assertTrue(cat in parsed.who and kate in parsed.who and player in parsed.who)
        self.assertEqual(0, parsed.who_info[cat].sequence)
        self.assertEqual(1, parsed.who_info[kate].sequence)
        self.assertEqual(2, parsed.who_info[player].sequence)
        self.assertEqual("at", parsed.who_info[cat].previous_word)
        self.assertEqual("and", parsed.who_info[kate].previous_word)
        self.assertEqual("and", parsed.who_info[player].previous_word)
        self.assertEqual([cat, kate, player], parsed.who_order)
        parsed = soul.parse(player, "smile at myself and kate and cat")
        self.assertEqual(["myself", "kate", "cat"], parsed.args)
        self.assertEqual([player, kate, cat], parsed.who_order)
        parsed = soul.parse(player, "smile at kate, cat and cat")
        self.assertEqual(["kate", "cat", "cat"], parsed.args, "deal with multiple occurences")
        self.assertEqual([kate, cat, cat], parsed.who_order, "deal with multiple occurrences")

    def testVerbTarget(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        player.set_title("the great %s, destroyer of worlds", True)
        player.move(mudlib.base.Location("somewhere"))
        npc_max = mudlib.npc.NPC("max", "m")
        player.location.livings = { npc_max, player }
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "grin")
        self.assertEqual("grin", verb)
        self.assertTrue(len(who) == 0)
        self.assertIsInstance(who, (set, frozenset), "targets must be a set for O(1) lookups")
        self.assertEqual("You grin evilly.", player_msg)
        self.assertEqual("The great Julie, destroyer of worlds grins evilly.", room_msg)
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "grin at max")
        self.assertEqual("grin", verb)
        self.assertTrue(len(who) == 1)
        self.assertIsInstance(who, (set, frozenset), "targets must be a set for O(1) lookups")
        self.assertEqual("max", list(who)[0].name)
        self.assertEqual("You grin evilly at max.", player_msg)
        self.assertEqual("The great Julie, destroyer of worlds grins evilly at max.", room_msg)
        self.assertEqual("The great Julie, destroyer of worlds grins evilly at you.", target_msg)
        # parsed results
        parsed = soul.parse(player, "grin at all")
        self.assertEqual("grin", parsed.verb)
        self.assertEqual({npc_max}, parsed.who, "parse('all') must result in only the npc, not the player")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertTrue(len(who) == 1)
        self.assertIsInstance(who, (set, frozenset), "targets must be a set for O(1) lookups")
        self.assertEqual("max", list(who)[0].name)
        self.assertEqual("You grin evilly at max.", player_msg)
        parsed = soul.parse(player, "grin at all and me")
        self.assertEqual("grin", parsed.verb)
        self.assertEqual({player, npc_max}, parsed.who, "parse('all and me') must include npc and the player")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual({npc_max}, who, "player should no longer be part of the remaining targets")
        self.assertTrue("yourself" in player_msg and "max" in player_msg)

    def testMessageQuote(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        # babble
        parsed = mudlib.soul.ParseResults("babble")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You babble something incoherently.", player_msg)
        self.assertEqual("Julie babbles something incoherently.", room_msg)
        # babble with message
        parsed.message = "blurp"
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You babble 'blurp' incoherently.", player_msg)
        self.assertEqual("Julie babbles 'blurp' incoherently.", room_msg)

    def testMessageQuoteParse(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        player.move(mudlib.base.Location("somewhere"))
        player.location.livings = { mudlib.npc.NPC("max", "m"), player }
        # whisper
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "whisper \"hello there\"")
        self.assertEqual("You whisper 'hello there'.", player_msg)
        self.assertEqual("Julie whispers 'hello there'.", room_msg)
        # whisper to a person
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "whisper to max \"hello there\"")
        self.assertEqual("You whisper 'hello there' to max.", player_msg)
        self.assertEqual("Julie whispers 'hello there' to max.", room_msg)
        # whisper to a person with adverb
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "whisper softly to max \"hello there\"")
        self.assertEqual("You whisper 'hello there' softly to max.", player_msg)
        self.assertEqual("Julie whispers 'hello there' softly to max.", room_msg)

    def testBodypart(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = {mudlib.npc.NPC("max", "m")}
        parsed = mudlib.soul.ParseResults("beep", who=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You triumphantly beep max on the nose.", player_msg)
        self.assertEqual("Julie triumphantly beeps max on the nose.", room_msg)
        self.assertEqual("Julie triumphantly beeps you on the nose.", target_msg)
        parsed.bodypart = "arm"
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You triumphantly beep max on the arm.", player_msg)
        self.assertEqual("Julie triumphantly beeps max on the arm.", room_msg)
        self.assertEqual("Julie triumphantly beeps you on the arm.", target_msg)
        # check handling of more than one bodypart
        with self.assertRaises(mudlib.soul.ParseError) as ex:
            soul.process_verb(player, "kick max side knee")
        self.assertEqual("You can't do that both in the side and on the knee.", str(ex.exception))

    def testQualifier(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = {mudlib.npc.NPC("max", "m")}
        parsed = mudlib.soul.ParseResults("tickle", who=targets, qualifier="fail")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You try to tickle max, but fail miserably.", player_msg)
        self.assertEqual("Julie tries to tickle max, but fails miserably.", room_msg)
        self.assertEqual("Julie tries to tickle you, but fails miserably.", target_msg)
        parsed.qualifier = "don't"
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You don't tickle max.", player_msg)
        self.assertEqual("Julie doesn't tickle max.", room_msg)
        self.assertEqual("Julie doesn't tickle you.", target_msg)
        parsed.qualifier = "suddenly"
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You suddenly tickle max.", player_msg)
        self.assertEqual("Julie suddenly tickles max.", room_msg)
        self.assertEqual("Julie suddenly tickles you.", target_msg)
        parsed = mudlib.soul.ParseResults("scream", qualifier="don't", message="I have no idea")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You don't scream 'I have no idea' loudly.", player_msg)
        self.assertEqual("Julie doesn't scream 'I have no idea' loudly.", room_msg)
        self.assertEqual("Julie doesn't scream 'I have no idea' loudly.", target_msg)

    def testQualifierParse(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "dont scream")
        self.assertEqual("don't scream", verb, "expected spell-corrected qualifier")
        self.assertEqual("You don't scream loudly.", player_msg)
        self.assertEqual("Julie doesn't scream loudly.", room_msg)
        self.assertEqual("Julie doesn't scream loudly.", target_msg)
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "don't scream")
        self.assertEqual("don't scream", verb)
        self.assertEqual("You don't scream loudly.", player_msg)
        self.assertEqual("Julie doesn't scream loudly.", room_msg)
        self.assertEqual("Julie doesn't scream loudly.", target_msg)
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "don't scream \"I have no idea\"")
        self.assertEqual("don't scream", verb)
        self.assertEqual("You don't scream 'I have no idea' loudly.", player_msg)
        self.assertEqual("Julie doesn't scream 'I have no idea' loudly.", room_msg)
        self.assertEqual("Julie doesn't scream 'I have no idea' loudly.", target_msg)
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "fail say")
        self.assertEqual("fail say", verb)
        self.assertEqual("You try to say nothing, but fail miserably.", player_msg)
        self.assertEqual("Julie tries to say nothing, but fails miserably.", room_msg)

    def testAdverbs(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f", "human")
        # check handling of more than one adverb
        with self.assertRaises(mudlib.soul.ParseError) as ex:
            soul.process_verb(player, "cough sickly and noisily")
        self.assertEqual("You can't do that both sickly and noisily.", str(ex.exception))
        # check handling of adverb prefix where there is 1 unique result
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "cough sic")
        self.assertEqual("You cough sickly.", player_msg)
        self.assertEqual("Julie coughs sickly.", room_msg)
        # check handling of adverb prefix where there are more results
        with self.assertRaises(mudlib.soul.ParseError) as ex:
            soul.process_verb(player, "cough si")
        self.assertEqual("What adverb did you mean: sickly, sideways, signally, significantly, or silently?", str(ex.exception))

    def testUnrecognisedWord(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f", "human")
        with self.assertRaises(mudlib.soul.ParseError):
            soul.process_verb(player, "cough hubbabubba")

    def testCheckNameWithSpaces(self):
        livings = {"rat": "RAT", "brown bird": "BROWN BIRD"}
        items = {"paper": "PAPER", "blue gem": "BLUE GEM", "dark red crystal": "DARK RED CRYSTAL"}
        result = mudlib.soul.check_name_with_spaces(["give","the","blue","gem","to","rat"], 0, livings, items)
        self.assertEqual((None,None,0), result)
        result = mudlib.soul.check_name_with_spaces(["give","the","blue","gem","to","rat"], 1, livings, items)
        self.assertEqual((None,None,0), result)
        result = mudlib.soul.check_name_with_spaces(["give","the","blue","gem","to","rat"], 4, livings, items)
        self.assertEqual((None,None,0), result)
        result = mudlib.soul.check_name_with_spaces(["give","the","blue","gem","to","rat"], 2, livings, items)
        self.assertEqual(("BLUE GEM","blue gem",2), result)
        result = mudlib.soul.check_name_with_spaces(["give","the","dark","red","crystal", "to","rat"], 2, livings, items)
        self.assertEqual(("DARK RED CRYSTAL","dark red crystal",3), result)
        result = mudlib.soul.check_name_with_spaces(["give","the","dark","red","paper", "to","rat"], 2, livings, items)
        self.assertEqual((None,None,0), result)
        result = mudlib.soul.check_name_with_spaces(["give", "paper", "to","brown", "bird"], 3, livings, items)
        self.assertEqual(("BROWN BIRD","brown bird",2), result)

    def testCheckNamesWithSpacesParsing(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        bird = mudlib.npc.NPC("brown bird", "f")
        room = mudlib.base.Location("somewhere")
        gate = mudlib.base.Exit(room, "the gate", direction="gate")
        door1 = mudlib.base.Exit(room, "door number one", direction="door one")
        door2 = mudlib.base.Exit(room, "door number two", direction="door two")
        room.add_exits([gate,door1,door2])
        bird.move(room)
        player.move(room)
        with self.assertRaises(mudlib.errors.ParseError) as x:
            soul.parse(player, "hug bird")
        self.assertEqual("It's not clear what you mean by bird.", str(x.exception))
        parsed=soul.parse(player, "hug brown bird affection")
        self.assertEqual("hug", parsed.verb)
        self.assertEqual("affectionately", parsed.adverb)
        self.assertEqual({bird}, parsed.who)
        # check spaces in exit names
        parsed = soul.parse(player, "gate", external_verbs=frozenset(room.exits))
        self.assertEqual("gate", parsed.verb)
        parsed = soul.parse(player, "enter gate", external_verbs={"enter"}, room_exits=player.location.exits)
        self.assertEqual("enter", parsed.verb)
        self.assertEqual(["gate"], parsed.args)
        self.assertEqual({gate}, parsed.who)
        with self.assertRaises(mudlib.soul.UnknownVerbException):
            soul.parse(player, "door", room_exits=player.location.exits)
        parsed = soul.parse(player, "enter door two", external_verbs={"enter"}, room_exits=player.location.exits)
        self.assertEqual("enter", parsed.verb)
        self.assertEqual(["door two"], parsed.args)
        self.assertEqual({door2}, parsed.who)
        with self.assertRaises(mudlib.soul.NonSoulVerb) as x:
            soul.parse(player, "door one", room_exits=player.location.exits)
        parsed = x.exception.parsed
        self.assertEqual("door one", parsed.verb)
        self.assertEqual({door1}, parsed.who)
        with self.assertRaises(mudlib.soul.NonSoulVerb) as x:
            soul.parse(player, "door two", room_exits=player.location.exits)
        parsed = x.exception.parsed
        self.assertEqual("door two", parsed.verb)
        self.assertEqual({door2}, parsed.who)

    def testEnterExits(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        room = mudlib.base.Location("somewhere")
        gate = mudlib.base.Exit(room, "gate", direction="gate")
        east = mudlib.base.Exit(room, "east", direction="east")
        door1 = mudlib.base.Exit(room, "door number one", direction="door one")
        room.add_exits([gate,door1,east])
        player.move(room)
        # known actions: enter/go/climb/crawl
        with self.assertRaises(mudlib.soul.NonSoulVerb) as x:
            soul.parse(player, "enter door one", room_exits=player.location.exits)
        parsed = x.exception.parsed
        self.assertEqual("door one", parsed.verb)
        self.assertEqual({door1}, parsed.who)
        with self.assertRaises(mudlib.soul.NonSoulVerb) as x:
            soul.parse(player, "climb gate", room_exits=player.location.exits)
        parsed = x.exception.parsed
        self.assertEqual("gate", parsed.verb)
        with self.assertRaises(mudlib.soul.NonSoulVerb) as x:
            soul.parse(player, "go east", room_exits=player.location.exits)
        parsed = x.exception.parsed
        self.assertEqual("east", parsed.verb)
        with self.assertRaises(mudlib.soul.NonSoulVerb) as x:
            soul.parse(player, "crawl east", room_exits=player.location.exits)
        parsed = x.exception.parsed
        self.assertEqual("east", parsed.verb)
        parsed = soul.parse(player, "jump west", room_exits=player.location.exits)
        self.assertEqual("jump", parsed.verb)
        self.assertEqual("westwards", parsed.adverb)

    def testParse(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f", "human")
        room = mudlib.base.Location("somewhere")
        room.add_exits([mudlib.base.Exit(room, "a door to the south", direction="south")])
        player.move(room)
        targets = { mudlib.npc.NPC("max", "m"), mudlib.npc.NPC("kate", "f"), mudlib.npc.NPC("dinosaur", "n") }
        targets_with_player = set(targets) | {player}
        player.location.livings = targets
        newspaper = mudlib.base.Item("newspaper")
        player.location.insert(newspaper, player)
        parsed = soul.parse(player, "fail grin sickly at everyone head")
        self.assertEqual("fail", parsed.qualifier)
        self.assertEqual("grin", parsed.verb)
        self.assertEqual("sickly", parsed.adverb)
        self.assertEqual("head", parsed.bodypart)
        self.assertEqual("", parsed.message)
        self.assertTrue(len(parsed.who) == 3)
        self.assertTrue(all(isinstance(x, mudlib.base.Living) for x in parsed.who), "parse must return Livings in 'who'")
        self.assertEqual(targets, parsed.who)
        parsed = soul.parse(player, "slap myself")
        self.assertEqual(None, parsed.qualifier)
        self.assertEqual("slap", parsed.verb)
        self.assertEqual(None, parsed.adverb)
        self.assertEqual(None, parsed.bodypart)
        self.assertEqual("", parsed.message)
        self.assertEqual({player}, parsed.who, "myself should be player")
        parsed = soul.parse(player, "slap all")
        self.assertEqual(None, parsed.qualifier)
        self.assertEqual("slap", parsed.verb)
        self.assertEqual(None, parsed.adverb)
        self.assertEqual(None, parsed.bodypart)
        self.assertEqual("", parsed.message)
        self.assertEqual(targets, parsed.who, "all should not include player")
        parsed = soul.parse(player, "slap all and myself")
        self.assertEqual(targets_with_player, parsed.who, "all and myself should include player")
        parsed = soul.parse(player, "slap newspaper")
        self.assertEqual({newspaper}, parsed.who, "must be able to perform soul verb on item")
        with self.assertRaises(mudlib.soul.ParseError) as x:
            soul.parse(player, "slap dino")
        self.assertEqual("Perhaps you meant dinosaur?", str(x.exception), "must suggest living with prefix")
        with self.assertRaises(mudlib.soul.ParseError) as x:
            soul.parse(player, "slap news")
        self.assertEqual("Perhaps you meant newspaper?", str(x.exception), "must suggest item with prefix")
        with self.assertRaises(mudlib.soul.ParseError) as x:
            soul.parse(player, "slap undefined")
        self.assertEqual("It's not clear what you mean by undefined.", str(x.exception))
        parsed = soul.parse(player, "smile west")
        self.assertEqual("westwards", parsed.adverb)
        with self.assertRaises(mudlib.soul.ParseError) as x:
            soul.parse(player, "smile north")
        self.assertEqual("What adverb did you mean: northeastwards, northwards, or northwestwards?", str(x.exception))
        parsed = soul.parse(player, "smile south")
        self.assertEqual(["south"], parsed.args, "south must be parsed as a normal arg because it's an exit in the room")
        parsed = soul.parse(player, "smile kate dinosaur and max")
        self.assertEqual(["kate", "dinosaur", "max"], parsed.args, "must be able to skip comma")
        self.assertEqual(3, len(parsed.who), "must be able to skip comma")
        parsed = soul.parse(player, "reply kate ofcourse,  darling.")
        self.assertEqual(["kate", "ofcourse,", "darling."], parsed.args, "must be able to skip comma")
        self.assertEqual(1, len(parsed.who))

    def testDEFA(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = {mudlib.npc.NPC("max", "m")}
        # grin
        parsed = mudlib.soul.ParseResults("grin")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You grin evilly.", player_msg)
        self.assertEqual("Julie grins evilly.", room_msg)
        # drool
        parsed = mudlib.soul.ParseResults("drool", who=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You drool on max.", player_msg)
        self.assertEqual("Julie drools on max.", room_msg)
        self.assertEqual("Julie drools on you.", target_msg)

    def testPREV(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = {mudlib.npc.NPC("max", "m")}
        # peer
        parsed = mudlib.soul.ParseResults("peer", who=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You peer at max.", player_msg)
        self.assertEqual("Julie peers at max.", room_msg)
        self.assertEqual("Julie peers at you.", target_msg)
        # tease
        parsed = mudlib.soul.ParseResults("tease", who=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You tease max.", player_msg)
        self.assertEqual("Julie teases max.", room_msg)
        self.assertEqual("Julie teases you.", target_msg)
        # turn
        parsed = mudlib.soul.ParseResults("turn", who=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You turn your head towards max.", player_msg)
        self.assertEqual("Julie turns her head towards max.", room_msg)
        self.assertEqual("Julie turns her head towards you.", target_msg)

    def testPHYS(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = {mudlib.npc.NPC("max", "m")}
        # require person
        with self.assertRaises(mudlib.errors.ParseError):
            parsed = mudlib.soul.ParseResults("bonk")
            soul.process_verb_parsed(player, parsed)
        # pounce
        parsed = mudlib.soul.ParseResults("pounce", who=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You pounce max playfully.", player_msg)
        self.assertEqual("Julie pounces max playfully.", room_msg)
        self.assertEqual("Julie pounces you playfully.", target_msg)
        # hold
        parsed = mudlib.soul.ParseResults("hold", who=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You hold max in your arms.", player_msg)
        self.assertEqual("Julie holds max in her arms.", room_msg)
        self.assertEqual("Julie holds you in her arms.", target_msg)

    def testSHRT(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        # faint
        parsed = mudlib.soul.ParseResults("faint", adverb="slowly")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You faint slowly.", player_msg)
        self.assertEqual("Julie faints slowly.", room_msg)
        # cheer
        parsed = mudlib.soul.ParseResults("cheer")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You cheer enthusiastically.", player_msg)
        self.assertEqual("Julie cheers enthusiastically.", room_msg)

    def testPERS(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = {mudlib.npc.NPC("max", "m")}
        # fear1
        parsed = mudlib.soul.ParseResults("fear")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You shiver with fear.", player_msg)
        self.assertEqual("Julie shivers with fear.", room_msg)
        # fear2
        parsed.who = targets
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You fear max.", player_msg)
        self.assertEqual("Julie fears max.", room_msg)
        self.assertEqual("Julie fears you.", target_msg)

    def testSIMP(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = {mudlib.npc.NPC("max", "m")}

        # yell 1
        parsed = mudlib.soul.ParseResults("yell")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You yell in a high pitched voice.", player_msg)
        self.assertEqual("Julie yells in a high pitched voice.", room_msg)
        # yell 2
        parsed.who = targets
        parsed.adverb = "angrily"
        parsed.message = "why"
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You yell 'why' angrily at max.", player_msg)
        self.assertEqual("Julie yells 'why' angrily at max.", room_msg)
        self.assertEqual("Julie yells 'why' angrily at you.", target_msg)
        # ask
        parsed = mudlib.soul.ParseResults("ask", who=targets, message="are you happy")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You ask max: are you happy?", player_msg)
        self.assertEqual("Julie asks max: are you happy?", room_msg)
        self.assertEqual("Julie asks you: are you happy?", target_msg)
        # puzzle1
        parsed = mudlib.soul.ParseResults("puzzle")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You look puzzled.", player_msg)
        self.assertEqual("Julie looks puzzled.", room_msg)
        # puzzle2
        parsed.who = targets
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You look puzzled at max.", player_msg)
        self.assertEqual("Julie looks puzzled at max.", room_msg)
        self.assertEqual("Julie looks puzzled at you.", target_msg)
        # chant1
        parsed = mudlib.soul.ParseResults("chant", adverb="merrily", message="tralala")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You merrily chant: tralala.", player_msg)
        self.assertEqual("Julie merrily chants: tralala.", room_msg)
        # chant2
        parsed = mudlib.soul.ParseResults("chant")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You chant: Hare Krishna Krishna Hare Hare.", player_msg)
        self.assertEqual("Julie chants: Hare Krishna Krishna Hare Hare.", room_msg)

    def testDEUX(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        # die
        parsed = mudlib.soul.ParseResults("die", adverb="suddenly")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You suddenly fall down and play dead.", player_msg)
        self.assertEqual("Julie suddenly falls to the ground, dead.", room_msg)
        # ah
        parsed = mudlib.soul.ParseResults("ah", adverb="rudely")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You go 'ah' rudely.", player_msg)
        self.assertEqual("Julie goes 'ah' rudely.", room_msg)

    def testQUAD(self):
        soul = mudlib.soul.Soul()
        player = mudlib.player.Player("julie", "f")
        targets = {mudlib.npc.NPC("max", "m")}
        # watch1
        parsed = mudlib.soul.ParseResults("watch")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You watch the surroundings carefully.", player_msg)
        self.assertEqual("Julie watches the surroundings carefully.", room_msg)
        # watch2
        parsed.who = targets
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You watch max carefully.", player_msg)
        self.assertEqual("Julie watches max carefully.", room_msg)
        self.assertEqual("Julie watches you carefully.", target_msg)
        # ayt
        parsed.verb = "ayt"
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual(set(targets), who)
        self.assertEqual("You wave your hand in front of max's face, is he there?", player_msg)
        self.assertEqual("Julie waves her hand in front of max's face, is he there?", room_msg)
        self.assertEqual("Julie waves her hand in front of your face, are you there?", target_msg)
        # ayt
        targets2 = {mudlib.npc.NPC("max", "m"), player}
        parsed.who = targets2
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertTrue(player_msg.startswith("You wave your hand in front of "))
        self.assertTrue("max's" in player_msg and "your own" in player_msg)
        self.assertTrue(room_msg.startswith("Julie waves her hand in front of "))
        self.assertTrue("max's" in room_msg and "her own" in room_msg)
        self.assertEqual("Julie waves her hand in front of your face, are you there?", target_msg)

    def testFULL(self):
        pass  # FULL is not yet used


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
