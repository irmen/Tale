"""
Unit tests for the Soul

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import unittest
import collections

import tale
import tale.base
import tale.errors
import tale.player
import tale.verbdefs
from tale.story import StoryConfig
from tests.supportstuff import FakeDriver


class TestSoul(unittest.TestCase):
    def setUp(self):
        tale.mud_context.driver = FakeDriver()
        tale.mud_context.config = StoryConfig()
        tale.mud_context.resources = tale.mud_context.driver.resources

    def testSpacify(self):
        soul = tale.base.Soul()
        self.assertEqual("", soul.spacify(""))
        self.assertEqual(" abc", soul.spacify("abc"))
        self.assertEqual(" abc", soul.spacify(" abc"))
        self.assertEqual(" abc", soul.spacify("  abc"))
        self.assertEqual(" abc", soul.spacify("  \t\tabc"))
        self.assertEqual(" \nabc", soul.spacify("  \nabc"))

    def testUnknownVerb(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        with self.assertRaises(tale.errors.UnknownVerbException) as ex:
            parsed = tale.base.ParseResult("_unknown_verb_")
            soul.process_verb_parsed(player, parsed)
        self.assertEqual("_unknown_verb_", str(ex.exception))
        self.assertEqual("_unknown_verb_", ex.exception.verb)
        self.assertEqual([], ex.exception.words)
        self.assertEqual(None, ex.exception.qualifier)
        with self.assertRaises(tale.errors.UnknownVerbException) as ex:
            soul.process_verb(player, "fail _unknown_verb_ herp derp")
        self.assertEqual("_unknown_verb_", ex.exception.verb)
        self.assertEqual("fail", ex.exception.qualifier)
        self.assertEqual(["_unknown_verb_", "herp", "derp"], ex.exception.words)
        self.assertTrue(soul.is_verb("bounce"))
        self.assertFalse(soul.is_verb("_unknown_verb_"))

    def testAdverbWithoutVerb(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        with self.assertRaises(tale.errors.UnknownVerbException) as ex:
            soul.parse(player, "forg")     # forgetfully etc.
        self.assertEqual("forg", ex.exception.verb)
        with self.assertRaises(tale.errors.ParseError) as ex:
            soul.parse(player, "giggle forg")     # forgetfully etc.
        self.assertEqual("What adverb did you mean: forgetfully or forgivingly?", str(ex.exception))

    def testExternalVerbs(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        with self.assertRaises(tale.errors.UnknownVerbException):
            soul.process_verb(player, "externalverb")
        verb, _ = soul.process_verb(player, "sit", external_verbs=set())
        self.assertEqual("sit", verb)
        with self.assertRaises(tale.errors.NonSoulVerb) as x:
            soul.process_verb(player, "sit", external_verbs={"sit"})
        self.assertEqual("sit", str(x.exception))
        self.assertEqual("sit", x.exception.parsed.verb)
        with self.assertRaises(tale.errors.NonSoulVerb) as x:
            soul.process_verb(player, "externalverb", external_verbs={"externalverb"})
        self.assertIsInstance(x.exception.parsed, tale.base.ParseResult)
        self.assertEqual("externalverb", x.exception.parsed.verb)
        with self.assertRaises(tale.errors.NonSoulVerb) as x:
            soul.process_verb(player, "who who", external_verbs={"who"})
        self.assertEqual("who", x.exception.parsed.verb, "who as external verb must be processed as normal arg, not as adverb")
        self.assertEqual(["who"], x.exception.parsed.args, "who as external verb must be processed as normal arg, not as adverb")

    def testExternalVerbUnknownWords(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        with self.assertRaises(tale.errors.ParseError) as x:
            soul.process_verb(player, "sit door1")
        self.assertEqual("It's not clear what you mean by 'door1'.", str(x.exception))
        with self.assertRaises(tale.errors.NonSoulVerb) as x:
            soul.process_verb(player, "sit door1 zen", external_verbs={"sit"})
        parsed = x.exception.parsed
        self.assertEqual("sit", parsed.verb)
        self.assertEqual(["door1", "zen"], parsed.args)
        self.assertEqual(["door1", "zen"], parsed.unrecognized)

    def testWho(self):
        player = tale.player.Player("fritz", "m")
        julie = tale.base.Living("julie", "f", race="human")
        harry = tale.base.Living("harry", "m", race="human")
        soul = tale.base.Soul()
        self.assertEqual("yourself", soul.who_replacement(player, player, player))  # you kick yourself
        self.assertEqual("himself", soul.who_replacement(player, player, julie))   # fritz kicks himself
        self.assertEqual("harry", soul.who_replacement(player, harry, player))   # you kick harry
        self.assertEqual("harry", soul.who_replacement(player, harry, julie))    # fritz kicks harry
        self.assertEqual("harry", soul.who_replacement(player, harry, None))     # fritz kicks harry
        self.assertEqual("you", soul.who_replacement(julie, player, player))  # julie kicks you
        self.assertEqual("Fritz", soul.who_replacement(julie, player, harry))   # julie kicks fritz
        self.assertEqual("harry", soul.who_replacement(julie, harry, player))   # julie kicks harry
        self.assertEqual("you", soul.who_replacement(julie, harry, harry))    # julie kicks you
        self.assertEqual("harry", soul.who_replacement(julie, harry, None))     # julie kicks harry

    def testPoss(self):
        player = tale.player.Player("fritz", "m")
        julie = tale.base.Living("julie", "f", race="human")
        harry = tale.base.Living("harry", "m", race="human")
        soul = tale.base.Soul()
        self.assertEqual("your own", soul.poss_replacement(player, player, player))  # your own foot
        self.assertEqual("his own", soul.poss_replacement(player, player, julie))   # his own foot
        self.assertEqual("harry's", soul.poss_replacement(player, harry, player))   # harrys foot
        self.assertEqual("harry's", soul.poss_replacement(player, harry, julie))    # harrys foot
        self.assertEqual("harry's", soul.poss_replacement(player, harry, None))     # harrys foot
        self.assertEqual("your", soul.poss_replacement(julie, player, player))   # your foot
        self.assertEqual("Fritz's", soul.poss_replacement(julie, player, harry))    # fritz' foot
        self.assertEqual("harry's", soul.poss_replacement(julie, harry, player))    # harrys foot
        self.assertEqual("your", soul.poss_replacement(julie, harry, harry))     # your foot
        self.assertEqual("harry's", soul.poss_replacement(julie, harry, None))      # harrys foot

    def testGender(self):
        soul = tale.base.Soul()
        with self.assertRaises(KeyError):
            tale.player.Player("player", "x")
        player = tale.player.Player("julie", "f")
        parsed = tale.base.ParseResult("stomp")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("Julie stomps her foot.", room_msg)
        player = tale.player.Player("fritz", "m")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("Fritz stomps his foot.", room_msg)
        player = tale.player.Player("zyzzy", "n")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("Zyzzy stomps its foot.", room_msg)

    def testIgnorewords(self):
        soul = tale.base.Soul()
        player = tale.player.Player("fritz", "m")
        with self.assertRaises(tale.errors.ParseError):
            soul.parse(player, "in")
        with self.assertRaises(tale.errors.ParseError):
            soul.parse(player, "and")
        with self.assertRaises(tale.errors.ParseError):
            soul.parse(player, "fail")
        with self.assertRaises(tale.errors.ParseError):
            soul.parse(player, "fail in")
        with self.assertRaises(tale.errors.UnknownVerbException) as x:
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
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        philip = tale.base.Living("philip", "m")
        kate = tale.base.Living("kate", "f", title="Kate")
        cat = tale.base.Living("cat", "n", title="hairy cat")
        targets = [philip, kate, cat]
        # peer
        parsed = tale.base.ParseResult("peer", who_list=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual(set(targets), who)
        self.assertTrue(player_msg.startswith("You peer at "))
        self.assertTrue("philip" in player_msg and "hairy cat" in player_msg and "Kate" in player_msg)
        self.assertTrue(room_msg.startswith("Julie peers at "))
        self.assertTrue("philip" in room_msg and "hairy cat" in room_msg and "Kate" in room_msg)
        self.assertEqual("Julie peers at you.", target_msg)
        # all/everyone
        player.move(tale.base.Location("somewhere"))
        livings = set(targets)
        livings.add(player)
        player.location.livings = livings
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "smile confusedly at everyone")
        self.assertEqual("smile", verb)
        self.assertEqual(3, len(who))
        self.assertEqual(set(targets), set(who), "player should not be in targets")
        self.assertTrue("philip" in player_msg and "hairy cat" in player_msg and "Kate" in player_msg and "yourself" not in player_msg)
        self.assertTrue("philip" in room_msg and "hairy cat" in room_msg and "Kate" in room_msg and "herself" not in room_msg)
        self.assertEqual("Julie smiles confusedly at you.", target_msg)

    def testWhoInfo(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        kate = tale.base.Living("kate", "f", title="Kate")
        cat = tale.base.Living("cat", "n", title="hairy cat")
        player.move(tale.base.Location("somewhere"))
        cat.move(player.location)
        kate.move(player.location)
        parsed = soul.parse(player, "smile at cat and kate and myself")
        self.assertEqual(["cat", "kate", "myself"], parsed.args)
        self.assertEqual(3, parsed.who_count)
        self.assertEqual(3, parsed.who_count)
        self.assertTrue(cat in parsed.who_info and kate in parsed.who_info and player in parsed.who_info)
        self.assertEqual(0, parsed.who_info[cat].sequence)
        self.assertEqual(1, parsed.who_info[kate].sequence)
        self.assertEqual(2, parsed.who_info[player].sequence)
        self.assertEqual("at", parsed.who_info[cat].previous_word)
        self.assertEqual("and", parsed.who_info[kate].previous_word)
        self.assertEqual("and", parsed.who_info[player].previous_word)
        self.assertEqual([cat, kate, player], list(parsed.who_info))
        self.assertEqual(3, parsed.who_count)
        self.assertEqual((cat, kate, player), parsed.who_123)
        self.assertEqual(player, parsed.who_last)
        parsed = soul.parse(player, "smile at myself and kate and cat")
        self.assertEqual(["myself", "kate", "cat"], parsed.args)
        self.assertEqual([player, kate, cat], list(parsed.who_info))
        self.assertEqual(3, parsed.who_count)
        self.assertEqual((player, kate, cat), parsed.who_123)
        self.assertEqual(cat, parsed.who_last)
        parsed = soul.parse(player, "smile at kate cat myself")
        self.assertEqual("at", parsed.who_info[kate].previous_word, "ony kate has a previous word")
        self.assertEqual(None, parsed.who_info[cat].previous_word, "cat doesn't have a previous word")
        self.assertEqual(None, parsed.who_info[player].previous_word, "player doesn't have a previous word")
        # multiple references to the same entity are folded into one:
        parsed = soul.parse(player, "smile at kate, cat and cat")
        self.assertEqual(["kate", "cat", "cat"], parsed.args)
        self.assertEqual([kate, cat], list(parsed.who_info))
        self.assertEqual(2, parsed.who_count)
        self.assertEqual((kate, cat, None), parsed.who_123)

    def test_sanity(self):
        with self.assertRaises(AssertionError):
            tale.base.ParseResult("walk", who_info={})    # must be ordered dict instead
        tale.base.ParseResult("walk", who_info=collections.OrderedDict())  # must be ordered dict
        who_info = collections.OrderedDict()
        cat = tale.base.Living("cat", "f")
        dog = tale.base.Living("dog", "m")
        who_info[cat] = "info1"
        who_info[dog] = "info2"
        who_list = []
        tale.base.ParseResult("walk", who_info=who_info, who_list=who_list)
        who_list = [cat, dog]
        tale.base.ParseResult("walk", who_info=who_info, who_list=who_list)
        who_list = [cat, dog, cat]
        tale.base.ParseResult("walk", who_info=who_info, who_list=who_list)
        with self.assertRaises(tale.errors.ParseError):
            tale.base.ParseResult("walk", who_info=None, who_list=who_list)

    def test_who123(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        kate = tale.base.Living("kate", "f", title="Kate")
        cat = tale.base.Living("cat", "n", title="hairy cat")
        player.move(tale.base.Location("somewhere"))
        cat.move(player.location)
        kate.move(player.location)
        parsed = soul.parse(player, "smile at cat and kate and myself")
        self.assertEqual(cat, parsed.who_1)
        self.assertEqual((cat, kate), parsed.who_12)
        self.assertEqual((cat, kate, player), parsed.who_123)
        self.assertEqual(player, parsed.who_last)
        parsed = soul.parse(player, "smile at kate")
        self.assertEqual(kate, parsed.who_1)
        self.assertEqual((kate, None), parsed.who_12)
        self.assertEqual((kate, None, None), parsed.who_123)
        self.assertEqual(kate, parsed.who_last)
        parsed = soul.parse(player, "smile")
        self.assertIsNone(parsed.who_1)
        self.assertEqual((None, None), parsed.who_12)
        self.assertEqual((None, None, None), parsed.who_123)
        self.assertEqual(None, parsed.who_last)

    def testVerbTarget(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        player.title = "the great Julie, destroyer of worlds"
        player.move(tale.base.Location("somewhere"))
        npc_max = tale.base.Living("max", "m")
        player.location.livings = {npc_max, player}
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
        self.assertEqual([npc_max], list(parsed.who_info), "parse('all') must result in only the npc, not the player")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertTrue(len(who) == 1)
        self.assertIsInstance(who, (set, frozenset), "targets must be a set for O(1) lookups")
        self.assertEqual("max", list(who)[0].name)
        self.assertEqual("You grin evilly at max.", player_msg)
        parsed = soul.parse(player, "grin at all and me")
        self.assertEqual("grin", parsed.verb)
        self.assertEqual([npc_max, player], list(parsed.who_info), "parse('all and me') must include npc and the player")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual({npc_max}, who, "player should no longer be part of the remaining targets")
        self.assertTrue("yourself" in player_msg and "max" in player_msg)

    def testVerbTargetTypes(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        player.title = "the great Julie, destroyer of worlds"
        loc = tale.base.Location("somewhere")
        player.move(loc)
        npc_max = tale.base.Living("max", "m")
        loc.livings = {npc_max, player}
        rock = tale.base.Item("rock")
        loc.items = {rock}
        exit_east = tale.base.Exit(["east"], "somewhere", "east")
        loc.add_exits([exit_east])
        # target who type can be: Living, Item or Exit.
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "smile julie")
        self.assertEqual("smile", verb)
        self.assertEqual(set(), who, "player must not be part of the result targets")
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "smile max")
        self.assertEqual({npc_max}, who, "living max")
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "smile rock")
        self.assertEqual({rock}, who, "item rock")
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "smile east")
        self.assertEqual({exit_east}, who, "exit east")

    def testMessageQuote(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        # babble
        parsed = tale.base.ParseResult("babble")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You babble something incoherently.", player_msg)
        self.assertEqual("Julie babbles something incoherently.", room_msg)
        # babble with message
        parsed.message = "blurp"
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You babble 'blurp' incoherently.", player_msg)
        self.assertEqual("Julie babbles 'blurp' incoherently.", room_msg)

    def testMessageQuoteParse(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        player.move(tale.base.Location("somewhere"))
        player.location.livings = {tale.base.Living("max", "m"), player}
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
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        targets = [tale.base.Living("max", "m")]
        parsed = tale.base.ParseResult("beep", who_list=targets)
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
        with self.assertRaises(tale.errors.ParseError) as ex:
            soul.process_verb(player, "kick max side knee")
        self.assertEqual("You can't do that both in the side and on the knee.", str(ex.exception))

    def testQualifier(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        targets = [tale.base.Living("max", "m")]
        parsed = tale.base.ParseResult("tickle", qualifier="fail", who_list=targets)
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
        parsed = tale.base.ParseResult("scream", qualifier="don't", message="I have no idea")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You don't scream 'I have no idea' loudly.", player_msg)
        self.assertEqual("Julie doesn't scream 'I have no idea' loudly.", room_msg)
        self.assertEqual("Julie doesn't scream 'I have no idea' loudly.", target_msg)

    def testQualifierParse(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
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
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "fail sit")
        self.assertEqual("fail sit", verb)
        self.assertEqual("You try to sit down, but fail miserably.", player_msg)
        self.assertEqual("Julie tries to sit down, but fails miserably.", room_msg)

    def testAdverbs(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f", race="human")
        # check handling of more than one adverb
        with self.assertRaises(tale.errors.ParseError) as ex:
            soul.process_verb(player, "cough sickly and noisily")
        self.assertEqual("You can't do that both sickly and noisily.", str(ex.exception))
        # check handling of adverb prefix where there is 1 unique result
        verb, (who, player_msg, room_msg, target_msg) = soul.process_verb(player, "cough sic")
        self.assertEqual("You cough sickly.", player_msg)
        self.assertEqual("Julie coughs sickly.", room_msg)
        # check handling of adverb prefix where there are more results
        with self.assertRaises(tale.errors.ParseError) as ex:
            soul.process_verb(player, "cough si")
        self.assertEqual("What adverb did you mean: sickly, sideways, signally, significantly, or silently?", str(ex.exception))

    def testUnrecognisedWord(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f", race="human")
        with self.assertRaises(tale.errors.ParseError):
            soul.process_verb(player, "cough hubbabubba")

    def testCheckNameWithSpaces(self) -> None:
        blue_gem = tale.base.Item("BLUE GEM")
        dark_crystal = tale.base.Item("DARK RED CRYSTAL")
        brown_bird = tale.base.Living("BROWN BIRD", "n")
        exit_north = tale.base.Exit(["n"], "north", "exit north")
        exit_south = tale.base.Exit(["s"], "south", "exit south")
        livings = {"rat": tale.base.Living("RAT", "n"), "brown bird": brown_bird}
        items = {"paper": tale.base.Item("PAPER"), "blue gem": blue_gem, "dark red crystal": dark_crystal}
        exits = {"north bound somewhere": exit_north, "south bound somewhere": exit_south}
        soul = tale.base.Soul()
        result = soul.check_name_with_spaces(["give", "the", "blue", "gem", "to", "rat"], 0, livings, items, {})
        self.assertEqual((None, None, 0), result)
        result = soul.check_name_with_spaces(["give", "the", "blue", "gem", "to", "rat"], 1, livings, items, {})
        self.assertEqual((None, None, 0), result)
        result = soul.check_name_with_spaces(["give", "the", "blue", "gem", "to", "rat"], 4, livings, items, {})
        self.assertEqual((None, None, 0), result)
        result = soul.check_name_with_spaces(["give", "the", "blue", "gem", "to", "rat"], 2, livings, items, {})
        self.assertEqual((blue_gem, "blue gem", 2), result)
        result = soul.check_name_with_spaces(["give", "the", "dark", "red", "crystal", "to", "rat"], 2, livings, items, {})
        self.assertEqual((dark_crystal, "dark red crystal", 3), result)
        result = soul.check_name_with_spaces(["give", "the", "dark", "red", "paper", "to", "rat"], 2, livings, items, {})
        self.assertEqual((None, None, 0), result)
        result = soul.check_name_with_spaces(["give", "paper", "to", "brown", "bird"], 3, livings, items, {})
        self.assertEqual((brown_bird, "brown bird", 2), result)
        result = soul.check_name_with_spaces(["go", "south", "bound", "somewhere", "yes"], 1, livings, items, exits)
        self.assertEqual((exit_south, "south bound somewhere", 3), result)

    def testCheckNamesWithSpacesParsing(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        bird = tale.base.Living("brown bird", "f")
        room = tale.base.Location("somewhere")
        gate = tale.base.Exit("gate", room, "the gate")
        door1 = tale.base.Exit("door one", room, "door number one")
        door2 = tale.base.Exit("door two", room, "door number two")
        room.add_exits([gate, door1, door2])
        bird.move(room)
        player.move(room)
        with self.assertRaises(tale.errors.ParseError) as x:
            soul.parse(player, "hug bird")
        self.assertEqual("It's not clear what you mean by 'bird'.", str(x.exception))
        parsed = soul.parse(player, "hug brown bird affection")
        self.assertEqual("hug", parsed.verb)
        self.assertEqual("affectionately", parsed.adverb)
        self.assertEqual([bird], list(parsed.who_info))
        # check spaces in exit names
        parsed = soul.parse(player, "gate", external_verbs=frozenset(room.exits))
        self.assertEqual("gate", parsed.verb)
        parsed = soul.parse(player, "frobnizz gate", external_verbs={"frobnizz"})
        self.assertEqual("frobnizz", parsed.verb)
        self.assertEqual(["gate"], parsed.args)
        self.assertEqual([gate], list(parsed.who_info))
        with self.assertRaises(tale.errors.UnknownVerbException):
            soul.parse(player, "door")
        parsed = soul.parse(player, "enter door two", external_verbs={"enter"})
        self.assertEqual("enter", parsed.verb)
        self.assertEqual(["door two"], parsed.args)
        self.assertEqual([door2], list(parsed.who_info))
        with self.assertRaises(tale.errors.NonSoulVerb) as x:
            soul.parse(player, "door one")
        parsed = x.exception.parsed
        self.assertEqual("door one", parsed.verb)
        self.assertEqual([door1], list(parsed.who_info))
        with self.assertRaises(tale.errors.NonSoulVerb) as x:
            soul.parse(player, "door two")
        parsed = x.exception.parsed
        self.assertEqual("door two", parsed.verb)
        self.assertEqual([door2], list(parsed.who_info))

    def testEnterExits(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        room = tale.base.Location("somewhere")
        gate = tale.base.Exit("gate", room, "gate")
        east = tale.base.Exit("east", room, "east")
        door1 = tale.base.Exit("door one", room, "door number one")
        room.add_exits([gate, door1, east])
        player.move(room)
        # known actions: enter/go/climb/crawl
        with self.assertRaises(tale.errors.NonSoulVerb) as x:
            soul.parse(player, "enter door one")
        parsed = x.exception.parsed
        self.assertEqual("door one", parsed.verb)
        self.assertEqual([door1], list(parsed.who_info))
        with self.assertRaises(tale.errors.NonSoulVerb) as x:
            soul.parse(player, "climb gate")
        parsed = x.exception.parsed
        self.assertEqual("gate", parsed.verb)
        with self.assertRaises(tale.errors.NonSoulVerb) as x:
            soul.parse(player, "go east")
        parsed = x.exception.parsed
        self.assertEqual("east", parsed.verb)
        with self.assertRaises(tale.errors.NonSoulVerb) as x:
            soul.parse(player, "crawl east")
        parsed = x.exception.parsed
        self.assertEqual("east", parsed.verb)
        parsed = soul.parse(player, "jump west")
        self.assertEqual("jump", parsed.verb)
        self.assertEqual("westwards", parsed.adverb)

    def testParse(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f", race="human")
        room = tale.base.Location("somewhere")
        south_exit = tale.base.Exit("south", room, "a door to the south")
        east_exit = tale.base.Exit("east", room, "a door to the east")
        room.add_exits([east_exit, south_exit])
        player.move(room)
        max_npc = tale.base.Living("max", "m")
        kate_npc = tale.base.Living("kate", "f")
        dino_npc = tale.base.Living("dinosaur", "n")
        targets = [max_npc, kate_npc, dino_npc]
        targets_with_player = targets + [player]
        player.location.livings = targets
        newspaper = tale.base.Item("newspaper")
        player.location.insert(newspaper, player)
        parsed = soul.parse(player, "fail grin sickly at everyone head")
        self.assertEqual("fail", parsed.qualifier)
        self.assertEqual("grin", parsed.verb)
        self.assertEqual("sickly", parsed.adverb)
        self.assertEqual("head", parsed.bodypart)
        self.assertEqual("", parsed.message)
        self.assertTrue(parsed.who_count == 3)
        self.assertTrue(all(isinstance(x, tale.base.Living) for x in parsed.who_info), "parse must return Livings in 'who'")
        self.assertEqual(targets, list(parsed.who_info))
        self.assertEqual(tuple(targets), parsed.who_123)
        self.assertEqual(targets[-1], parsed.who_last)
        parsed = soul.parse(player, "slap myself")
        self.assertEqual(None, parsed.qualifier)
        self.assertEqual("slap", parsed.verb)
        self.assertEqual(None, parsed.adverb)
        self.assertEqual(None, parsed.bodypart)
        self.assertEqual("", parsed.message)
        self.assertEqual(1, parsed.who_count)
        self.assertEqual([player], list(parsed.who_info), "myself should be player")
        self.assertEqual(player, parsed.who_1)
        self.assertEqual(player, parsed.who_last)
        parsed = soul.parse(player, "slap all")
        self.assertEqual(None, parsed.qualifier)
        self.assertEqual("slap", parsed.verb)
        self.assertEqual(None, parsed.adverb)
        self.assertEqual(None, parsed.bodypart)
        self.assertEqual("", parsed.message)
        self.assertEqual(3, parsed.who_count, "all should not include player")
        self.assertEqual(targets, list(parsed.who_info), "all should not include player")
        self.assertEqual(tuple(targets), parsed.who_123)
        self.assertEqual(targets[-1], parsed.who_last)
        parsed = soul.parse(player, "slap all but kate")
        self.assertEqual(2, parsed.who_count, "all but kate should only be max and the dino")
        self.assertEqual([max_npc, dino_npc], list(parsed.who_info), "all but kate should only be max and the dino")
        self.assertEqual((max_npc, dino_npc, None), parsed.who_123)
        parsed = soul.parse(player, "slap all and myself")
        self.assertEqual(4, parsed.who_count)
        self.assertEqual(targets_with_player, list(parsed.who_info), "all and myself should include player")
        self.assertEqual(tuple(targets_with_player[:3]), parsed.who_123)
        self.assertEqual(targets_with_player[-1], parsed.who_last)
        parsed = soul.parse(player, "slap newspaper")
        self.assertEqual([newspaper], list(parsed.who_info), "must be able to perform soul verb on item")
        self.assertEqual(1, parsed.who_count)
        self.assertEqual(newspaper, parsed.who_1)
        self.assertEqual(newspaper, parsed.who_last)
        with self.assertRaises(tale.errors.ParseError) as x:
            soul.parse(player, "slap dino")
        self.assertEqual("Perhaps you meant dinosaur?", str(x.exception), "must suggest living with prefix")
        with self.assertRaises(tale.errors.ParseError) as x:
            soul.parse(player, "slap news")
        self.assertEqual("Perhaps you meant newspaper?", str(x.exception), "must suggest item with prefix")
        with self.assertRaises(tale.errors.ParseError) as x:
            soul.parse(player, "slap undefined")
        self.assertEqual("It's not clear what you mean by 'undefined'.", str(x.exception))
        parsed = soul.parse(player, "smile west")
        self.assertEqual("westwards", parsed.adverb)
        with self.assertRaises(tale.errors.ParseError) as x:
            soul.parse(player, "smile north")
        self.assertEqual("What adverb did you mean: northeastwards, northwards, or northwestwards?", str(x.exception))
        parsed = soul.parse(player, "smile south")
        self.assertEqual(["south"], parsed.args, "south must be parsed as a normal arg because it's an exit in the room")
        parsed = soul.parse(player, "smile kate dinosaur and max")
        self.assertEqual(["kate", "dinosaur", "max"], parsed.args, "must be able to skip comma")
        self.assertEqual(3, parsed.who_count, "must be able to skip comma")
        parsed = soul.parse(player, "reply kate ofcourse,  darling.")
        self.assertEqual(["kate", "ofcourse,", "darling."], parsed.args, "must be able to skip comma")
        self.assertEqual(1, parsed.who_count)

    def testParseMovement(self):
        # check movement parsing for room exits
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f", race="human")
        room = tale.base.Location("somewhere")
        south_exit = tale.base.Exit("south", room, "a door to the south")
        east_exit = tale.base.Exit("east", room, "a door to the east")
        room.add_exits([east_exit, south_exit])
        player.move(room)
        with self.assertRaises(tale.errors.NonSoulVerb) as x:
            soul.parse(player, "crawl south")
        self.assertEqual("south", x.exception.parsed.verb, "just the exit is the verb, not the movement action")
        self.assertEqual([south_exit], list(x.exception.parsed.who_info), "exit must be in the who set")
        self.assertEqual(south_exit, x.exception.parsed.who_1)
        self.assertEqual(1, x.exception.parsed.who_count)
        parsed_str = str(x.exception.parsed)
        self.assertTrue("verb=south" in parsed_str)
        with self.assertRaises(tale.errors.ParseError) as x:
            soul.parse(player, "crawl somewherenotexisting")
        self.assertEqual("You can't crawl there.", str(x.exception))
        with self.assertRaises(tale.errors.ParseError) as x:
            soul.parse(player, "crawl")
        self.assertEqual("Crawl where?", str(x.exception))
        room = tale.base.Location("somewhere")  # no exits in this new room
        player.move(room)
        with self.assertRaises(tale.errors.UnknownVerbException):
            soul.parse(player, "crawl")   # must raise unknownverb if there are no exits in the room

    def testUnparsed(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f", race="human")
        parsed = soul.parse(player, "fart")
        self.assertEqual("", parsed.unparsed)
        parsed = soul.parse(player, "grin sadistically")
        self.assertEqual("sadistically", parsed.unparsed)
        parsed = soul.parse(player, "fail sit zen")
        self.assertEqual("zen", parsed.unparsed)
        parsed = soul.parse(player, "pat myself comfortingly on the shoulder")
        self.assertEqual("myself comfortingly on the shoulder", parsed.unparsed)
        parsed = soul.parse(player, "take the watch and the key from the box", external_verbs={"take"})
        self.assertEqual("the watch and the key from the box", parsed.unparsed)
        parsed = soul.parse(player, "fail to _undefined_verb_ on the floor", external_verbs={"_undefined_verb_"})
        self.assertEqual("on the floor", parsed.unparsed)
        parsed = soul.parse(player, "say 'red or blue'", external_verbs={"say"})
        self.assertEqual("'red or blue'", parsed.unparsed)
        parsed = soul.parse(player, "say red or blue", external_verbs={"say"})
        self.assertEqual("red or blue", parsed.unparsed)
        parsed = soul.parse(player, "say hastily red or blue", external_verbs={"say"})
        self.assertEqual("hastily red or blue", parsed.unparsed)
        parsed = soul.parse(player, "fail say hastily red or blue on your head", external_verbs={"say"})
        self.assertEqual("hastily red or blue on your head", parsed.unparsed)

    def testDEFA(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        targets = [tale.base.Living("max", "m")]
        # grin
        parsed = tale.base.ParseResult("grin")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You grin evilly.", player_msg)
        self.assertEqual("Julie grins evilly.", room_msg)
        # drool
        parsed = tale.base.ParseResult("drool", who_list=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You drool on max.", player_msg)
        self.assertEqual("Julie drools on max.", room_msg)
        self.assertEqual("Julie drools on you.", target_msg)

    def testPREV(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        targets = [tale.base.Living("max", "m")]
        # peer
        parsed = tale.base.ParseResult("peer", who_list=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You peer at max.", player_msg)
        self.assertEqual("Julie peers at max.", room_msg)
        self.assertEqual("Julie peers at you.", target_msg)
        # tease
        parsed = tale.base.ParseResult("tease", who_list=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You tease max.", player_msg)
        self.assertEqual("Julie teases max.", room_msg)
        self.assertEqual("Julie teases you.", target_msg)
        # turn
        parsed = tale.base.ParseResult("turn", who_list=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You turn your head towards max.", player_msg)
        self.assertEqual("Julie turns her head towards max.", room_msg)
        self.assertEqual("Julie turns her head towards you.", target_msg)

    def testPHYS(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        targets = [tale.base.Living("max", "m")]
        # require person
        with self.assertRaises(tale.errors.ParseError):
            parsed = tale.base.ParseResult("bonk")
            soul.process_verb_parsed(player, parsed)
        # pounce
        parsed = tale.base.ParseResult("pounce", who_list=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You pounce max playfully.", player_msg)
        self.assertEqual("Julie pounces max playfully.", room_msg)
        self.assertEqual("Julie pounces you playfully.", target_msg)
        # hold
        parsed = tale.base.ParseResult("hold", who_list=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You hold max in your arms.", player_msg)
        self.assertEqual("Julie holds max in her arms.", room_msg)
        self.assertEqual("Julie holds you in her arms.", target_msg)

    def testSHRT(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        # faint
        parsed = tale.base.ParseResult("faint", adverb="slowly")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You faint slowly.", player_msg)
        self.assertEqual("Julie faints slowly.", room_msg)
        # cheer
        parsed = tale.base.ParseResult("cheer")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You cheer enthusiastically.", player_msg)
        self.assertEqual("Julie cheers enthusiastically.", room_msg)

    def testPERS(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        targets = [tale.base.Living("max", "m")]
        # fear1
        parsed = tale.base.ParseResult("fear")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You shiver with fear.", player_msg)
        self.assertEqual("Julie shivers with fear.", room_msg)
        # fear2
        parsed = tale.base.ParseResult("fear", who_list=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You fear max.", player_msg)
        self.assertEqual("Julie fears max.", room_msg)
        self.assertEqual("Julie fears you.", target_msg)

    def testSIMP(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        targets = [tale.base.Living("max", "m")]

        # scream 1
        parsed = tale.base.ParseResult("scream")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You scream loudly.", player_msg)
        self.assertEqual("Julie screams loudly.", room_msg)
        # scream 2
        parsed = tale.base.ParseResult("scream", who_list=targets)
        parsed.adverb = "angrily"
        parsed.message = "why"
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You scream 'why' angrily at max.", player_msg)
        self.assertEqual("Julie screams 'why' angrily at max.", room_msg)
        self.assertEqual("Julie screams 'why' angrily at you.", target_msg)
        # ask
        parsed = tale.base.ParseResult("ask", message="are you happy", who_list=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You ask max: are you happy?", player_msg)
        self.assertEqual("Julie asks max: are you happy?", room_msg)
        self.assertEqual("Julie asks you: are you happy?", target_msg)
        # puzzle1
        parsed = tale.base.ParseResult("puzzle")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You look puzzled.", player_msg)
        self.assertEqual("Julie looks puzzled.", room_msg)
        # puzzle2
        parsed = tale.base.ParseResult("puzzle", who_list=targets)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You look puzzled at max.", player_msg)
        self.assertEqual("Julie looks puzzled at max.", room_msg)
        self.assertEqual("Julie looks puzzled at you.", target_msg)
        # chant1
        parsed = tale.base.ParseResult("chant", adverb="merrily", message="tralala")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You merrily chant: tralala.", player_msg)
        self.assertEqual("Julie merrily chants: tralala.", room_msg)
        # chant2
        parsed = tale.base.ParseResult("chant")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You chant: Hare Krishna Krishna Hare Hare.", player_msg)
        self.assertEqual("Julie chants: Hare Krishna Krishna Hare Hare.", room_msg)

    def testDEUX(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        # die
        parsed = tale.base.ParseResult("die", adverb="suddenly")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You suddenly fall down and play dead.", player_msg)
        self.assertEqual("Julie suddenly falls to the ground, dead.", room_msg)
        # ah
        parsed = tale.base.ParseResult("ah", adverb="rudely")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You go 'ah' rudely.", player_msg)
        self.assertEqual("Julie goes 'ah' rudely.", room_msg)
        # verb needs a person
        with self.assertRaises(tale.errors.ParseError) as x:
            soul.process_verb(player, "touch")
        self.assertEqual("The verb touch needs a person.", str(x.exception))

    def testQUAD(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f")
        targets = [tale.base.Living("max", "m")]
        # watch1
        parsed = tale.base.ParseResult("watch")
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertEqual("You watch the surroundings carefully.", player_msg)
        self.assertEqual("Julie watches the surroundings carefully.", room_msg)
        # watch2
        parsed = tale.base.ParseResult("watch", who_list=targets)
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
        targets2 = [tale.base.Living("max", "m"), player]
        parsed = tale.base.ParseResult("ayt", who_list=targets2)
        who, player_msg, room_msg, target_msg = soul.process_verb_parsed(player, parsed)
        self.assertTrue(player_msg.startswith("You wave your hand in front of "))
        self.assertTrue("max's" in player_msg and "your own" in player_msg)
        self.assertTrue(room_msg.startswith("Julie waves her hand in front of "))
        self.assertTrue("max's" in room_msg and "her own" in room_msg)
        self.assertEqual("Julie waves her hand in front of your face, are you there?", target_msg)

    def testFULL(self):
        pass  # FULL is not yet used

    def testPronounReferences(self):
        soul = tale.base.Soul()
        player = tale.player.Player("julie", "f", race="human")
        room = tale.base.Location("somewhere")
        room2 = tale.base.Location("somewhere else")
        player.move(room)
        max_npc = tale.base.Living("Max", "m")
        kate_npc = tale.base.Living("Kate", "f")
        dino_npc = tale.base.Living("dinosaur", "n")
        targets = [max_npc, kate_npc, dino_npc]
        player.location.livings = targets
        newspaper = tale.base.Item("newspaper")
        player.location.insert(newspaper, player)
        # her
        parsed = soul.parse(player, "hug kate")
        soul.remember_previous_parse(parsed)
        parsed = soul.parse(player, "kiss her")
        self.assertEqual(["(By 'her', we assume you meant Kate.)\n"], player.test_get_output_paragraphs())
        self.assertEqual(kate_npc, parsed.who_1)
        # it
        parsed = soul.parse(player, "hug dinosaur")
        soul.remember_previous_parse(parsed)
        parsed = soul.parse(player, "kiss it")
        self.assertEqual(["(By 'it', we assume you meant dinosaur.)\n"], player.test_get_output_paragraphs())
        self.assertEqual(dino_npc, parsed.who_1)
        with self.assertRaises(tale.errors.ParseError) as x:
            parsed = soul.parse(player, "kiss her")
        self.assertEqual("It is not clear who or what you're referring to.", str(x.exception))
        # them
        parsed = soul.parse(player, "hug kate and dinosaur")
        soul.remember_previous_parse(parsed)
        parsed = soul.parse(player, "kiss them")
        self.assertEqual(["(By 'them', we assume you meant Kate and dinosaur.)\n"], player.test_get_output_paragraphs())
        self.assertEqual([kate_npc, dino_npc], list(parsed.who_info))
        # when no longer around
        parsed = soul.parse(player, "hug kate")
        soul.remember_previous_parse(parsed)
        player.move(room2)
        with self.assertRaises(tale.errors.ParseError) as x:
            parsed = soul.parse(player, "kiss her")
        self.assertEqual("She is no longer around.", str(x.exception))

    def test_adjust_verbs(self):
        allowed = ["hug", "ponder", "sit", "kick", "cough", "greet", "poke", "yawn"]
        remove = ["hug", "kick"]
        verbs = {"frobnizificate": (tale.verbdefs.SIMP, None, "frobnizes \nHOW \nAT", "at")}
        # keep original values to put back after tests
        ORIG_VERBS = tale.verbdefs.VERBS.copy()
        ORIG_AGGRESSIVE_VERBS = tale.verbdefs.AGGRESSIVE_VERBS.copy()
        ORIG_NONLIVING_OK_VERBS = tale.verbdefs.NONLIVING_OK_VERBS.copy()
        ORIG_MOVEMENT_VERBS = tale.verbdefs.MOVEMENT_VERBS.copy()
        try:
            tale.verbdefs.adjust_available_verbs(allowed_verbs=allowed, remove_verbs=remove, add_verbs=verbs)
            self.assertEqual({"poke"}, tale.verbdefs.AGGRESSIVE_VERBS)
            self.assertEqual({"yawn"}, tale.verbdefs.NONLIVING_OK_VERBS)
            self.assertEqual(set(), tale.verbdefs.MOVEMENT_VERBS)
            remaining = sorted(tale.verbdefs.VERBS.keys())
            self.assertEqual(["cough", "frobnizificate", "greet", "poke", "ponder", "sit", "yawn"], remaining)
        finally:
            # restore original values
            tale.verbdefs.VERBS = ORIG_VERBS
            tale.verbdefs.AGGRESSIVE_VERBS = ORIG_AGGRESSIVE_VERBS
            tale.verbdefs.NONLIVING_OK_VERBS = ORIG_NONLIVING_OK_VERBS
            tale.verbdefs.MOVEMENT_VERBS = ORIG_MOVEMENT_VERBS


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
