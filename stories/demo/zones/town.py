# coding=utf-8
"""
The central town, which is the place where mud players start/log in

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
from tale.base import Location, Exit, Door, Item, Container, Key, clone
from tale.npc import NPC
from tale.player import Player
from tale.errors import ActionRefused
from tale.items.basic import trashcan, newspaper, gem, gameclock, pouch
from tale.items.board import bulletinboard
from npcs.town_creatures import TownCrier, VillageIdiot, WalkingRat


def init(driver):
    # called when zone is first loaded
    board.load()
    pass


square = Location("Town square",
    """
    The old town square of the village. It is not much really, and narrow
    streets quickly lead away from the small fountain in the center.
    """)

lane = Location("Lane of Magicks",
    """
    A long straight road leading to the horizon. Apart from a nearby small tower,
    you can't see any houses or other landmarks. The road seems to go on forever though.
    """)

square.add_exits([Exit(["north", "lane"], lane, "A long straight lane leads north towards the horizon.")])

paper = clone(newspaper)
paper.aliases = {"paper"}
paper.short_description = "Last day's newspaper lies on the floor."

# add a bulletin board to the town
board = clone(bulletinboard)
board.posts = [
    {
        "author": "irmen",
        "date": "2015-05-23",
        "subject": "hello and welcome to this world",
        "text": "Hello all who read this! Welcome to this world."
    },
    {
        "author": "irmen",
        "date": "2015-05-23",
        "subject": "behavior",
        "text": "Please behave responsibly.\n\nSigned, Irmen"
    },
]
# try to load the persisted board messages:
board.storage_file = "boards/board.json"
lane.init_inventory([board])


class CursedGem(Item):
    def move(self, target, actor, silent=False, is_player=False, verb="move"):
        if self.contained_in is actor and "wizard" not in actor.privileges:
            raise ActionRefused("The gem is cursed! It sticks to your hand, you can't get rid of it!")
        super(CursedGem, self).move(target, actor, verb=verb)


class InsertOnlyBox(Container):
    def remove(self, item, actor):
        raise ActionRefused("The box is cursed! You can't take anything out of it!")


class RemoveOnlyBox(Container):
    def insert(self, item, actor):
        raise ActionRefused("No matter how hard you try, you can't fit %s in the box." % item.title)


insertonly_box = InsertOnlyBox("box1", "box1 (a black box)")
removeonly_box = RemoveOnlyBox("box2", "box2 (a white box)")
normal_gem = clone(gem)
removeonly_box.init_inventory([normal_gem])

cursed_gem = CursedGem("black gem")
cursed_gem.aliases = {"gem"}
normal_gem = Item("blue gem")
normal_gem.aliases = {"gem"}
lane.add_exits([Exit("south", square, "The town square lies to the south.")])
lane.add_exits([Exit(["shop", "north east", "northeast", "ne"], "shoppe.shop", "There's a curiosity shop to the north-east.")])


class WizardTowerEntry(Exit):
    def allow_passage(self, actor):
        if "wizard" in actor.privileges:
            actor.tell("You pass through the force-field.")
        else:
            raise ActionRefused("You can't go that way, the force-field is impenetrable.")


lane.add_exits([WizardTowerEntry("west", "wizardtower.hall", "To the west is the wizard's tower. It seems to be protected by a force-field.")])

towncrier = TownCrier("laish", "f", title="Laish the town crier", description="The town crier is awfully quiet today. She seems rather preoccupied with something.")
towncrier.aliases = {"crier", "town crier"}

idiot = VillageIdiot("idiot", "m", title="blubbering idiot", description="""
    This person's engine is running but there is nobody behind the wheel.
    He is a few beers short of a six-pack. Three ice bricks shy of an igloo.
    Not the sharpest knife in the drawer. Anyway you get the idea: it's an idiot.
    """)

rat = WalkingRat("rat", "n", race="rodent", description="A filthy looking rat. Its whiskers tremble slightly as it peers back at you.")

ant = NPC("ant", "n", race="insect", short_description="A single ant seems to have lost its way.")

clock = clone(gameclock)
clock.short_description = "On the pavement lies a clock, it seems to be working still."

square.init_inventory([cursed_gem, normal_gem, paper, trashcan, pouch, insertonly_box, removeonly_box, clock, towncrier, idiot, rat, ant])


class AlleyOfDoors(Location):
    def notify_player_arrived(self, player, previous_location):
        if previous_location is self:
            player.tell("...Weird... The door you just entered seems to go back to the same place you came from...")


alley = AlleyOfDoors("Alley of doors", "An alley filled with doors.")
descr = "The doors seem to be connected to the computer nearby."
door1 = Door(["first door", "door one"], alley, "There's a door marked 'door one'.", long_description=descr, locked=False, opened=True)
door2 = Door(["second door", "door two"], alley, "There's a door marked 'door two'.", long_description=descr, locked=True, opened=False)
door3 = Door(["third door", "door three"], alley, "There's a door marked 'door three'.", long_description=descr, locked=False, opened=False)
door4 = Door(["fourth door", "door four"], alley, "There's a door marked 'door four'.", long_description=descr, locked=True, opened=False)
alley.add_exits([
    door1, door2, door3, door4,
    Exit(["north", "square"], square, "You can go north which brings you back to the square."),
])

square.add_exits([Exit(["alley", "south"], alley, "There's an alley to the south.", "It looks like a very small alley, but you can walk through it.")])


class GameEnd(Location):
    def init(self):
        pass

    def insert(self, obj, actor):
        # Normally you would use notify_player_arrived() to trigger an action.
        # but for the game ending, we require an immediate response.
        # So instead we hook into the direct arrival of something in this location.
        super(GameEnd, self).insert(obj, actor)
        try:
            obj.story_completed()   # player arrived! Great Success!
        except AttributeError:
            pass


game_end = GameEnd("Game End", "It seems like it is game over!")


class EndDoor(Door):
    def unlock(self, actor, item):
        super(EndDoor, self).unlock(actor, item)
        if not self.locked:
            if "unlocked_enddoor" not in actor.hints.checkpoints:
                actor.tell_later("<dim>(You will remember this event.)</>")
            actor.hints.checkpoint("unlocked_enddoor", "The way to freedom lies before you!")


end_door = EndDoor(["east", "door"], game_end, "To the east is a door with a sign 'Game Over' on it.", locked=True, opened=False)
end_door.key_code = 999
lane.add_exits([end_door])


class Computer(Item):
    def init(self):
        super(Computer, self).init()
        self.aliases = {"keyboard", "screen", "wires"}

    def allow_item_move(self, actor, verb="move"):
        raise ActionRefused("You can't %s the computer." % verb)

    @property
    def description(self):
        return "It seems to be connected to the four doors. " \
               + self.screen_text() \
               + " There's also a small keyboard to type commands. " \
               + " On the side of the screen there's a large sticker with 'say hello' written on it."

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
                    if door.locked:
                        door.locked = False
                        message = doorname.upper() + " UNLOCKED"
                    else:
                        message = "COMMAND INVALID - DOOR ALREADY UNLOCKED"
                else:
                    if door.locked:
                        message = "COMMAND INVALID - DOOR ALREADY LOCKED"
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
                actor.tell("The computer beeps quietly. The screen shows: \"I CAN'T HEAR YOU. PLEASE TYPE COMMANDS INSTEAD OF SPEAKING.\"  How odd.")

    def handle_verb(self, parsed, actor):
        if parsed.verb == "hack":
            if self in parsed.who_info:
                actor.tell("It doesn't need to be hacked, you can just type commands on it.")
                return True
            elif parsed.who_info:
                raise ActionRefused("You can't hack that.")
            else:
                raise ActionRefused("What do you want to hack?")
        if parsed.verb in ("type", "enter"):
            if parsed.who_info and self not in parsed.who_info:
                raise ActionRefused("You need to type it on the computer.")
            if parsed.message:
                # type "bla bla" on computer (message between quotes)
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


computer = Computer("computer", short_description="A computer is connected to the doors via a couple of wires.")
computer.verbs = {
    # register some custom verbs. You can redefine existing verbs, so be careful.
    "hack": "Attempt to hack an electronic device.",
    "type": "Enter some text.",
    "enter": "Enter some text.",
}
alley.insert(computer, None)


class DoorKey(Key):
    def notify_moved(self, source_container, target_container, actor):
        # check if a player picked up this key
        player = None
        if type(target_container) is Player:
            player = target_container
        elif type(self.contained_in) is Player:
            player = self.contained_in
        if player:
            if "got_doorkey" not in actor.hints.checkpoints:
                actor.tell_later("<dim>(You will remember this event.)</>")
            player.hints.checkpoint("got_doorkey", "You've found something that might open the exit.")


doorkey = DoorKey("key", description="A key with a little label marked 'Game Over'.")
doorkey.key_for(end_door)
alley.insert(doorkey, None)


class MagicGameEnd(Item):
    def __init__(self):
        super(MagicGameEnd, self).__init__("magic orb", description="A magic orb of some sort.")
        self.aliases = "orb"

    def notify_moved(self, source_container, target_container, actor):
        actor.tell_later("By touching it you immediately end the game!")
        actor.story_completed()


alley.insert(MagicGameEnd(), None)
