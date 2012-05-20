"""
Unittests for Mud base objects

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import unittest
import tale.globals
from supportstuff import DummyDriver, MsgTraceNPC

tale.globals.mud_context.driver = DummyDriver()

from tale.base import Location, Exit, Item
from tale.errors import SecurityViolation, ParseError
from tale.npc import NPC
from tale.player import Player
from tale.soul import NonSoulVerb, ParseResults


class TestPlayer(unittest.TestCase):
    def test_init(self):
        player = Player("fritz", "m")
        player.set_title("%s the great", includes_name_param=True)
        self.assertEqual("fritz", player.name)
        self.assertEqual("Fritz the great", player.title)
        self.assertEqual("", player.description)
        self.assertEqual("human", player.race)
        self.assertEqual("m", player.gender)
        self.assertEqual(set(), player.privileges)
        self.assertTrue(1 < player.stats["agi"] < 100)
    def test_tell(self):
        player = Player("fritz", "m")
        player.tell(None)
        self.assertEqual(["None"], player.get_output_lines())
        player.tell("")
        self.assertEqual([], player.get_output_lines())
        player.tell("")
        player.tell("")
        self.assertEqual([], player.get_output_lines())
        player.tell("")
        player.tell("line1")
        player.tell("")
        player.tell("line2")
        player.tell("")
        self.assertEqual(["line1", "line2"], player.get_output_lines())
        player.tell("", format=False)
        player.tell("line1", format=False)
        player.tell("", format=False)
        player.tell("line2", format=False)
        player.tell("", format=False)
        self.assertEqual(["\n", "\aline1", "\n", "\n", "\aline2", "\n"], player.get_output_lines())
        player.tell("\n")
        self.assertEqual(["\n"], player.get_output_lines())
        player.tell("line1")
        player.tell("line2")
        player.tell("hello\nnewline")
        player.tell("\n")
        player.tell("ints", 42, 999)
        self.assertEqual(["line1", "line2", "hello\nnewline", "\n", "ints 42 999"], player.get_output_lines())
        self.assertEqual([], player.get_output_lines())
        player.tell("para1", end=False)
        player.tell("para2", end=True)
        player.tell("para3")
        player.tell("\n")
        player.tell("para4", "\n", "para5")
        self.assertEqual(["para1", "para2", "\n", "para3", "\n", "para4  para5"], player.get_output_lines())
        player.tell("   xyz   \n  123", format=False)
        self.assertEqual(["\n", "\a   xyz   \n  123", "\n"], player.get_output_lines())
        player.tell("line1", end=True)
        player.tell("\n")
        player.tell("line2", end=True)
        player.tell("\n")
        player.tell("\n")
        self.assertEqual(["line1", "\n", "\n", "line2", "\n", "\n", "\n"], player.get_output_lines())

    def test_tell_emptystring(self):
        player = Player("fritz", "m")
        player.tell("", end=False)
        self.assertEqual([], player.get_output_lines())
        player.tell("", end=True)
        self.assertEqual(["\n"], player.get_output_lines())
        player.tell("", end=True)
        player.tell("", end=True)
        self.assertEqual(["\n", "\n"], player.get_output_lines())

    def test_tell_formats(self):
        player = Player("fritz", "m")
        player.tell("a b c", format=True)
        player.tell("d e f", format=True)
        self.assertEqual(["a b c", "d e f"], player.get_output_lines())
        player.tell("a b c", format=True)
        player.tell("d e f", format=True)
        self.assertEqual("  a b c d e f", player.get_wrapped_output_lines())
        player.tell("a b c", format=False)
        player.tell("d e f", format=False)
        self.assertEqual(["\n", "\aa b c", "\n", "\n", "\ad e f", "\n"], player.get_output_lines())
        player.tell("a b c", format=False)
        player.tell("d e f", format=False)
        self.assertEqual("\n  a b c\n\n  d e f", player.get_wrapped_output_lines())
        player.tell("a b c", format=True)
        player.tell("d e f", format=False)
        self.assertEqual(["a b c", "\n", "\ad e f", "\n"], player.get_output_lines())
        player.tell("a b c", format=True)
        player.tell("d e f", format=False)
        self.assertEqual("  a b c\n  d e f", player.get_wrapped_output_lines())

    def test_tell_wrapped(self):
        player = Player("fritz", "m")
        player.set_screen_sizes(0, 80)
        player.tell("line1")
        player.tell("line2", "\n")
        player.tell("hello\nnewline")
        player.tell("\n")  # paragraph separator
        player.tell("ints", 42, 999)
        self.assertEqual("line1 line2 hello newline\nints 42 999", player.get_wrapped_output_lines())
        player.tell("para1", end=False)
        player.tell("para2", end=True)
        player.tell("para3")
        player.tell("\n")
        player.tell("para4", "\n", "para5")
        self.assertEqual("para1 para2\npara3\npara4  para5", player.get_wrapped_output_lines())
        player.tell("word " * 30)
        self.assertNotEqual(("word " * 30).strip(), player.get_wrapped_output_lines())
        player.tell("word " * 30, format=False)
        self.assertEqual("\n"+("word " * 30).strip(), player.get_wrapped_output_lines(), "when format=False output should be unformatted")
        player.tell("   xyz   \n  123", format=False)
        self.assertEqual("\n   xyz   \n  123", player.get_wrapped_output_lines())
        player.tell("line1", end=True)
        player.tell("\n")
        player.tell("line2", end=True)
        player.tell("\n")
        player.tell("\n")
        self.assertEqual("line1\n\nline2", player.get_wrapped_output_lines())

    def test_look(self):
        player = Player("fritz", "m")
        attic = Location("Attic", "A dark attic.")
        player.look()
        self.assertEqual(["[Limbo]", "\n", "The intermediate or transitional place or state. There's only nothingness.\nLivings end up here if they're not inside a proper location yet.", "\n"], player.get_output_lines())
        player.move(attic, silent=True)
        player.look(short=True)
        self.assertEqual(["[Attic]", "\n"], player.get_output_lines())
        julie = NPC("julie", "f")
        julie.move(attic, silent=True)
        player.look(short=True)
        self.assertEqual(["[Attic]", "\n", "Present: julie", "\n"], player.get_output_lines())

    def test_look_brief(self):
        player = Player("fritz", "m")
        attic = Location("Attic", "A dark attic.")
        cellar = Location("Cellar", "A gloomy cellar.")
        julie = NPC("julie", "f")
        julie.move(attic, silent=True)
        player.move(attic, silent=True)
        player.brief = 0  # default setting: always long descriptions
        player.look()
        self.assertEqual(["[Attic]", "\n", "A dark attic.", "\n", "Julie is here.", "\n"], player.get_output_lines())
        player.look()
        self.assertEqual(["[Attic]", "\n", "A dark attic.", "\n", "Julie is here.", "\n"], player.get_output_lines())
        player.look(short=True)   # override
        self.assertEqual(["[Attic]", "\n", "Present: julie", "\n"], player.get_output_lines())
        player.brief = 1  # short for known, long for new locations
        player.look()
        self.assertEqual(["[Attic]", "\n", "Present: julie", "\n"], player.get_output_lines())
        player.move(cellar, silent=True)
        player.look()
        self.assertEqual(["[Cellar]", "\n", "A gloomy cellar.", "\n"], player.get_output_lines())
        player.look()
        self.assertEqual(["[Cellar]", "\n"], player.get_output_lines())
        player.brief = 2  # short always
        player.known_locations.clear()
        player.look()
        self.assertEqual(["[Cellar]", "\n"], player.get_output_lines())
        player.move(attic, silent=True)
        player.look()
        self.assertEqual(["[Attic]", "\n", "Present: julie", "\n"], player.get_output_lines())
        player.look(short=True)   # override
        self.assertEqual(["[Attic]", "\n", "Present: julie", "\n"], player.get_output_lines())
        player.look(short=False)  # override
        self.assertEqual(["[Attic]", "\n", "A dark attic.", "\n", "Julie is here.", "\n"], player.get_output_lines())

    def test_others(self):
        attic = Location("Attic", "A dark attic.")
        player = Player("merlin", "m")
        player.set_title("wizard merlin")
        julie = MsgTraceNPC("julie", "f", "human")
        fritz = MsgTraceNPC("fritz", "m", "human")
        julie.move(attic, silent=True)
        fritz.move(attic, silent=True)
        player.move(attic, silent=True)
        player.tell_others("one", "two", "three")
        self.assertEqual([], player.get_output_lines())
        self.assertEqual(["one", "two", "three"], fritz.messages)
        self.assertEqual(["one", "two", "three"], julie.messages)
        fritz.clearmessages()
        julie.clearmessages()
        player.tell_others("{title} and {Title}")
        self.assertEqual(["wizard merlin and Wizard merlin"], fritz.messages)

    def test_wiretap(self):
        attic = Location("Attic", "A dark attic.")
        player = Player("fritz", "m")
        julie = NPC("julie", "f")
        julie.move(attic)
        player.move(attic)
        julie.tell("message for julie")
        attic.tell("message for room")
        self.assertEqual(["message for room"], player.get_output_lines())
        with self.assertRaises(SecurityViolation):
            player.create_wiretap(julie)
        player.privileges = {"wizard"}
        player.create_wiretap(julie)
        player.create_wiretap(attic)
        julie.tell("message for julie")
        attic.tell("message for room")
        self.assertEqual(["\n", "\n", "\n", "[wiretap on 'Attic': message for room]", "[wiretap on 'julie': message for julie]",
            "[wiretap on 'julie': message for room]", "message for room"], sorted(player.get_output_lines()))
        # test removing the wiretaps
        player.installed_wiretaps.clear()
        import gc
        gc.collect()
        julie.tell("message for julie")
        attic.tell("message for room")
        self.assertEqual(["message for room"], player.get_output_lines())

    def test_socialize(self):
        player = Player("fritz", "m")
        attic = Location("Attic", "A dark attic.")
        julie = NPC("julie", "f")
        julie.move(attic)
        player.move(attic)
        parsed = player.parse("wave all")
        self.assertEqual("wave", parsed.verb)
        self.assertEqual([julie], parsed.who_order)
        who, playermsg, roommsg, targetmsg = player.socialize_parsed(parsed)
        self.assertEqual({julie}, who)
        self.assertEqual("You wave happily at julie.", playermsg)
        with self.assertRaises(tale.soul.UnknownVerbException):
            player.parse("befrotzificate all and me")
        with self.assertRaises(NonSoulVerb) as x:
            player.parse("befrotzificate all and me", external_verbs={"befrotzificate"})
        parsed = x.exception.parsed
        self.assertEqual("befrotzificate", parsed.verb)
        self.assertEqual([julie, player], parsed.who_order)
        attic.exits["south"] = Exit("target", "door")
        try:
            player.parse("push south")
            self.fail("push south should throw a parse error because of the exit that is used")
        except ParseError:
            pass
        with self.assertRaises(NonSoulVerb):
            player.parse("fart south")
        parsed = player.parse("hug julie")
        player.validate_socialize_targets(parsed)

    def test_verbs(self):
        player = Player("julie", "f")
        player.verbs.append("smurf")
        player.verbs.append("smurf")
        self.assertTrue("smurf" in player.verbs)
        self.assertEqual(2, player.verbs.count("smurf"))

    def test_story_complete(self):
        player = Player("fritz", "m")
        self.assertFalse(player.story_complete)
        self.assertIsNone(player.story_complete_callback)
        player.story_completed()
        self.assertTrue(player.story_complete)
        self.assertIsNone(player.story_complete_callback)
        player.story_completed("huzzah")
        self.assertTrue(player.story_complete)
        self.assertEqual("huzzah", player.story_complete_callback)

    def test_handle_and_notify_action(self):
        class SpecialPlayer(Player):
            def init(self):
                self.handled = False
                self.handle_verb_called = False
                self.notify_called = False
            def handle_verb(self, parsed, actor):
                self.handle_verb_called = True
                if parsed.verb in self.verbs:
                    self.handled = True
                    return True
                else:
                    return False
            def notify_action(self, parsed, actor):
                self.notify_called = True
        player = SpecialPlayer("julie", "f")
        player.verbs = ["xywobble"]
        room = Location("room")
        class Chair(Item):
            def init(self):
                self.handled = False
                self.handle_verb_called = False
                self.notify_called = False
            def handle_verb(self, parsed, actor):
                self.handle_verb_called = True
                if parsed.verb in self.verbs:
                    self.handled = True
                    return True
                else:
                    return False
            def notify_action(self, parsed, actor):
                self.notify_called = True
        chair_in_inventory = Chair("littlechair")
        chair_in_inventory.verbs = ["kerwaffle"]
        player.insert(chair_in_inventory, player)
        chair = Chair("chair")
        chair.verbs = ["frobnitz"]
        room.init_inventory([player, chair])

        # first check if the handle_verb passes to all objects including inventory
        parsed = ParseResults("kowabungaa12345")
        handled = room.handle_verb(parsed, player)
        self.assertFalse(handled)
        self.assertTrue(chair.handle_verb_called)
        self.assertTrue(player.handle_verb_called)
        self.assertTrue(chair_in_inventory.handle_verb_called)
        self.assertFalse(chair.handled)
        self.assertFalse(player.handled)
        self.assertFalse(chair_in_inventory.handled)

        # check item handling
        player.init()
        chair.init()
        chair_in_inventory.init()
        parsed = ParseResults("frobnitz")
        handled = room.handle_verb(parsed, player)
        self.assertTrue(handled)
        self.assertTrue(chair.handled)
        self.assertFalse(player.handled)
        self.assertFalse(chair_in_inventory.handled)

        # check living handling
        player.init()
        chair.init()
        chair_in_inventory.init()
        parsed = ParseResults("xywobble")
        handled = room.handle_verb(parsed, player)
        self.assertTrue(handled)
        self.assertFalse(chair.handled)
        self.assertTrue(player.handled)
        self.assertFalse(chair_in_inventory.handled)

        # check inventory handling
        player.init()
        chair.init()
        chair_in_inventory.init()
        parsed = ParseResults("kerwaffle")
        handled = room.handle_verb(parsed, player)
        self.assertTrue(handled)
        self.assertFalse(chair.handled)
        self.assertFalse(player.handled)
        self.assertTrue(chair_in_inventory.handled)

        # check notify_action
        player.init()
        chair.init()
        chair_in_inventory.init()
        room.notify_action(parsed, player)
        self.assertTrue(chair.notify_called)
        self.assertTrue(player.notify_called)
        self.assertTrue(chair_in_inventory.notify_called)


if __name__ == '__main__':
    unittest.main()
