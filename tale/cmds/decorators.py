import inspect
import functools
from .. import util
from .. import errors


def cmd(func):
    """
    Decorator to define a normal command function.
    It checks the signature.
    """
    argspec = inspect.getargspec(func)
    if argspec.args == ["player", "parsed"] and argspec.varargs is None and argspec.keywords == "ctx" and argspec.defaults is None:
        func.__doc__ = util.format_docstring(func.__doc__)
        if not hasattr(func, "enable_notify_action"):
            func.enable_notify_action = True   # by default the normal commands should be passed to notify_action
        return func
    else:
        raise SyntaxError("invalid cmd function signature for: " + func.__name__)


def wizcmd(func):
    """
    Decorator to define a wizard command function.
    It adds a privilege check wrapper and checks the signature.
    """
    func.enable_notify_action = False   # none of the wizard commands should be used with notify_action

    @functools.wraps(func)
    def executewizcommand(player, parsed, **ctx):
        if not "wizard" in player.privileges:
            raise errors.SecurityViolation("Wizard privilege required for verb " + parsed.verb)
        return func(player, parsed, **ctx)

    argspec = inspect.getargspec(func)
    if argspec.args == ["player", "parsed"] and argspec.varargs is None and argspec.keywords == "ctx" and argspec.defaults is None:
        func.__doc__ = util.format_docstring(func.__doc__)
        return func
    else:
        raise SyntaxError("invalid wizcmd function signature for: " + func.__name__)


def disable_notify_action(func):
    """decorator to prevent the command being passed to notify_action events"""
    func.enable_notify_action = False
    return func


def disable_in_IF(func):
    """decorator to remove the command in Interactive Fiction mode"""
    func.disabled_for_IF = True
    return func
