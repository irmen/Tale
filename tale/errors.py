"""
Exception classes

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""


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
