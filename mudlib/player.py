import baseobjects
import soul


class Player(baseobjects.Living):
    """
    Player controlled entity.
    Has a Soul for social interaction.
    """
    def __init__(self, name, gender, description=None):
        super(Player, self).__init__(name, gender, description)
        self.soul = soul.Soul()

    def socialize(self, commandstring):
        return self.soul.process_verb(self, commandstring)

    def socialize_parsed(self, verb, who=None, adverbs=None, message="", bodyparts=None):
        return self.soul.process_verb_parsed(self, verb, who, adverbs, message, bodyparts)
