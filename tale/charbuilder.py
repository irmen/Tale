# coding=utf-8
"""
Character builder for multi-user mode.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
from . import races
from . import lang
from . import util


class PlayerNaming(object):
    def __init__(self):
        self.wizard = False
        self.name = self.title = self.gender = self.race = self.description = None
        self.money = 0.0

    def apply_to(self, player):
        player.init_race(self.race, self.gender)
        player.init_names(self.name, self.title, self.description, None)
        player.money = self.money
        if self.wizard:
            player.privileges.add("wizard")
        else:
            player.privileges.discard("wizard")


class CharacterBuilder(object):
    def __init__(self, player):
        self.player = player

    def build(self):
        choice = util.input_choice("Create default (<bright>w</>)izard, default (<bright>p</>)layer, (<bright>c</>)ustom player?", ["w", "p", "c"], self.player)
        if choice == "w":
            return self.create_default_wizard()
        elif choice == "p":
            return self.create_default_player()
        elif choice == "c":
            return self.create_player_from_info()

    def create_player_from_info(self):
        naming = PlayerNaming()
        while True:
            naming.name = self.player.input("Name? ")
            if naming.name:
                break
        naming.gender = util.input_choice("Gender {choices}? ", ["m", "f", "n"], self.player)
        self.player.tell("Player races: " + ", ".join(races.player_races))
        naming.race = util.input_choice("Race? ", races.player_races, self.player)
        naming.wizard = util.input_confirm("Wizard y/n? ", self.player)
        naming.description = "A regular person."
        if naming.wizard:
            naming.title = "arch wizard " + lang.capital(naming.name)
        return naming

    def create_default_wizard(self):
        # @todo these hardcoded player profiles eventually need to go
        naming = PlayerNaming()
        naming.name = "rinzwind"
        naming.wizard = True
        naming.description = "This wizard looks very important."
        naming.gender = "m"
        naming.race = "human"
        naming.title = "arch wizard " + lang.capital(naming.name)
        naming.money = 40.35
        return naming

    def create_default_player(self):
        # @todo these hardcoded player profiles eventually need to go
        naming = PlayerNaming()
        naming.name = "joe"
        naming.wizard = False
        naming.description = "A regular person."
        naming.gender = "m"
        naming.race = "human"
        naming.money = 0.0
        return naming
