"""
Character builder for multi-user mode.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from typing import Callable, Generator

from . import lang
from . import mud_context
from . import races
from .accounts import MudAccounts
from .base import Stats
from .player import Player, PlayerConnection


class PlayerNaming:
    def __init__(self) -> None:
        self._name = self.title = self.gender = self.description = None  # type: str
        self.money = mud_context.config.player_money
        self.stats = Stats()
        self.wizard = False

    def apply_to(self, player: Player) -> None:
        assert self._name
        assert self.gender
        player.init_gender(self.gender)
        player.init_names(self._name, self.title, self.description, None)
        player.stats = self.stats
        player.money = self.money

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value.lower()


class CharacterBuilder:
    def __init__(self, conn: PlayerConnection, continue_dialog: Callable[[PlayerNaming], None]) -> None:
        self.conn = conn
        self.continue_dialog = continue_dialog

    def build_async(self) -> Generator:
        self.conn.output("Creating a player character.\n")
        naming = PlayerNaming()
        naming.name = yield "input", ("Name?", MudAccounts.accept_name)
        naming.gender = yield "input", ("Gender (m)ale/(f)emale/(n)euter ?", lang.validate_gender)
        naming.gender = naming.gender[0]
        self.conn.player.tell("You can choose one of the following races: " + lang.join(races.playable_races))
        race = yield "input", ("Player race?", valid_playable_race)
        naming.stats = Stats.from_race(race, gender=naming.gender)
        naming.description = "A regular person." if naming.stats.race == "human" else "A weird creature."
        self.continue_dialog(naming)


def valid_playable_race(value: str) -> str:
    value = value.lower() if value else ""
    if value in races.playable_races:
        return value
    raise ValueError("That is not a valid race.")
