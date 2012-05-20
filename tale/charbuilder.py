"""
Character builder for multi-user mode.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from . import races
from . import player


class CharacterBuilder(object):
    def __init__(self, driver):
        self.driver = driver

    def build(self):
        while True:
            choice = self.driver.input("Create default (w)izard, default (p)layer, (c)ustom player? ")
            if choice == "w":
                return self.create_default_wizard()
            elif choice == "p":
                return self.create_default_player()
            elif choice == "c":
                return self.create_player_from_info()

    def create_player_from_info(self):
        while True:
            name = self.driver.input("Name? ")
            if name:
                break
        gender = self.driver.input("Gender m/f/n? ")[0]
        while True:
            print("Player races:", ", ".join(races.player_races))
            race = self.driver.input("Race? ")
            if race in races.player_races:
                break
            print("Unknown race, try again.")
        wizard = self.driver.input("Wizard y/n? ") == "y"
        description = "A regular person."
        p = player.Player(name, gender, race, description)
        if wizard:
            p.privileges.add("wizard")
            p.set_title("arch wizard %s", includes_name_param=True)
        return p

    def create_default_wizard(self):
        p = player.Player("irmen", "m", "human", "This wizard looks very important.")
        p.privileges.add("wizard")
        p.set_title("arch wizard %s", includes_name_param=True)
        return p

    def create_default_player(self):
        return player.Player("irmen", "m", "human", "A regular person.")
