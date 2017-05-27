"""
The house, where the player starts the game

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import random

from tale.base import Location, Exit, Door, Key, Living
from tale.driver import Driver
from tale.errors import StoryCompleted
from tale.lang import capital
from tale.parseresult import ParseResult
from tale.player import Player
from tale.util import Context, call_periodically


def init(driver: Driver) -> None:
    # called when zone is first loaded
    pass


# define the various locations


class GameEnd(Location):
    def notify_player_arrived(self, player: Player, previous_location: Location) -> None:
        # player has entered, and thus the story ends
        player.tell("\n")
        player.tell("\n")
        player.tell("<bright>Congratulations on escaping the house!</> Someone else has to look after Garfield now though...")
        raise StoryCompleted


livingroom = Location("Living room", "The living room in your home in the outskirts of the city.")
closet = Location("Closet", "A small room.")
outside = GameEnd("Outside", "It is beautiful weather outside.")


# define the exits that connect the locations

door = Door(
    ["garden", "door"], outside,
    "A door leads to the garden.", "There's a heavy door here that leads to the garden outside the house.",
    locked=True, opened=False)
door.key_code = 1
# use an exit with an unbound target (string), the driver will link this up:
closet_exit = Exit("closet", "house.closet", "There's a small closet in your house.")
livingroom.add_exits([door, closet_exit])
# use another exit with a bound target (object):
closet.add_exits([Exit("living room", livingroom, "You can see the living room.")])


# define items and NPCs

class Cat(Living):
    def init(self) -> None:
        self.aliases = {"cat"}

    @call_periodically(5, 20)
    def do_purr(self, ctx: Context) -> None:
        if random.random() > 0.5:
            self.location.tell("%s purrs happily." % capital(self.title))
        else:
            self.location.tell("%s yawns sleepily." % capital(self.title))

    def notify_action(self, parsed: ParseResult, actor: Living) -> None:
        if parsed.verb in ("pet", "stroke", "tickle", "cuddle", "hug"):
            self.tell_others("{Title} curls up in a ball and purrs contently.")
        elif parsed.verb in ("hello", "hi", "greet"):
            self.tell_others("{Title} stares at you incomprehensibly.")
        else:
            message = (parsed.message or parsed.unparsed).lower()
            if self.name in message:
                self.tell_others("{Title} looks up at you.")


cat = Cat("garfield", "m", race="cat", description="A very obese cat, orange and black. It looks tired, but glances at you happily.")
livingroom.insert(cat, None)
key = Key("key", "small rusty key", "This key is small and rusty. It has a label attached, reading \"garden door\".")
key.key_for(door)
closet.insert(key, None)
