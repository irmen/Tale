

class Player(object):
    def __init__(self, name):
        self.name = name

    def interact(self):
        yield "Hallo dit is "+self.name
