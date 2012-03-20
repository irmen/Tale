"""
Non-Player-Character classes

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division
from . import baseobjects
from . import languagetools
from .errors import ActionRefused


class NPC(baseobjects.Living):
    """
    Non-Player-Character: computer controlled entity.
    These are neutral or friendly, aggressive NPCs should be Monsters.
    """
    def __init__(self, name, gender, title=None, description=None, race="human"):
        super(NPC, self).__init__(name, gender, title, description, race)

    def allow_give(self, item, actor):
        """NPC have a bit nicer refusal message when giving items to them."""
        assert item
        raise ActionRefused("%s doesn't want %s." % (languagetools.capital(self.title), item.title))


class Monster(NPC):
    """
    Special kind of NPC: a monster can be hostile and attack other Livings.
    Usually has Weapons, Armour, and attack actions.
    """
    def __init__(self, name, gender, race, title=None, description=None):
        super(Monster, self).__init__(name, gender, title, description, race)
        self.aggressive = True

    def start_attack(self, victim):
        """
        Starts attacking the given living until death ensues on either side
        """
        name = languagetools.capital(self.title)
        room_msg = "%s starts attacking %s!" % (name, victim.title)
        victim_msg = "%s starts attacking you!" % name
        attacker_msg = "You start attacking %s!" % victim.title
        victim.tell(victim_msg)
        victim.location.tell(room_msg, exclude_living=victim, specific_targets=[self], specific_target_msg=attacker_msg)
