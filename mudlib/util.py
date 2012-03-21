"""
Utility stuff

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

# there's nothing her so far

from __future__ import print_function, division
from . import lang


def print_object_location(player, obj, container, print_parentheses=True):
    if not container:
        if print_parentheses:
            player.tell("(it's not clear where %s is)" % obj.name)
        else:
            player.tell("It's not clear where %s is." % obj.name)
        return
    if container in player:
        if print_parentheses:
            player.tell("(%s was found in %s, in your inventory)" % (obj.name, container.title))
        else:
            player.tell("%s was found in %s, in your inventory." % (lang.capital(obj.name), container.title))
    elif container is player.location:
        if print_parentheses:
            player.tell("(%s was found in your current location)" % obj.name)
        else:
            player.tell("%s was found in your current location." % lang.capital(obj.name))
    elif container is player:
        if print_parentheses:
            player.tell("(%s was found in your inventory)" % obj.name)
        else:
            player.tell("%s was found in your inventory." % lang.capital(obj.name))
    else:
        if print_parentheses:
            player.tell("(%s was found in %s)" % (obj.name, container.name))
        else:
            player.tell("%s was found in %s." % (lang.capital(obj.name), container.name))
