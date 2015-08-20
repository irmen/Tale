# coding=utf-8
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


class LocationIntegrityError(Exception):
    """When the driver notices an integrity problem with locations, exits, etc."""
    def __init__(self, msg, direction, exit, location):
        super(LocationIntegrityError, self).__init__(msg)
        self.direction = direction
        self.exit = exit
        self.location = location


class AsyncDialog(Exception):
    """Command execution needs to continue with an async dialog"""
    def __init__(self, dialog, *args):
        self.dialog = dialog
        self.args = args
