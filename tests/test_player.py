"""
Unittests for Mud base objects

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division, unicode_literals
import sys
import unittest
import tale.globalcontext
from supportstuff import DummyDriver, MsgTraceNPC
from tale.base import Location, Exit, Item
from tale.errors import SecurityViolation, ParseError
from tale.npc import NPC
from tale.player import Player, TextBuffer
from tale.soul import NonSoulVerb, ParseResult
from tale.io.console_io import ConsoleIo
from tale.charbuilder import CharacterBuilder
from tale.util import AttrDict
if sys.version_info < (3, 0):
    from StringIO import StringIO
else:
    from io import StringIO


class TestPlayer(unittest.TestCase):
    def setUp(self):
        tale.globalcontext.mud_context.driver = DummyDriver()
        tale.globalcontext.mud_context.config = AttrDict()
        tale.globalcontext.mud_context.config.server_mode="if"
    def test_init(self):
        player = Player("fritz", "m")
        player.title = "Fritz the great"
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
        self.assertEqual(["None\n"], player.get_output_paragraphs_raw())
        player.tell("")
        self.assertEqual([], player.get_output_paragraphs_raw())
        player.tell("")
        player.tell("")
        self.assertEqual([], player.get_output_paragraphs_raw())
        player.tell("")
        player.tell("line1")
        player.tell("line2")
        player.tell("")
        self.assertEqual(["line1\nline2\n"], player.get_output_paragraphs_raw())
        player.tell("", format=False)
        player.tell("line1", format=False)
        player.tell("", format=False)
        player.tell("line2", format=False)
        player.tell("", format=False)
        self.assertEqual(["\nline1\n\nline2\n\n"], player.get_output_paragraphs_raw())
        player.tell("\n")
        self.assertEqual(["\n"], player.get_output_paragraphs_raw())
        player.tell("line1")
        player.tell("line2")
        player.tell("hello\nnewline")
        player.tell("\n")
        player.tell("ints", 42, 999)
        self.assertEqual(["line1\nline2\nhello\nnewline\n", "ints\n42\n999\n"], player.get_output_paragraphs_raw())
        self.assertEqual([], player.get_output_paragraphs_raw())
        player.tell("para1", end=False)
        player.tell("para2", end=True)
        player.tell("para3")
        player.tell("\n")
        player.tell("para4", "\n", "para5")
        self.assertEqual(["para1\npara2\n", "para3\n", "para4\n\npara5\n"], player.get_output_paragraphs_raw())
        player.tell("   xyz   \n  123", format=False)
        self.assertEqual(["   xyz   \n  123\n"], player.get_output_paragraphs_raw())
        player.tell("line1", end=True)
        player.tell("\n")
        player.tell("line2", end=True)
        player.tell("\n")
        player.tell("\n")
        self.assertEqual(["line1\n", "\n", "line2\n", "\n", "\n"], player.get_output_paragraphs_raw())

    def test_tell_chain(self):
        player = Player("fritz", "m")
        player.tell("hi").tell("there")
        self.assertEqual(["hi\nthere\n"], player.get_output_paragraphs_raw())

    def test_tell_emptystring(self):
        player = Player("fritz", "m")
        player.tell("", end=False)
        self.assertEqual([], player.get_output_paragraphs_raw())
        player.tell("", end=True)
        self.assertEqual(["\n"], player.get_output_paragraphs_raw())
        player.tell("", end=True)
        player.tell("", end=True)
        self.assertEqual(["\n", "\n"], player.get_output_paragraphs_raw())

    def test_tell_formats(self):
        player = Player("fritz", "m")
        player.io = ConsoleIo(None)
        player.set_screen_sizes(0, 100)
        player.tell("a b c", format=True)
        player.tell("d e f", format=True)
        self.assertEqual(["a b c\nd e f\n"], player.get_output_paragraphs_raw())
        player.tell("a b c", format=True)
        player.tell("d e f", format=True)
        self.assertEqual("a b c d e f\n", player.get_output())
        player.tell("a b c", format=False)
        player.tell("d e f", format=False)
        self.assertEqual(["a b c\nd e f\n"], player.get_output_paragraphs_raw())
        player.tell("a b c", format=False)
        player.tell("d e f", format=False)
        self.assertEqual("a b c\nd e f\n", player.get_output())
        player.tell("a b c", format=True)
        player.tell("d e f", format=False)
        self.assertEqual(["a b c\n", "d e f\n"], player.get_output_paragraphs_raw())
        player.tell("a b c", format=True)
        player.tell("d e f", format=False)
        self.assertEqual("a b c\nd e f\n", player.get_output())

    def test_tell_formatted(self):
        player = Player("fritz", "m")
        player.io = ConsoleIo(None)
        player.set_screen_sizes(0, 100)
        player.tell("line1")
        player.tell("line2", "\n")
        player.tell("hello\nnewline")
        player.tell("\n")  # paragraph separator
        player.tell("ints", 42, 999)
        self.assertEqual("line1 line2  hello newline\nints 42 999\n", player.get_output())
        player.tell("para1", end=False)
        player.tell("para2", end=True)
        player.tell("para3")
        player.tell("\n")
        player.tell("para4", "\n", "para5")
        self.assertEqual("para1 para2\npara3\npara4  para5\n", player.get_output())
        player.tell("word " * 30)
        self.assertNotEqual(("word " * 30).strip(), player.get_output())
        player.tell("word " * 30, format=False)
        self.assertEqual(("word " * 30) + "\n", player.get_output())  # when format=False output should be unformatted
        player.tell("   xyz   \n  123", format=False)
        self.assertEqual("   xyz   \n  123\n", player.get_output())
        player.tell("line1", end=True)
        player.tell("\n")
        player.tell("line2", end=True)
        player.tell("\n")
        player.tell("\n")
        self.assertEqual(["line1\n", "\n", "line2\n", "\n", "\n"], player.get_output_paragraphs_raw())
        player.tell("line1", end=True)
        player.tell("\n")
        player.tell("line2", end=True)
        player.tell("\n")
        player.tell("\n")
        self.assertEqual("line1\n\nline2\n\n\n", player.get_output())

    def test_peek_output(self):
        player = Player("fritz", "m")
        player.io = ConsoleIo(None)
        player.set_screen_sizes(0, 100)
        player.tell("line1")
        player.tell("line2", 42)
        self.assertEqual(["line1\nline2\n42\n"], player.peek_output_paragraphs_raw())
        self.assertEqual("line1 line2 42\n", player.get_output())
        self.assertEqual([], player.peek_output_paragraphs_raw())

    def test_look(self):
        player = Player("fritz", "m")
        attic = Location("Attic", "A dark attic.")
        player.look()
        self.assertEqual(["[Limbo]\n", "The intermediate or transitional place or state. There's only nothingness.\nLiving beings end up here if they're not in a proper location yet.\n"], player.get_output_paragraphs_raw())
        player.move(attic, silent=True)
        player.look(short=True)
        self.assertEqual(["[Attic]\n"], player.get_output_paragraphs_raw())
        julie = NPC("julie", "f")
        julie.move(attic, silent=True)
        player.look(short=True)
        self.assertEqual(["[Attic]\n", "Present: julie\n"], player.get_output_paragraphs_raw())

    def test_look_brief(self):
        player = Player("fritz", "m")
        attic = Location("Attic", "A dark attic.")
        cellar = Location("Cellar", "A gloomy cellar.")
        julie = NPC("julie", "f")
        julie.move(attic, silent=True)
        player.move(attic, silent=True)
        player.brief = 0  # default setting: always long descriptions
        player.look()
        self.assertEqual(["[Attic]\n", "A dark attic.\n", "Julie is here.\n"], player.get_output_paragraphs_raw())
        player.look()
        self.assertEqual(["[Attic]\n", "A dark attic.\n", "Julie is here.\n"], player.get_output_paragraphs_raw())
        player.look(short=True)   # override
        self.assertEqual(["[Attic]\n", "Present: julie\n"], player.get_output_paragraphs_raw())
        player.brief = 1  # short for known, long for new locations
        player.look()
        self.assertEqual(["[Attic]\n", "Present: julie\n"], player.get_output_paragraphs_raw())
        player.move(cellar, silent=True)
        player.look()
        self.assertEqual(["[Cellar]\n", "A gloomy cellar.\n"], player.get_output_paragraphs_raw())
        player.look()
        self.assertEqual(["[Cellar]\n"], player.get_output_paragraphs_raw())
        player.brief = 2  # short always
        player.known_locations.clear()
        player.look()
        self.assertEqual(["[Cellar]\n"], player.get_output_paragraphs_raw())
        player.move(attic, silent=True)
        player.look()
        self.assertEqual(["[Attic]\n", "Present: julie\n"], player.get_output_paragraphs_raw())
        player.look(short=True)   # override
        self.assertEqual(["[Attic]\n", "Present: julie\n"], player.get_output_paragraphs_raw())
        player.look(short=False)  # override
        self.assertEqual(["[Attic]\n", "A dark attic.\n", "Julie is here.\n"], player.get_output_paragraphs_raw())

    def test_others(self):
        attic = Location("Attic", "A dark attic.")
        player = Player("merlin", "m")
        player.title = "wizard Merlin"
        julie = MsgTraceNPC("julie", "f", "human")
        fritz = MsgTraceNPC("fritz", "m", "human")
        julie.move(attic, silent=True)
        fritz.move(attic, silent=True)
        player.move(attic, silent=True)
        player.tell_others("one", "two", "three")
        self.assertEqual([], player.get_output_paragraphs_raw())
        self.assertEqual(["one", "two", "three"], fritz.messages)
        self.assertEqual(["one", "two", "three"], julie.messages)
        fritz.clearmessages()
        julie.clearmessages()
        player.tell_others("{title} and {Title}")
        self.assertEqual(["wizard Merlin and Wizard Merlin"], fritz.messages)

    def test_wiretap(self):
        attic = Location("Attic", "A dark attic.")
        player = Player("fritz", "m")
        player.io = ConsoleIo(None)
        player.io.supports_smartquotes = False
        player.set_screen_sizes(0, 100)
        julie = NPC("julie", "f")
        julie.move(attic)
        player.move(attic)
        julie.tell("message for julie")
        attic.tell("message for room")
        self.assertEqual(["message for room\n"], player.get_output_paragraphs_raw())
        with self.assertRaises(SecurityViolation):
            player.create_wiretap(julie)
        player.privileges = {"wizard"}
        player.create_wiretap(julie)
        player.create_wiretap(attic)
        julie.tell("message for julie")
        attic.tell("message for room")
        output = player.get_output()
        self.assertTrue("[wiretapped from 'Attic': message for room]" in output)
        self.assertTrue("[wiretapped from 'julie': message for julie]" in output)
        self.assertTrue("[wiretapped from 'julie': message for room]" in output)
        self.assertTrue("message for room " in output)
        # test removing the wiretaps
        player.clear_wiretaps()
        import gc
        gc.collect()
        julie.tell("message for julie")
        attic.tell("message for room")
        self.assertEqual(["message for room\n"], player.get_output_paragraphs_raw())

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
        attic.add_exits([Exit("south", "target", "door")])
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
        player.verbs["smurf"] = ""
        self.assertTrue("smurf" in player.verbs)
        del player.verbs["smurf"]
        self.assertFalse("smurf" in player.verbs)

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
        player.verbs["xywobble"] = ""
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
        chair_in_inventory.verbs["kerwaffle"] = ""
        player.insert(chair_in_inventory, player)
        chair = Chair("chair")
        chair.verbs["frobnitz"] = ""
        room.init_inventory([player, chair])

        # first check if the handle_verb passes to all objects including inventory
        parsed = ParseResult("kowabungaa12345")
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
        parsed = ParseResult("frobnitz")
        handled = room.handle_verb(parsed, player)
        self.assertTrue(handled)
        self.assertTrue(chair.handled)
        self.assertFalse(player.handled)
        self.assertFalse(chair_in_inventory.handled)

        # check living handling
        player.init()
        chair.init()
        chair_in_inventory.init()
        parsed = ParseResult("xywobble")
        handled = room.handle_verb(parsed, player)
        self.assertTrue(handled)
        self.assertFalse(chair.handled)
        self.assertTrue(player.handled)
        self.assertFalse(chair_in_inventory.handled)

        # check inventory handling
        player.init()
        chair.init()
        chair_in_inventory.init()
        parsed = ParseResult("kerwaffle")
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

    def test_move_notify(self):
        class LocationNotify(Location):
            def notify_npc_left(self, npc, target_location):
                self.npc_left = npc
                self.npc_left_target = target_location
            def notify_npc_arrived(self, npc, previous_location):
                self.npc_arrived = npc
                self.npc_arrived_from = previous_location
            def notify_player_left(self, player, target_location):
                self.player_left = player
                self.player_left_target = target_location
            def notify_player_arrived(self, player, previous_location):
                self.player_arrived = player
                self.player_arrived_from = previous_location
        player = Player("julie", "f")
        room1 = LocationNotify("room1")
        room2 = LocationNotify("room2")
        room1.insert(player, player)
        player.move(room2)
        tale.globalcontext.mud_context.driver.execute_after_player_actions()
        self.assertEqual(room2, player.location)
        self.assertEqual(player, room1.player_left)
        self.assertEqual(room2, room1.player_left_target)
        self.assertEqual(player, room2.player_arrived)
        self.assertEqual(room1, room2.player_arrived_from)

    def test_write_output(self):
        player = Player("julie", "f")
        player.io = ConsoleIo(None)
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            player.tell("hello 1", end=True)
            player.tell("hello 2", end=True)
            player.write_output()
            self.assertEqual("  hello 1\n  hello 2\n", sys.stdout.getvalue())
        finally:
            sys.stdout = old_stdout

    def test_input(self):
        player = Player("julie", "f")
        player.io = ConsoleIo(None)
        old_stdout = sys.stdout
        old_stdin = sys.stdin
        sys.stdout = StringIO()
        sys.stdin = StringIO("input text\n")
        try:
            player.tell("first this text")
            x = player.input("inputprompt")
            self.assertEqual("input text", x)
            self.assertEqual("  first this text\ninputprompt", sys.stdout.getvalue())  # should have outputted the buffered text
        finally:
            sys.stdout = old_stdout
            sys.stdin = old_stdin


class TestTextbuffer(unittest.TestCase):
    def test_empty_lines(self):
        output = TextBuffer()
        output.print("")
        output.print("")
        self.assertEqual([], output.get_paragraphs(), "empty strings shouldn't be stored")
        output.print("", format=False)
        output.print("", format=False)
        self.assertEqual([("\n\n", False)], output.get_paragraphs(), "2 empty strings without format should be stored in 1 paragraph with 2 new lines")
        output.print("", end=True)
        output.print("", end=True)
        self.assertEqual([("\n", True), ("\n", True)], output.get_paragraphs(), "2 empty strings with end=true should be stored in 2 paragraphs")
        output.print("", end=True)
        output.print("", end=True)
        output.print("", end=True)
        self.assertEqual([("\n", True), ("\n", True), ("\n", True)], output.get_paragraphs())
        output.print("")
        output.print("1")
        output.print("2")
        output.print("")
        self.assertEqual([("1\n2\n", True)], output.get_paragraphs())

    def test_end(self):
        output = TextBuffer()
        output.print("1", end=True)
        output.print("2", end=True)
        self.assertEqual([("1\n", True), ("2\n", True)], output.get_paragraphs())
        output.print("one")
        output.print("1", end=True)
        output.print("two")
        output.print("2", end=True)
        output.print("three")
        self.assertEqual([("one\n1\n", True), ("two\n2\n", True), ("three\n", True)], output.get_paragraphs())

    def test_whitespace(self):
        output = TextBuffer()
        output.print("1")
        output.print("2")
        output.print("3")
        self.assertEqual([("1\n2\n3\n", True)], output.get_paragraphs())

    def test_strip(self):
        output = TextBuffer()
        output.print("   1   ", format=True)
        self.assertEqual([("1\n", True)], output.get_paragraphs())
        output.print("   1   ", format=False)
        self.assertEqual([("   1   \n", False)], output.get_paragraphs())


class TestCharacterBuilder(unittest.TestCase):
    def test_build(self):
        b = CharacterBuilder(None)
        pn = b.create_default_player()
        self.assertFalse(pn.wizard)
        pn = b.create_default_wizard()
        self.assertTrue(pn.wizard)
    def test_apply_to(self):
        b = CharacterBuilder(None)
        p = Player("test", "n")
        pn = b.create_default_wizard()
        self.assertFalse("wizard" in p.privileges)
        self.assertEqual("Test", p.title)
        pn.apply_to(p)
        self.assertTrue("wizard" in p.privileges)
        self.assertEqual("irmen", p.name)
        self.assertEqual("human", p.race)
        self.assertEqual("m", p.gender)
        self.assertEqual("arch wizard Irmen", p.title)


if __name__ == '__main__':
    unittest.main()
