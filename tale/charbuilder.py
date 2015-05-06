# coding=utf-8
"""
Character builder for multi-user mode.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
from . import races
from . import lang
import re


class PlayerNaming(object):
    def __init__(self):
        self.wizard = False
        self.name = self.title = self.gender = self.race = self.description = None
        self.money = 0.0

    def apply_to(self, player):
        player.init_race(self.race, self.gender)
        player.init_names(self.name, self.title, self.description, None)
        player.money = self.money
        player.privileges.discard("wizard")
        if self.wizard:
            player.privileges.add("wizard")


class CharacterBuilder(object):
    def __init__(self, conn):
        self.conn = conn

    def build(self):
        choice = self.conn.input_choice("Create default (<bright>w</>)izard, default (<bright>p</>)layer, (<bright>c</>)ustom player?", ["w", "p", "c"])
        if choice == "w":
            return self.create_default_wizard()
        elif choice == "p":
            return self.create_default_player()
        elif choice == "c":
            return self.create_player_from_info()

    def create_player_from_info(self):
        naming = PlayerNaming()
        while True:
            naming.name = self.conn.input_direct("Name? ")
            if re.match("[a-zA-Z]{3,}$", naming.name):
                break
            else:
                self.conn.output("Name needs to be 3 or more letters (a-z, A-Z, no spaces).")
        naming.gender = self.conn.input_choice("Gender {choices}? ", ["m", "f", "n"])
        self.conn.player.tell("You can choose one of the following races: ", lang.join(races.player_races))
        naming.race = self.conn.input_choice("Player race? ", races.player_races)
        naming.wizard = self.conn.input_confirm("Wizard y/n? ")
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
