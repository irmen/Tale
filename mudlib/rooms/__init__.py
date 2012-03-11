"""
Package containing the rooms of the mud.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from . import town
from . import wizardtower

STARTLOCATION_PLAYER = town.square
STARTLOCATION_WIZARD = wizardtower.hall
