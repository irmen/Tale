"""
Exception classes

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals


class SecurityViolation(Exception):
    """Some security constraint was violated"""
    pass


class ParseError(Exception):
    """Problem with parsing the user input. Should be shown to the user as a nice error message."""
    pass


class ActionRefused(Exception):
    """The action that was tried was refused by the situation or target object"""
    pass


class SessionExit(Exception):
    """Player session ends."""
    pass


class RetrySoulVerb(Exception):
    """Retry a command as soul verb instead."""
    pass


class RetryParse(Exception):
    """Retry the command as a different one"""
    def __init__(self, command):
        self.command = command


class StoryCompleted(Exception):
    """The story has been completed by the player. (I.F. mode only). (Immediate game end!)"""
    def __init__(self, callback=None):
        self.callback = callback
