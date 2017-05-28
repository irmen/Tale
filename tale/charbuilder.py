"""
Character builder for multi-user mode.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from typing import Generator

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
        self.password = None
        self.email = None

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


class IFCharacterBuilder:
    """Create a new player character interactively."""
    def __init__(self, conn: PlayerConnection) -> None:
        self.conn = conn
        self.naming = PlayerNaming()

    def ask_name(self) -> Generator:
        self.conn.output("Creating a player character.\n")
        self.naming.name = yield "input", ("What shall you be known as?", MudAccounts.accept_name)

    def ask_credentials(self) -> Generator:
        yield from []

    def ask_confirm(self) -> Generator:
        return True
        # noinspection PyUnreachableCode
        yield

    def build_character(self) -> Generator:
        yield from self.ask_name()
        yield from self.ask_credentials()
        self.naming.gender = yield "input", ("What is the gender of your player character (m/f/n)?", lang.validate_gender)
        self.conn.player.tell("You can choose one of the following races: " + lang.join(races.playable_races))
        race = yield "input", ("What should be the race of your player character?", valid_playable_race)
        self.naming.stats = Stats.from_race(race, gender=self.naming.gender)
        self.naming.description = "A regular person." if self.naming.stats.race == "human" else "A weird creature."
        okay = yield from self.ask_confirm()
        return self.naming if okay else None


class MudCharacterBuilder(IFCharacterBuilder):
    """Create a new player character interactively."""
    def __init__(self, conn: PlayerConnection, name: str) -> None:
        super().__init__(conn)
        self.naming.name = name

    def ask_name(self) -> Generator:
        self.conn.output("<ul><bright>New character creation: '%s'.</>\n" % self.naming.name)
        yield from []

    def ask_credentials(self) -> Generator:
        self.naming.password = yield "input-noecho", ("Please type in the desired password.", MudAccounts.accept_password)
        self.naming.email = yield "input", ("Please type in your email address.", MudAccounts.accept_email)

    def ask_confirm(self) -> Generator:
        # review the account
        self.conn.player.tell("<bright>Please review your new character.</>", end=True)
        self.conn.player.tell("<dim> name:</> %s,  <dim>gender:</> %s,  <dim>race:</> %s"
                              % (self.naming.name, lang.GENDERS[self.naming.gender], self.naming.stats.race), end=True)
        self.conn.player.tell("<dim> email:</> " + self.naming.email, end=True)
        okay = yield "input", ("You cannot change your name later. Do you want to create this character?", lang.yesno)
        if okay:
            return True
        self.conn.player.tell("Ok, let's get back to the beginning then.", end=True)
        return False


def valid_playable_race(value: str) -> str:
    value = value.lower() if value else ""
    if value in races.playable_races:
        return value
    raise ValueError("That is not a valid race.")
