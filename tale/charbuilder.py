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
        self._name = self.title = self.gender = self.race = self.description = None
        self.money = 0.0

    def apply_to(self, player):
        player.init_race(self.race, self.gender)
        player.init_names(self._name, self.title, self.description, None)
        player.money = self.money
        player.privileges.discard("wizard")
        if self.wizard:
            player.privileges.add("wizard")

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value.lower()


class CharacterBuilder(object):
    def __init__(self, conn, continue_dialog=None):
        self.conn = conn
        self.continue_dialog = continue_dialog

    def build_async(self):
        while True:
            choice = yield "input", "Create default (<bright>w</>)izard, default (<bright>p</>)layer, (<bright>c</>)ustom player?"
            if choice == "w":
                naming = self.create_default_wizard()
                if self.continue_dialog:
                    return self.continue_dialog(naming)
                return naming
            elif choice == "p":
                naming = self.create_default_player()
                if self.continue_dialog:
                    return self.continue_dialog(naming)
                return naming
            elif choice == "c":
                naming = PlayerNaming()
                while True:
                    name = yield "input", "Name?"
                    message = CharacterBuilder.validate_name(name)
                    if not message:
                        naming.name = name
                        break
                    self.conn.output(message)
                while True:
                    naming.gender = yield "input", "Gender (m)ale/(f)emale/(n)euter ?"
                    if naming.gender in ('m', 'f', 'n'):
                        break
                    self.conn.output("That is not a valid answer.")
                self.conn.player.tell("You can choose one of the following races: ", lang.join(races.player_races))
                while True:
                    naming.race = yield "input", "Player race?"
                    if naming.race in races.player_races:
                        break
                    self.conn.output("That is not a valid answer.")
                while True:
                    answer = yield "input", "Wizard y/n?"
                    try:
                        naming.wizard = lang.yesno(answer)
                        break
                    except ValueError:
                        self.conn.output("That is not a valid answer.")
                naming.description = "A regular person."
                if naming.wizard:
                    naming.title = "arch wizard " + lang.capital(naming.name)
                if self.continue_dialog:
                    return self.continue_dialog(naming)
                return naming
            else:
                self.conn.output("That is not a valid answer.")

    @staticmethod
    def validate_name(name):
        if re.match("[a-zA-Z]{3,}$", name):
            return None
        return "Name needs to be 3 or more letters (a-z, A-Z, no spaces)."

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
