import baseobjects


class NPC(baseobjects.Living):
    """
    Non-Player-Character: computer controlled entity.
    These are neutral or friendly, aggressive NPCs should be Monsters.
    """
    def __init__(self, name, gender, description=None):
        super(NPC, self).__init__(name, gender, description)


class Monster(NPC):
    """
    Special kind of NPC: a monster can be hostile and attack other Livings.
    Usually has Weapons, Armour, and attack actions.
    """
    def __init__(self, name, gender, description=None):
        super(Monster, self).__init__(name, gender, description)
