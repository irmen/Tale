"""
The central town, which is the place where mud players start/log in

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from typing import Union, Optional

from npcs.town_creatures import TownCrier, VillageIdiot, WalkingRat

from tale.base import Location, Exit, Door, Item, Container, Key, Living, ParseResult, ContainingType
from tale.driver import Driver
from tale.errors import ActionRefused, TaleError, StoryCompleted
from tale.items.basic import trashcan, newspaper, gem, gameclock, pouch
from tale.items.board import bulletinboard
from tale.player import Player


def init(driver: Driver) -> None:
    # called when zone is first loaded
    board.load()
    board.save()  # make sure the storage file exists


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

paper = newspaper.clone()
paper.aliases = {"paper"}
paper.short_description = "Last day's newspaper lies on the floor."

# add a bulletin board to the town, with some initial messages
board = bulletinboard.clone()
board.storage_file = "boards/board.json"
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
lane.init_inventory([board])


class CursedGem(Item):
    def move(self, target: ContainingType, actor: Living=None,
             *, silent: bool=False, is_player: bool=False, verb: str="move", direction_name: str=None) -> None:
        if self.contained_in is actor and "wizard" not in actor.privileges:
            raise ActionRefused("The gem is cursed! It sticks to your hand, you can't get rid of it!")
        super().move(target, actor, verb=verb)


class InsertOnlyBox(Container):
    def remove(self, item: Union[Living, Item], actor: Optional[Living]) -> None:
        raise ActionRefused("The box is cursed! You can't take anything out of it!")


class RemoveOnlyBox(Container):
    def insert(self, item: Union[Living, Item], actor: Optional[Living]) -> None:
        raise ActionRefused("No matter how hard you try, you can't fit %s in the box." % item.title)


insertonly_box = InsertOnlyBox("box1", "box1 (a black box)")
removeonly_box = RemoveOnlyBox("box2", "box2 (a white box)")
normal_gem = gem.clone()
removeonly_box.init_inventory([normal_gem])

cursed_gem = CursedGem("black gem")
cursed_gem.aliases = {"gem"}
normal_gem = Item("blue gem")
normal_gem.aliases = {"gem"}
lane.add_exits([Exit("south", square, "The town square lies to the south.")])
lane.add_exits([Exit(["shop", "north east", "northeast", "ne"], "shoppe.shop", "There's a curiosity shop to the north-east.")])


class WizardTowerEntry(Exit):
    def allow_passage(self, actor: Living) -> None:
        if "wizard" in actor.privileges:
            actor.tell("You pass through the force-field.")
        else:
            raise ActionRefused("You can't go that way, the force-field is impenetrable.")


lane.add_exits([WizardTowerEntry("west", "wizardtower.hall",
                                 "To the west is the wizard's tower. It seems to be protected by a force-field.")])

towncrier = TownCrier("laish", "f", title="Laish the town crier",
                      descr="The town crier is awfully quiet today. She seems rather preoccupied with something.")
towncrier.aliases = {"crier", "town crier"}

idiot = VillageIdiot("idiot", "m", title="blubbering idiot", descr="""
    This person's engine is running but there is nobody behind the wheel.
    He is a few beers short of a six-pack. Three ice bricks shy of an igloo.
    Not the sharpest knife in the drawer. Anyway you get the idea: it's an idiot.
    """)

rat = WalkingRat("rat", "n", race="rodent", descr="A filthy looking rat. Its whiskers tremble slightly as it peers back at you.")

ant = Living("ant", "n", race="insect", short_descr="A single ant seems to have lost its way.")

clock = gameclock.clone()
clock.short_description = "On the pavement lies a clock, it seems to be working still."

square.init_inventory([cursed_gem, normal_gem, paper, trashcan, pouch, insertonly_box, removeonly_box, clock, towncrier, idiot, rat, ant])


class AlleyOfDoors(Location):
    def notify_player_arrived(self, player: Player, previous_location: Location) -> None:
        if previous_location is self:
            player.tell("...Weird... The door you just entered seems to go back to the same place you came from...")


alley = AlleyOfDoors("Alley of doors", "An alley filled with doors.")
descr = "The doors seem to be connected to the computer nearby."
door1 = Door(["first door", "door one"], alley, "There's a door marked 'door one'.", long_descr=descr, locked=False, opened=True)
door2 = Door(["second door", "door two"], alley, "There's a door marked 'door two'.", long_descr=descr, locked=True, opened=False)
door3 = Door(["third door", "door three"], alley, "There's a door marked 'door three'.", long_descr=descr, locked=False, opened=False)
door4 = Door(["fourth door", "door four"], alley, "There's a door marked 'door four'.", long_descr=descr, locked=True, opened=False)
alley.add_exits([
    door1, door2, door3, door4,
    Exit(["north", "square"], square, "You can go north which brings you back to the square."),
])

square.add_exits([Exit(["alley", "south"], alley, "There's an alley to the south.",
                       "It looks like a very small alley, but you can walk through it.")])


class GameEnd(Location):
    def notify_player_arrived(self, player, previous_location: Location) -> None:
        # player has entered, and thus the story ends
        player.tell("\n")
        player.tell("\n")
        player.tell("<bright>Congratulations! You've finished the game!</>")
        raise StoryCompleted


game_end = GameEnd("Game End", "It seems like it is game over!")


class EndDoor(Door):
    def unlock(self, actor: Living, item: Item=None) -> None:
        super().unlock(actor, item)
        if not self.locked:
            if isinstance(actor, Player):
                # remember a hint about unlocking this door
                if actor.hints.checkpoint("unlocked_enddoor", "The way to freedom lies before you!"):
                    actor.tell_later("<dim>(You will remember this event.)</>")


end_door = EndDoor(["east", "door"], game_end, "To the east is a door with a sign 'Game Over' on it.", locked=True, opened=False)
end_door.key_code = "999"
lane.add_exits([end_door])


class Computer(Item):
    def init(self) -> None:
        super().init()
        self.aliases = {"keyboard", "screen", "wires"}

    def allow_item_move(self, actor: Living, verb: str="move") -> None:
        raise ActionRefused("You can't %s the computer." % verb)

    @property
    def description(self) -> str:
        return "It seems to be connected to the four doors. " \
               + self.screen_text() \
               + " There's also a small keyboard to type commands. " \
               + " On the side of the screen there's a large sticker with 'say hello' written on it."

    @description.setter
    def description(self, value: str) -> None:
        raise TaleError("you cannot set the description of Computer because it is dynamic")

    def screen_text(self) -> str:
        txt = ["The screen of the computer reads:  \""]
        for door in (door1, door2, door3, door4):
            txt.append(door.name.upper())
            txt.append(": LOCKED. " if door.locked else ": UNLOCKED. ")
        txt.append(" AWAITING COMMAND.\"")
        return "".join(txt)

    def read(self, actor: Living) -> None:
        actor.tell(self.screen_text())

    def process_typed_command(self, command: str, doorname: str, actor: Living) -> None:
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
                if not isinstance(door, Door):
                    message = "THAT IS NOT THE NAME OF A DOOR"
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

    def notify_action(self, parsed: ParseResult, actor: Living) -> None:
        if parsed.verb in ("hello", "hi"):
            self.process_typed_command("hello", "", actor)
        elif parsed.verb in ("say", "yell"):
            if "hi" in parsed.args or "hello" in parsed.args:
                self.process_typed_command("hello", "", actor)
            else:
                actor.tell("The computer beeps quietly. The screen shows: "
                           "\"I CAN'T HEAR YOU. PLEASE TYPE COMMANDS INSTEAD OF SPEAKING.\"  How odd.")

    def handle_verb(self, parsed: ParseResult, actor: Living) -> bool:
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


computer = Computer("computer", short_descr="A computer is connected to the doors via a couple of wires.")
computer.verbs = {
    # register some custom verbs. You can redefine existing verbs, so be careful.
    "hack": "Attempt to hack an electronic device.",
    "type": "Enter some text.",
    "enter": "Enter some text.",
}
alley.insert(computer, None)


class DoorKey(Key):
    def notify_moved(self, source_container: ContainingType, target_container: ContainingType, actor: Living) -> None:
        # check if a player picked up this key
        player = None
        if isinstance(target_container, Player):
            player = target_container
        elif isinstance(self.contained_in, Player):
            player = self.contained_in
        if player:
            if player.hints.checkpoint("got_doorkey", "You've found something that might open the exit."):
                actor.tell_later("<dim>(You will remember this event.)</>")


doorkey = DoorKey("key", descr="A key with a little label marked 'Game Over'.")
doorkey.key_for(end_door)
alley.insert(doorkey, None)


class MagicGameEnd(Item):
    def __init__(self) -> None:
        super().__init__("magic orb", descr="A magic orb of some sort.")
        self.aliases = {"orb"}

    def notify_moved(self, source_container: ContainingType, target_container: ContainingType, actor: Living) -> None:
        if isinstance(actor, Player):
            actor.tell("You try to pick up the orb, but as soon as you touch it it ends this game!")
            raise StoryCompleted


alley.insert(MagicGameEnd(), None)
