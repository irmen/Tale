import baseobjects
import soul


class Player(baseobjects.Living):
    """
    Player controlled entity.
    Has a Soul for social interaction.
    """
    def __init__(self, name, gender, race="human", description=None):
        super(Player, self).__init__(name, gender, description, race)
        self.display_name = name.capitalize()
        self.soul = soul.Soul()

    def socialize(self, commandstring):
        return self.soul.process_verb(self, commandstring)

    def socialize_parsed(self, verb, who=None, adverb=None, message="", bodypart=None, qualifier=None):
        return self.soul.process_verb_parsed(self, verb, who, adverb, message, bodypart, qualifier)
