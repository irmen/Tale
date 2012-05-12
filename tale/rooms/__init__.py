"""
Package containing the rooms of the mud.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""


STARTLOCATION_PLAYER = None
STARTLOCATION_WIZARD = None


def init(driver):
    from . import town
    from . import wizardtower
    global STARTLOCATION_PLAYER
    global STARTLOCATION_WIZARD
    STARTLOCATION_PLAYER = town.square
    STARTLOCATION_WIZARD = wizardtower.hall
