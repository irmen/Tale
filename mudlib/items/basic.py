"""
Basic items.

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from ..baseobjects import Item, Container

trashcan = Container("trashcan", "dented steel trashcan", description="A steel trash can, looking worn. The lid is closed, probably for the better.")
newspaper = Item("newspaper", description="Reading the date, you see it is last week's newspaper. It smells funky too.")
rock = Item("rock", "large rock", "A pretty large rock. It looks extremely heavy.")
gem = Item("gem", "sparkling gem", "Light sparkles from this beautiful red gem.")
pouch = Container("pouch", "small leather pouch", "It is closed with a leather strap.")
