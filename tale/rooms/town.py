"""
The central town, which is the place where mud players start/log in

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import copy
import random
import datetime
from ..base import Location, Exit, Door, Item, Container, heartbeat
from ..npc import NPC, Monster
from ..errors import ActionRefused, StoryCompleted
from ..items.basic import trashcan, newspaper, gem, worldclock
from ..util import message_nearby_locations, input
from .. import globals
from .. import lang

square = Location("Essglen Town square",
    """
    The old town square of Essglen. It is not much really, and narrow
    streets quickly lead away from the small fountain in the center.
    """)

lane = Location("Lane of Magicks",
    """
    A long straight road leading to the horizon. Apart from a nearby small tower,
    you can't see any houses or other landmarks. The road seems to go on forever though.
    """)

square.exits["north"] = Exit(lane, "A long straight lane leads north towards the horizon.")
square.exits["lane"] = square.exits["north"]

paper = copy.deepcopy(newspaper)
paper.aliases = {"paper"}


class CursedGem(Item):
    def move(self, target_container, actor, wizard_override=False):
        if self.contained_in is actor and not wizard_override:
            raise ActionRefused("The gem is cursed! It sticks to your hand, you can't get rid of it!")
        super(CursedGem, self).move(target_container, actor, wizard_override)


class InsertOnlyBox(Container):
    def remove(self, item, actor):
        raise ActionRefused("The box is cursed! You can't take anything out of it!")


class RemoveOnlyBox(Container):
    def insert(self, item, actor):
        raise ActionRefused("No matter how hard you try, you can't fit %s in the box." % item.title)

insertonly_box = InsertOnlyBox("box1", "box1 (a black box)")
removeonly_box = RemoveOnlyBox("box2", "box2 (a white box)")
bag = Container("bag")
normal_gem = copy.deepcopy(gem)
removeonly_box.init_inventory([normal_gem])

cursed_gem = CursedGem("black gem", "a black gem")
normal_gem = Item("blue gem", "a blue gem")
clock = copy.deepcopy(worldclock)
lane.exits["south"] = Exit(square, "The town square lies to the south.")


class WizardTowerEntry(Exit):
    def allow_passage(self, actor):
        if "wizard" in actor.privileges:
            actor.tell("You pass through the force-field.")
        else:
            raise ActionRefused("You can't go that way, the force-field is impenetrable.")

lane.exits["west"] = WizardTowerEntry("wizardtower.hall", "To the west is the wizard's tower. It seems to be protected by a force-field.")


class TownCrier(NPC):
    def init(self):
        # note: this npc uses the deferred feature to yell stuff at certain moments/
        # the blubbering idiot NPC uses a heartbeat mechanism (less efficient)
        due = globals.mud_context.driver.game_clock + datetime.timedelta(seconds=5)
        globals.mud_context.driver.defer(due, self, self.do_cry)

    def do_cry(self, driver=None):
        self.tell_others("{Title} yells: welcome everyone!")
        message_nearby_locations(self.location, "Someone nearby is yelling: welcome everyone!")
        due = driver.game_clock + datetime.timedelta(seconds=random.randint(20, 40) * globals.GAMETIME_TO_REALTIME)
        globals.mud_context.driver.defer(due, self, self.do_cry)

    def notify_action(self, parsed, actor):
        if parsed.verb in ("hi", "hello"):
            greet = True
        elif parsed.verb == "say":
            if "hello" in parsed.args or "hi" in parsed.args:
                greet = True
        elif parsed.verb == "greet" and self in parsed.who_info:
            greet = True
        else:
            greet = False
        if greet:
            self.tell_others("{Title} says: \"Hello there, %s.\"" % actor.title)


towncrier = TownCrier("laish", "f", "Laish the town crier",
    """
    The town crier of Essglen is awfully quiet today. She seems rather preoccupied with something.
    """)
towncrier.aliases = {"crier"}


@heartbeat
class VillageIdiot(NPC):
    def init(self):
        self.beats_before_drool = 4

    def heartbeat(self, ctx):
        # note: this village idiot NPC uses a heartbeat mechanism to drool at certain moments.
        # This is less efficient than using a deferred (as the town crier NPC does) because
        # the driver has to call all heartbeats every tick even though they do nothing yet.
        self.beats_before_drool -= 1
        if self.beats_before_drool <= 0:
            self.beats_before_drool = random.randint(10, 20)
            target = random.choice(list(self.location.livings))
            if target is self:
                self.location.tell("%s drools on %sself." % (lang.capital(self.title), self.objective))
            else:
                title = lang.capital(self.title)
                self.location.tell("%s drools on %s." % (title, target.title),
                    specific_targets=[target], specific_target_msg="%s drools on you." % title)


idiot = VillageIdiot("idiot", "m", "blubbering idiot",
    """
    This person's engine is running but there is nobody behind the wheel.
    He is a few beers short of a six-pack. Three ice bricks shy of an igloo.
    Not the sharpest knife in the drawer. Anyway you get the idea: it's an idiot.
    """)

rat = Monster("rat", "n", race="rodent", description="A filthy looking rat. Its whiskers tremble slightly as it peers back at you.")

ant = NPC("ant", "n", race="insect")

square.init_inventory([cursed_gem, normal_gem, paper, trashcan, bag, insertonly_box, removeonly_box, clock, towncrier, idiot, rat, ant])

alley = Location("Alley of doors", "An alley filled with doors.")
descr = "The doors seem to be connected to the computer nearby."
door1 = Door(alley, "Door one.", long_description=descr, direction="door one", locked=False, opened=True)
door2 = Door(alley, "Door two,", long_description=descr, direction="door two", locked=True, opened=True)
door3 = Door(alley, "Door three.", long_description=descr, direction="door three", locked=False, opened=False)
door4 = Door(alley, "Door four.", long_description=descr, direction="door four", locked=True, opened=False)

alley.add_exits([door1, door2, door3, door4])
alley.exits["first door"] = alley.exits["door one"]
alley.exits["second door"] = alley.exits["door two"]
alley.exits["third door"] = alley.exits["door three"]
alley.exits["fourth door"] = alley.exits["door four"]
alley.exits["north"] = Exit(square, "You can go north which brings you back to the square.")
square.exits["alley"] = Exit(alley, "There's an alley to the south.")
square.exits["south"] = square.exits["alley"]


class GameEnd(Location):
    def init(self):
        pass

    def insert(self, obj, actor):
        if obj is globals.mud_context.player:
            # Player entered this location!
            # The StoryCompleted exception is an immediate game end trigger.
            # This means the player never actually enters this location
            # (because the insert call aborts with an exception)
            # raise StoryCompleted(self.completion)
            obj.story_completed(self.completion)
            # setting the status on the player is usually better,
            # it allows the driver to complete the last player action normally.
        return super(GameEnd, self).insert(obj, actor)

    def completion(self, player, driver):
        player.tell("\n")
        player.tell("Congratulations! You beat the game!")
        if globals.MAX_SCORE:
            player.tell("\n")
            player.tell("You scored %d (out of %d) in %d turns." % (player.score, globals.MAX_SCORE, player.turns))
        driver.write_output()
        input("\nPress enter to continue. ")
        player.tell("\n")
        player.tell("Hope you had fun!")


game_end = GameEnd("Game End", "It seems like it is game over!")
lane.exits["east"] = Exit(game_end, "To the east, it looks like it is game over.")


class Computer(Item):
    def allow_move(self, actor):
        raise ActionRefused("You can't move the computer.")

    @property
    def description(self):
        return "It seems to be connected to the four doors. "  \
                + self.screen_text()  \
                + " There's also a small keyboard to type commands."

    def screen_text(self):
        txt = ["The screen of the computer reads:  \""]
        for door in (door1, door2, door3, door4):
            txt.append(door.name.upper())
            txt.append(": LOCKED. " if door.locked else ": UNLOCKED. ")
        txt.append(" AWAITING COMMAND.\"")
        return "".join(txt)

    def read(self, actor):
        actor.tell(self.screen_text())

    def process_typed_command(self, command, doorname, actor):
        if command == "help":
            message = "KNOWN COMMANDS: LOCK, UNLOCK"
        elif command in ("hi", "hello"):
            message = "GREETINGS, PROFESSOR FALKEN."
        elif command in ("unlock", "lock"):
            try:
                door = self.location.exits[doorname]
            except KeyError:
                message = "UNKNOWN DOOR"
            else:
                if command == "unlock":
                    door.locked = False
                    message = doorname.upper() + " UNLOCKED"
                else:
                    door.locked = True
                    message = doorname.upper() + " LOCKED"
        else:
            message = "INVALID COMMAND"
        actor.tell("The computer beeps quietly. The screen shows: \"%s\"" % message)

    def notify_action(self, parsed, actor):
        if parsed.verb in ("hello", "hi"):
            self.process_typed_command("hello", "", actor)
        elif parsed.verb in ("say", "yell"):
            if "hi" in parsed.args or "hello" in parsed.args:
                self.process_typed_command("hello", "", actor)
            else:
                actor.tell("The computer beeps softly. The screen shows: \"I CAN'T HEAR YOU. PLEASE TYPE COMMANDS INSTEAD OF SPEAKING.\"  How odd.")

    def handle_verb(self, parsed, actor):
        if parsed.verb == "hack" and self in parsed.who_info:
            actor.tell("It doesn't need to be hacked, you can just type commands on it.")
            return True
        if parsed.verb in ("type", "enter"):
            if parsed.who_info and self not in parsed.who_info:
                raise ActionRefused("You need to type it on the computer.")
            if parsed.message:
                # type "blabla" on computer (message between quotes)
                action, _, door = parsed.message.partition(" ")
                self.process_typed_command(action, door, actor)
                return True
            args = list(parsed.args)
            if self.name in args:
                args.remove(self.name)
            for name in self.aliases:
                if name in args:
                    args.remove(name)
            if args:
                args.append("")
                self.process_typed_command(args[0], args[1], actor)
                return True
        return False


computer = Computer("computer")
computer.verbs = ["hack", "type", "enter"]
computer.aliases = {"keyboard", "screen"}
alley.insert(computer, None)
