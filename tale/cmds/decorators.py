# coding=utf-8
"""
Decorator functions to help with defining commands.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import inspect
import functools
from .. import util
from .. import errors


def cmd(func):
    """
    Public decorator to define a normal command function.
    It checks the signature.
    Can be used by the user that is writing story code.
    """
    # NOTE: this code is VERY similar to the internal @cmd decorator in cmds/normal.py
    # If changes are made, make sure to update both occurrences
    if inspect.isgeneratorfunction(func):
        func.is_generator = True   # contains async yields
    argspec = inspect.getargspec(func)
    if argspec.args == ["player", "parsed", "ctx"] and argspec.varargs is None and argspec.keywords is None and argspec.defaults is None:
        func.__doc__ = util.format_docstring(func.__doc__)
        func.is_tale_command_func = True
        if not hasattr(func, "enable_notify_action"):
            func.enable_notify_action = True   # by default the normal commands should be passed to notify_action
        return func
    else:
        raise SyntaxError("invalid cmd function signature for: " + func.__name__)


def wizcmd(func):
    """
    Public decorator to define a wizard command function.
    It adds a privilege check wrapper and checks the signature.
    Can be used by the user that is writing story code.
    """
    func.enable_notify_action = False   # none of the wizard commands should be used with notify_action
    func.is_tale_command_func = True

    # NOTE: this code is VERY similar to the internal @wizcmd decorator in cmds/wizard.py
    # If changes are made, make sure to update both occurrences
    @functools.wraps(func)
    def executewizcommand(player, parsed, ctx):
        if "wizard" not in player.privileges:
            raise errors.SecurityViolation("Wizard privilege required for verb " + parsed.verb)
        return func(player, parsed, ctx)

    if inspect.isgeneratorfunction(func):
        func.is_generator = True   # contains async yields
    argspec = inspect.getargspec(func)
    if argspec.args == ["player", "parsed", "ctx"] and argspec.varargs is None and argspec.keywords is None and argspec.defaults is None:
        func.__doc__ = util.format_docstring(func.__doc__)
        return executewizcommand
    else:
        raise SyntaxError("invalid wizcmd function signature for: " + func.__name__)


def disable_notify_action(func):
    """decorator to prevent the command being passed to notify_action events"""
    func.enable_notify_action = False
    return func


def disabled_in_gamemode(mode):
    """decorator to disable a command in the given game mode"""
    def disable(func):
        func.disabled_in_mode = mode
        return func
    return disable


def overrides_soul(func):
    """decorator to let the command override (hide) the corresponding soul command"""
    func.overrides_soul = True
    return func


def no_soul_parse(func):
    """decorator to tell the command processor to skip the soul parse step and just treat the whole input as plain string"""
    func.no_soul_parse = True
    return func
