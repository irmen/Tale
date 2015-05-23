# coding=utf-8
"""
Character builder for multi-user mode.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
from . import races
from . import lang
from . import mud_context
from .base import Stats
from .player import MudAccounts


class PlayerNaming(object):
    def __init__(self):
        self._name = self.title = self.gender = self.description = None
        self.money = mud_context.config.player_money
        self.stats = Stats()

    def apply_to(self, player):
        assert self._name
        assert self.gender
        player.init_gender(self.gender)
        player.init_names(self._name, self.title, self.description, None)
        player.stats = self.stats
        player.money = self.money

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value.lower()


class CharacterBuilder(object):
    def __init__(self, conn, continue_dialog):
        self.conn = conn
        self.continue_dialog = continue_dialog

    def build_async(self):
        self.conn.output("Creating a player character.\n")
        naming = PlayerNaming()
        naming.name = yield "input", ("Name?", MudAccounts.accept_name)
        naming.gender = yield "input", ("Gender (m)ale/(f)emale/(n)euter ?", lang.validate_gender)
        naming.gender = naming.gender[0]
        self.conn.player.tell("You can choose one of the following races: ", lang.join(races.player_races))
        race = yield "input", ("Player race?", validate_race)
        naming.stats = Stats.from_race(race)
        naming.description = "A regular person." if naming.stats.race == "human" else "A weird creature."
        self.continue_dialog(naming)


def validate_race(value):
    value = value.lower() if value else ""
    if value in races.player_races:
        return value
    raise ValueError("That is not a valid race.")
