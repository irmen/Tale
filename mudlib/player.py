from . import baseobjects, soul
from . import languagetools as lang

class Player(baseobjects.Living):
    """
    Player controlled entity.
    Has a Soul for social interaction.
    """
    def __init__(self, name, gender, race="human", description=None):
        title = lang.capital(name)
        super(Player, self).__init__(name, gender, title, description, race)
        self.soul = soul.Soul()
        self.privileges = set()
        self.__output = []

    def set_title(self, title, includes_name_param=False):
        if includes_name_param:
            self.title = title % lang.capital(self.name)
        else:
            self.title = title

    def socialize(self, commandstring):
        return self.soul.process_verb(self, commandstring)

    def socialize_parsed(self, verb, who=None, adverb=None, message="", bodypart=None, qualifier=None):
        return self.soul.process_verb_parsed(self, verb, who, adverb, message, bodypart, qualifier)

    def tell(self, *msg):
        """
        A message send to a player, this is meant to be printed on the screen.
        For efficiency, messages are gathered in a buffer and printed later.
        """
        self.__output.extend(msg)

    def get_output_lines(self):
        """gets the accumulated output lines and clears the buffer"""
        lines = self.__output
        self.__output = []
        return lines
