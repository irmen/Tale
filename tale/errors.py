"""
Exception classes

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from typing import Generator, Tuple, Any, Optional


class TaleError(Exception):
    """base class for tale related errors"""
    pass


class TaleFlowControlException(Exception):
    """base class for flow-control exceptions"""
    pass


class StoryConfigError(TaleError):
    """There was a problem with the story configuration"""
    pass


class SecurityViolation(TaleError):
    """Some security constraint was violated"""
    pass


class ParseError(TaleError):
    """Problem with parsing the user input. Should be shown to the user as a nice error message."""
    pass


class ActionRefused(TaleFlowControlException):
    """The action that was tried was refused by the situation or target object"""
    pass


class SessionExit(TaleFlowControlException):
    """Player session ends."""
    pass


class RetrySoulVerb(TaleFlowControlException):
    """Retry a command as soul verb instead."""
    pass


class RetryParse(TaleFlowControlException):
    """Retry the command as a different one"""
    def __init__(self, command: str) -> None:
        self.command = command


class LocationIntegrityError(TaleError):
    """When the driver notices an integrity problem with locations, exits, etc."""
    def __init__(self, msg: str, direction: Optional[str], exit: Any, location: Any) -> None:
        super().__init__(msg)
        self.direction = direction
        self.exit = exit
        self.location = location


class AsyncDialog(TaleFlowControlException):
    """Command execution needs to continue with an async dialog"""
    def __init__(self, dialog: Generator[Tuple[str, Any], str, None], *args: Any) -> None:
        self.dialog = dialog
        self.args = args
