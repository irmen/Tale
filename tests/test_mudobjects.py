"""
Unittests for Mud base objects

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import unittest
import datetime
import tale.globals


class DummyDriver(object):
    def __init__(self):
        self.heartbeats = set()
        self.exits = []
        self.game_clock = datetime.datetime.now()
        self.deferreds = []
    def register_heartbeat(self, obj):
        self.heartbeats.add(obj)
    def unregister_heartbeat(self, obj):
        self.heartbeats.discard(obj)
    def register_exit(self, exit):
        self.exits.append(exit)
    def defer(self, due, owner, callable, *vargs, **kwargs):
        self.deferreds.append((due, owner, callable))
    def remove_deferreds(self, owner):
        self.deferreds = [(d[0], d[1], d[2]) for d in self.deferreds if d[1] is not owner]


from tale.globals import mud_context
mud_context.driver = DummyDriver()

from tale.base import Location, Exit, Item, Living, MudObject, _Limbo, Container, Weapon, Door
from tale.errors import SecurityViolation, ActionRefused, ParseError
from tale.npc import NPC, Monster
from tale.player import Player
from tale.soul import NonSoulVerb
import tale.rooms
tale.rooms.init(mud_context.driver)


class Wiretap(object):
    def __init__(self):
        self.msgs = []
    def tell(self, msg):
        self.msgs.append(msg)
    def clear(self):
        self.msgs = []


class MsgTraceNPC(NPC):
    def init(self):
        self._init_called = True
        self.clearmessages()
    def clearmessages(self):
        self.messages = []
    def tell(self, *messages):
        self.messages.extend(messages)


class TestLocations(unittest.TestCase):
    def setUp(self):
        mud_context.driver = DummyDriver()
        self.hall = Location("Main hall", "A very large hall.")
        self.attic = Location("Attic", "A dark attic.")
        self.street = Location("Street", "An endless street.")
        self.hall.exits["up"] = Exit(self.attic, "A ladder leads up.")
        self.hall.exits["door"] = Exit(self.street, "A heavy wooden door to the east blocks the noises from the street outside.")
        self.hall.exits["east"] = self.hall.exits["door"]
        self.table = Item("table", "oak table", "a large dark table with a lot of cracks in its surface")
        self.key = Item("key", "rusty key", "an old rusty key without a label")
        self.magazine = Item("magazine", "university magazine")
        self.rat = NPC("rat", "n", race="rodent")
        self.julie = NPC("julie", "f", "attractive Julie",
                     """
                     She's quite the looker.
                     """)
        self.julie.aliases = {"chick"}
        self.player = Player("player", "m")
        self.pencil = Item("pencil", title="fountain pen")
        self.pencil.aliases = {"pen"}
        self.bag = Container("bag")
        self.notebook_in_bag = Item("notebook")
        self.bag.insert(self.notebook_in_bag, self.player)
        self.player.insert(self.pencil, self.player)
        self.player.insert(self.bag, self.player)
        self.hall.init_inventory([self.table, self.key, self.magazine, self.rat, self.julie, self.player])

    def test_contains(self):
        self.assertTrue(self.julie in self.hall)
        self.assertTrue(self.magazine in self.hall)
        self.assertFalse(self.pencil in self.hall)
        self.assertFalse(self.magazine in self.attic)
        self.assertFalse(self.julie in self.attic)

    def test_look(self):
        expected = ["[Main hall]", "A very large hall.",
                    "A heavy wooden door to the east blocks the noises from the street outside. A ladder leads up.",
                    "You see an oak table, a rusty key, and a university magazine. Player, attractive Julie, and rat are here."]
        self.assertEqual(expected, self.hall.look())
        expected = ["[Main hall]", "A very large hall.",
                    "A heavy wooden door to the east blocks the noises from the street outside. A ladder leads up.",
                    "You see an oak table, a rusty key, and a university magazine. Attractive Julie and rat are here."]
        self.assertEqual(expected, self.hall.look(exclude_living=self.player))
        expected = ["[Attic]", "A dark attic."]
        self.assertEqual(expected, self.attic.look())

    def test_look_short(self):
        expected = ["[Attic]"]
        self.assertEqual(expected, self.attic.look(short=True))
        expected = ["[Main hall]", "Exits: door, east, up", "You see: key, magazine, table", "Present: julie, player, rat"]
        self.assertEqual(expected, self.hall.look(short=True))
        expected = ["[Main hall]", "Exits: door, east, up", "You see: key, magazine, table", "Present: julie, rat"]
        self.assertEqual(expected, self.hall.look(exclude_living=self.player, short=True))

    def test_search_living(self):
        self.assertEqual(None, self.hall.search_living("<notexisting>"))
        self.assertEqual(None, self.attic.search_living("<notexisting>"))
        self.assertEqual(self.rat, self.hall.search_living("rat"))
        self.assertEqual(self.julie, self.hall.search_living("Julie"))
        self.assertEqual(self.julie, self.hall.search_living("attractive julie"))
        self.assertEqual(self.julie, self.hall.search_living("chick"))
        self.assertEqual(None, self.hall.search_living("bloke"))

    def test_search_item(self):
        # almost identical to locate_item so only do a few basic tests
        self.assertEqual(None, self.player.search_item("<notexisting>"))
        self.assertEqual(self.pencil, self.player.search_item("pencil"))

    def test_locate_item(self):
        item, container = self.player.locate_item("<notexisting>")
        self.assertEqual(None, item)
        self.assertEqual(None, container)
        item, container = self.player.locate_item("pencil")
        self.assertEqual(self.pencil, item)
        self.assertEqual(self.player, container)
        item, container = self.player.locate_item("fountain pen")
        self.assertEqual(self.pencil, item, "need to find the title")
        item, container = self.player.locate_item("pen")
        self.assertEqual(self.pencil, item, "need to find the alias")
        item, container = self.player.locate_item("pencil", include_inventory=False)
        self.assertEqual(None, item)
        self.assertEqual(None, container)
        item, container = self.player.locate_item("key")
        self.assertEqual(self.key, item)
        self.assertEqual(self.hall, container)
        item, container = self.player.locate_item("key", include_location=False)
        self.assertEqual(None, item)
        self.assertEqual(None, container)
        item, container = self.player.locate_item("KEY")
        self.assertEqual(self.key, item, "should work case-insensitive")
        self.assertEqual(self.hall, container, "should work case-insensitive")
        item, container = self.player.locate_item("notebook")
        self.assertEqual(self.notebook_in_bag, item)
        self.assertEqual(self.bag, container, "should search in bags in inventory")
        item, container = self.player.locate_item("notebook", include_containers_in_inventory=False)
        self.assertEqual(None, item)
        self.assertEqual(None, container, "should not search in bags in inventory")

    def test_tell(self):
        rat = MsgTraceNPC("rat", "n", "rodent")
        self.assertTrue(rat._init_called, "init() must be called from __init__")
        julie = MsgTraceNPC("julie", "f", "human")
        hall = Location("hall")
        hall.livings = [rat, julie]
        hall.tell("roommsg")
        self.assertEqual(["roommsg"], rat.messages)
        self.assertEqual(["roommsg"], julie.messages)
        rat.clearmessages()
        julie.clearmessages()
        hall.tell("roommsg", rat, [julie], "juliemsg")
        self.assertEqual([], rat.messages)
        self.assertEqual(["juliemsg"], julie.messages)

    def test_enter_leave(self):
        hall = Location("hall")
        rat1 = NPC("rat1", "n")
        rat2 = NPC("rat2", "n")
        julie = NPC("julie", "f")
        with self.assertRaises(TypeError):
            hall.insert(12345, julie)
        self.assertEqual(_Limbo, rat1.location)
        self.assertFalse(rat1 in hall.livings)
        wiretap = Wiretap()
        hall.wiretaps.add(wiretap)
        hall.insert(rat1, julie)
        self.assertEqual(hall, rat1.location)
        self.assertTrue(rat1 in hall.livings)
        self.assertEqual([], wiretap.msgs, "insert shouldn't produce arrival messages")
        hall.insert(rat2, julie)
        self.assertTrue(rat2 in hall.livings)
        self.assertEqual([], wiretap.msgs, "insert shouldn't produce arrival messages")
        # now test leave
        wiretap.clear()
        hall.remove(rat1, julie)
        self.assertFalse(rat1 in hall.livings)
        self.assertIsNone(rat1.location)
        self.assertEqual([], wiretap.msgs, "remove shouldn't produce exit message")
        hall.remove(rat2, julie)
        self.assertFalse(rat2 in hall.livings)
        self.assertEqual([], wiretap.msgs, "remove shouldn't produce exit message")
        # test random leave
        hall.remove(rat1, julie)
        hall.remove(12345, julie)


class TestDoorsExits(unittest.TestCase):
    def test_actions(self):
        player = Player("julie", "f")
        hall = Location("hall")
        attic = Location("attic")
        unbound_exit = Exit("foo.bar", "a random exit")
        with self.assertRaises(Exception):
            self.assertFalse(unbound_exit.allow_passage(player))  # should fail because not bound
        exit1 = Exit(attic, "first ladder to attic")
        exit1.allow_passage(player)

        door = Door(hall, "open unlocked door", direction="north", locked=False, opened=True)
        with self.assertRaises(ActionRefused) as x:
            door.open(None, player)  # fail, it's already open
        self.assertTrue("already" in str(x.exception))
        door.close(None, player)
        self.assertFalse(door.opened, "must be closed")
        with self.assertRaises(ActionRefused) as x:
            door.lock(None, player)  # default door can't be locked
        self.assertTrue("can't" in str(x.exception))
        with self.assertRaises(ActionRefused) as x:
            door.unlock(None, player)  # fail, it's not locked
        self.assertTrue("not" in str(x.exception))

        door = Door(hall, "open locked door", direction="north", locked=True, opened=True)
        with self.assertRaises(ActionRefused) as x:
            door.open(None, player)  # fail, it's already open
        self.assertTrue("already" in str(x.exception))
        door.close(None, player)
        with self.assertRaises(ActionRefused) as x:
            door.lock(None, player)  # it's already locked
        self.assertTrue("already" in str(x.exception))
        with self.assertRaises(ActionRefused) as x:
            door.unlock(None, player)  # you can't unlock it
        self.assertTrue("can't" in str(x.exception))

        door = Door(hall, "closed unlocked door", direction="north", locked=False, opened=False)
        door.open(None, player)
        self.assertTrue(door.opened)
        door.close(None, player)
        self.assertFalse(door.opened)
        with self.assertRaises(ActionRefused) as x:
            door.close(None, player)  # it's already closed
        self.assertTrue("already" in str(x.exception))

        door = Door(hall, "closed locked door", direction="north", locked=True, opened=False)
        with self.assertRaises(ActionRefused) as x:
            door.open(None, player)  # can't open it, it's locked
        self.assertTrue("can't" in str(x.exception))
        with self.assertRaises(ActionRefused) as x:
            door.close(None, player)  # it's already closed
        self.assertTrue("already" in str(x.exception))

        door = Door(hall, "Some door.", direction="north")
        self.assertEqual("Some door.", door.short_description)
        self.assertEqual("Some door. It is open and unlocked.", door.long_description)
        self.assertTrue(door.opened)
        self.assertFalse(door.locked)
        door = Door(hall, "Some door.", "This is a peculiar door leading north.", direction="north")
        self.assertEqual("Some door.", door.short_description)
        self.assertEqual("This is a peculiar door leading north. It is open and unlocked.", door.long_description)

    def test_exits(self):
        hall = Location("hall")
        attic = Location("attic")
        exit1 = Exit(attic, "The first ladder leads to the attic.")
        exit2 = Exit(attic, "Second ladder to attic.", direction="up")
        exit3 = Exit(attic, "Third ladder to attic.", direction="ladder")
        exit4 = Exit(attic, "A window.", "A window, maybe if you open it you can get out?", "window")
        with self.assertRaises(ValueError):
            hall.add_exits([exit1])    # direction must be specified
        hall.add_exits([exit2, exit3, exit4])
        self.assertTrue(hall.exits["up"] is exit2)
        self.assertTrue(hall.exits["ladder"] is exit3)
        self.assertTrue(hall.exits["window"] is exit4)
        self.assertEqual(['[hall]', 'Third ladder to attic. Second ladder to attic. A window.'], hall.look())
        self.assertEqual("Third ladder to attic.", exit3.long_description)
        self.assertEqual("A window, maybe if you open it you can get out?", exit4.long_description)
        with self.assertRaises(ActionRefused):
            exit1.activate(None)
        with self.assertRaises(ActionRefused):
            exit1.deactivate(None)
        with self.assertRaises(ActionRefused):
            exit1.close(None, None)
        with self.assertRaises(ActionRefused):
            exit1.open(None, None)
        with self.assertRaises(ActionRefused):
            exit1.lock(None, None)
        with self.assertRaises(ActionRefused):
            exit1.unlock(None, None)
        with self.assertRaises(ActionRefused):
            exit1.manipulate("frobnitz", None)

    def test_bind_exit(self):
        exit = Exit("town.square", "someplace")
        self.assertFalse(exit.bound)
        exit.bind(tale.rooms)
        self.assertTrue(exit.bound)
        self.assertEqual(tale.rooms.town.square, exit.target)
        exit.bind(tale.rooms)


class TestLiving(unittest.TestCase):
    def test_contains(self):
        orc = Living("orc", "m")
        axe = Weapon("axe")
        orc.insert(axe, orc)
        self.assertTrue(axe in orc)
        self.assertTrue(axe in orc.inventory())
        self.assertEqual(1, orc.inventory_size())
        self.assertEqual(1, len(orc.inventory()))
    def test_allowance(self):
        orc = Living("orc", "m")
        idiot = NPC("idiot", "m")
        player = Player("julie", "f")
        axe = Weapon("axe")
        orc.insert(axe, orc)
        self.assertTrue(axe in orc)
        with self.assertRaises(ActionRefused) as x:
            orc.remove(axe, None)
        self.assertTrue("can't take" in str(x.exception))
        orc.remove(axe, orc)
        self.assertFalse(axe in orc)
    def test_move(self):
        hall = Location("hall")
        attic = Location("attic")
        rat = Living("rat", "n")
        hall.init_inventory([rat])
        wiretap_hall = Wiretap()
        wiretap_attic = Wiretap()
        hall.wiretaps.add(wiretap_hall)
        attic.wiretaps.add(wiretap_attic)
        self.assertTrue(rat in hall.livings)
        self.assertFalse(rat in attic.livings)
        self.assertEqual(hall, rat.location)
        rat.move(attic)
        self.assertTrue(rat in attic.livings)
        self.assertFalse(rat in hall.livings)
        self.assertEqual(attic, rat.location)
        self.assertEqual(["Rat leaves."], wiretap_hall.msgs)
        self.assertEqual(["Rat arrives."], wiretap_attic.msgs)
        # now try silent
        wiretap_attic.clear()
        wiretap_hall.clear()
        rat.move(hall, silent=True)
        self.assertTrue(rat in hall.livings)
        self.assertFalse(rat in attic.livings)
        self.assertEqual(hall, rat.location)
        self.assertEqual([], wiretap_hall.msgs)
        self.assertEqual([], wiretap_attic.msgs)
    def test_lang(self):
        living = Living("julie", "f")
        self.assertEqual("her", living.objective)
        self.assertEqual("her", living.possessive)
        self.assertEqual("she", living.subjective)
        self.assertEqual("f", living.gender)
        living = Living("max", "m")
        self.assertEqual("him", living.objective)
        self.assertEqual("his", living.possessive)
        self.assertEqual("he", living.subjective)
        self.assertEqual("m", living.gender)
        living = Living("herp", "n")
        self.assertEqual("it", living.objective)
        self.assertEqual("its", living.possessive)
        self.assertEqual("it", living.subjective)
        self.assertEqual("n", living.gender)


class TestNPC(unittest.TestCase):
    def test_init(self):
        rat = NPC("rat", "n", race="rodent")
        julie = NPC("julie", "f", "attractive Julie",
                    """
                    She's quite the looker.
                    """)
        self.assertFalse(julie.aggressive)
        self.assertEqual("julie", julie.name)
        self.assertEqual("attractive Julie", julie.title)
        self.assertEqual("She's quite the looker.", julie.description)
        self.assertEqual("human", julie.race)
        self.assertEqual("f", julie.gender)
        self.assertTrue(1 < julie.stats["agi"] < 100)
        self.assertEqual("rat", rat.name)
        self.assertEqual("rat", rat.title)
        self.assertEqual("rodent", rat.race)
        self.assertEqual("", rat.description)
        self.assertEqual("n", rat.gender)
        self.assertTrue(1 < rat.stats["agi"] < 100)
        dragon = Monster("dragon", "f", race="dragon")
        self.assertTrue(dragon. aggressive)


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
        self.assertEqual(["\a   xyz   \n  123", "\n"], player.get_output_lines())
        player.tell("line1", end=True)
        player.tell("\n")
        player.tell("line2", end=True)
        player.tell("\n")
        player.tell("\n")
        self.assertEqual(["line1", "\n", "\n", "line2", "\n", "\n", "\n"], player.get_output_lines())
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
        self.assertEqual(("word " * 30).strip(), player.get_wrapped_output_lines(), "when format=False output should be unformatted")
        player.tell("   xyz   \n  123", format=False)
        self.assertEqual("   xyz   \n  123", player.get_wrapped_output_lines())
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
        with self.assertRaises(ParseError):
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


class TestDescriptions(unittest.TestCase):
    def test_name(self):
        item = Item("key")
        self.assertEqual("key", item.name)
        self.assertEqual("key", item.title)
        self.assertEqual("", item.description)
    def test_title(self):
        item = Item("key", "rusty old key")
        self.assertEqual("key", item.name)
        self.assertEqual("rusty old key", item.title)
        self.assertEqual("", item.description)
    def test_description(self):
        item = Item("key", "rusty old key", "a small old key that's rusted")
        self.assertEqual("key", item.name)
        self.assertEqual("rusty old key", item.title)
        self.assertEqual("a small old key that's rusted", item.description)
        item = Item("key", "rusty old key",
                    """
                    a very small, old key that's rusted
                    """)
        self.assertEqual("key", item.name)
        self.assertEqual("rusty old key", item.title)
        self.assertEqual("a very small, old key that's rusted", item.description)

    def test_dynamic_description_by_using_property(self):
        import time
        class DynamicThing(Item):
            @property
            def description(self):
                return "The watch shows %f" % time.time()
            @property
            def title(self):
                return "a watch showing %f" % time.time()
        watch = DynamicThing("watch")
        title1 = watch.title
        descr1 = watch.description
        self.assertTrue(descr1.startswith("The watch shows "))
        self.assertTrue(title1.startswith("a watch showing "))
        time.sleep(0.02)
        self.assertNotEqual(title1, watch.title)
        self.assertNotEqual(descr1, watch.description)


class TestDestroy(unittest.TestCase):
    def setUp(self):
        mud_context.driver = DummyDriver()
    def test_destroy_base(self):
        ctx = {}
        o = MudObject("x")
        o.destroy(ctx)
    def test_destroy_loc(self):
        ctx = {}
        loc = Location("loc")
        i = Item("item")
        liv = Living("rat", "n")
        loc.exits = {"north": Exit("somewhere", "somewhere")}
        player = Player("julie", "f")
        player.privileges = {"wizard"}
        player.create_wiretap(loc)
        loc.init_inventory([i, liv, player])
        self.assertTrue(len(loc.exits) > 0)
        self.assertTrue(len(loc.items) > 0)
        self.assertTrue(len(loc.livings) > 0)
        self.assertTrue(len(loc.wiretaps) > 0)
        self.assertEqual(loc, player.location)
        self.assertEqual(loc, liv.location)
        self.assertTrue(len(player.installed_wiretaps) > 0)
        loc.destroy(ctx)
        self.assertTrue(len(loc.exits) == 0)
        self.assertTrue(len(loc.items) == 0)
        self.assertTrue(len(loc.livings) == 0)
        self.assertTrue(len(loc.wiretaps) == 0)
        self.assertTrue(len(player.installed_wiretaps) > 0, "wiretap object must remain on player")
        self.assertEqual(_Limbo, player.location)
        self.assertEqual(_Limbo, liv.location)

    def test_destroy_player(self):
        ctx = {}
        loc = Location("loc")
        player = Player("julie", "f")
        player.privileges = {"wizard"}
        player.create_wiretap(loc)
        player.insert(Item("key"), player)
        loc.init_inventory([player])
        self.assertTrue(len(loc.wiretaps) > 0)
        self.assertEqual(loc, player.location)
        self.assertTrue(len(player.installed_wiretaps) > 0)
        self.assertTrue(len(player.inventory()) > 0)
        self.assertTrue(player in loc.livings)
        player.destroy(ctx)
        import gc
        gc.collect()
        self.assertTrue(len(loc.wiretaps) == 0)
        self.assertTrue(len(player.installed_wiretaps) == 0)
        self.assertTrue(len(player.inventory()) == 0)
        self.assertFalse(player in loc.livings)
        self.assertIsNone(player.location, "destroyed player should end up nowhere (None)")

    def test_destroy_item(self):
        thing = Item("thing")
        ctx = {"driver": mud_context.driver}
        thing.destroy(ctx)

    def test_destroy_deferreds(self):
        ctx = {"driver": mud_context.driver}
        thing = Item("thing")
        player = Player("julie", "f")
        wolf = Monster("wolf", "m")
        loc = Location("loc")
        mud_context.driver.defer(datetime.datetime.now(), thing, "method")
        mud_context.driver.defer(datetime.datetime.now(), player, "method")
        mud_context.driver.defer(datetime.datetime.now(), wolf, "method")
        mud_context.driver.defer(datetime.datetime.now(), loc, "method")
        self.assertEqual(4, len(mud_context.driver.deferreds))
        thing.destroy(ctx)
        player.destroy(ctx)
        wolf.destroy(ctx)
        loc.destroy(ctx)
        self.assertEqual(0, len(mud_context.driver.deferreds), "all deferreds must be removed")


class TestContainer(unittest.TestCase):
    def test_container_contains(self):
        bag = Container("bag")
        key = Item("key")
        self.assertEqual(0, len(bag.inventory()))
        self.assertEqual(0, bag.inventory_size())
        npc = NPC("julie", "f")
        bag.insert(key, npc)
        self.assertTrue(key in bag)
        self.assertEqual(1, bag.inventory_size())
        bag.remove(key, npc)
        self.assertEqual(0, bag.inventory_size())
        self.assertFalse(key in bag)
        with self.assertRaises(KeyError):
            bag.remove("not_existing", npc)
    def test_allowance(self):
        bag = Container("bag")
        key = Item("key")
        player = Player("julie", "f")
        with self.assertRaises(Exception):
            bag.insert(None, player)
        bag.insert(key, player)
        with self.assertRaises(KeyError):
            bag.remove(None, player)
        bag.remove(key, player)
        bag.allow_move(player)
        with self.assertRaises(ActionRefused):
            key.insert(bag, player)
        with self.assertRaises(ActionRefused):
            key.remove(bag, player)
        self.assertFalse(key in bag)
        with self.assertRaises(ActionRefused):
            bag in key
    def test_inventory(self):
        bag = Container("bag")
        key = Item("key")
        thing = Item("gizmo")
        player = Player("julie", "f")
        with self.assertRaises(ActionRefused):
            thing in key  # can't check for containment in an Item
        self.assertFalse(thing in bag)
        with self.assertRaises(ActionRefused):
            key.insert(thing, player)  # can't add stuf to an Item
        bag.insert(thing, player)
        self.assertTrue(thing in bag)
    def test_title(self):
        bag = Container("bag", "leather bag", "a small leather bag")
        stone = Item("stone")
        player = Player("julie", "f")
        self.assertEqual("bag", bag.name)
        self.assertEqual("leather bag", bag.title)
        self.assertEqual("a small leather bag", bag.description)
        bag.move(player, player)
        self.assertEqual("bag", bag.name)
        self.assertEqual("leather bag (empty)", bag.title)
        self.assertEqual("a small leather bag", bag.description)
        stone.move(bag, player)
        self.assertEqual("bag", bag.name)
        self.assertEqual("leather bag (containing things)", bag.title)
        self.assertEqual("a small leather bag", bag.description)


class TestItem(unittest.TestCase):
    def test_insertremove(self):
        key = Item("key")
        thing = Item("gizmo")
        player = Player("julie", "f")
        with self.assertRaises(ActionRefused):
            key.remove(None, player)
        with self.assertRaises(ActionRefused):
            key.remove(thing, player)
        with self.assertRaises(ActionRefused):
            key.insert(None, player)
        with self.assertRaises(ActionRefused):
            key.insert(thing, player)
        key.allow_move(player)
        with self.assertRaises(ActionRefused):
            key.inventory()
        with self.assertRaises(ActionRefused):
            key.inventory_size()
    def test_move(self):
        hall = Location("hall")
        person = Living("person", "m")
        monster = Monster("dragon", "f", race="dragon")
        key = Item("key")
        stone = Item("stone")
        hall.init_inventory([person, key])
        stone.move(hall, person)
        wiretap_hall = Wiretap()
        wiretap_person = Wiretap()
        hall.wiretaps.add(wiretap_hall)
        person.wiretaps.add(wiretap_person)
        self.assertTrue(person in hall)
        self.assertTrue(key in hall)
        key.contained_in = person   # hack to force move to actually check the source container
        with self.assertRaises(KeyError):
            key.move(person, person)
        key.contained_in = hall   # put it back as it was
        key.move(person, person)
        self.assertFalse(key in hall)
        self.assertTrue(key in person)
        self.assertEqual([], wiretap_hall.msgs, "item.move() should be silent")
        self.assertEqual([], wiretap_person.msgs, "item.move() should be silent")
        with self.assertRaises(ActionRefused) as x:
            key.move(monster, person)
        self.assertTrue("not a good idea" in str(x.exception))
    def test_lang(self):
        thing = Item("thing")
        self.assertEqual("it", thing.objective)
        self.assertEqual("its", thing.possessive)
        self.assertEqual("it", thing.subjective)
        self.assertEqual("n", thing.gender)
    def test_location(self):
        thingy = Item("thing")
        with self.assertRaises(TypeError):
            thingy.location = "foobar"
        hall = Location("hall")
        thingy.location = hall
        self.assertEqual(hall, thingy.contained_in)
        self.assertEqual(hall, thingy.location)
        person = Living("person", "m")
        key = Item("key")
        backpack = Container("backpack")
        person.insert(backpack, person)
        self.assertIsNone(key.contained_in)
        self.assertIsNone(key.location)
        self.assertTrue(backpack in person)
        self.assertEqual(person, backpack.contained_in)
        self.assertEqual(_Limbo, backpack.location)
        hall.init_inventory([person, key])
        self.assertEqual(hall, key.contained_in)
        self.assertEqual(hall, key.location)
        self.assertEqual(hall, backpack.location)
        key.move(backpack, person)
        self.assertEqual(backpack, key.contained_in)
        self.assertEqual(hall, key.location)


class TestMudObject(unittest.TestCase):
    def test_mudobj(self):
        try:
            x = MudObject("name", "the title", "description")
            self.fail("assertion error expected")
        except AssertionError:
            pass
        x = MudObject("name", "title", "description")
        x.init()
        x.heartbeat(None)
        with self.assertRaises(ActionRefused):
            x.activate(None)
        with self.assertRaises(ActionRefused):
            x.deactivate(None)
        with self.assertRaises(ActionRefused):
            x.manipulate("frobnitz", None)
        x.destroy(None)


if __name__ == '__main__':
    unittest.main()
