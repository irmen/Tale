"""
Decorator functions to help with defining commands.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import inspect
import functools
from typing import Callable, Generator
from .. import util
from .. import errors
from .. import player
from ..parseresult import ParseResult
from ..story import GameMode


def cmd(func):
    """
    Public decorator to define a normal command function.
    It checks the signature.
    Can be used by the user that is writing story code.
    """
    # NOTE: this code is VERY similar to the internal @cmd decorator in cmds/normal.py
    # If changes are made, make sure to update both occurrences
    func.is_generator = inspect.isgeneratorfunction(func)   # contains async yields?
    if cmdfunc_signature_valid(func):
        func.__doc__ = util.format_docstring(func.__doc__)
        func.is_tale_command_func = True
        if not hasattr(func, "enable_notify_action"):
            func.enable_notify_action = True   # by default the normal commands should be passed to notify_action
        return func
    else:
        raise SyntaxError("invalid cmd function signature: " + func.__name__)


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
    def executewizcommand(player: player.Player, parsed: ParseResult, ctx: util.Context) \
            -> Callable[[player.Player, ParseResult, util.Context], None]:
        if "wizard" not in player.privileges:
            raise errors.SecurityViolation("Wizard privilege required for verb " + parsed.verb)
        return func(player, parsed, ctx)

    func.is_generator = inspect.isgeneratorfunction(func)   # contains async yields?
    if cmdfunc_signature_valid(func):
        func.__doc__ = util.format_docstring(func.__doc__)
        return executewizcommand
    else:
        raise SyntaxError("invalid wizcmd function signature: " + func.__name__)


def cmdfunc_signature_valid(func: Callable) -> bool:
    # the signature of a command function must be exactly this:  def func(player, parsed, ctx) -> None
    sig = inspect.signature(func)
    is_generator = inspect.isgeneratorfunction(func)
    if is_generator and sig.return_annotation is not Generator:
        return False
    elif not is_generator and sig.return_annotation not in [sig.empty, None]:
        return False
    expected_params = ["player", "parsed", "ctx"]
    if list(sig.parameters) != expected_params:
        print("params err")
        return False
    return all(sig.parameters[p].default is sig.empty and
               sig.parameters[p].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for p in expected_params)


def disable_notify_action(func: Callable) -> Callable:
    """decorator to prevent the command being passed to notify_action events"""
    func.enable_notify_action = False   # type: ignore
    return func


def disabled_in_gamemode(mode: GameMode) -> Callable:
    """decorator to disable a command in the given game mode"""
    def disable(func: Callable) -> Callable:
        func.disabled_in_mode = mode   # type: ignore
        return func
    assert isinstance(mode, GameMode)
    return disable


def overrides_soul(func: Callable) -> Callable:
    """decorator to let the command override (hide) the corresponding soul command"""
    func.overrides_soul = True   # type: ignore
    return func


def no_soul_parse(func: Callable) -> Callable:
    """decorator to tell the command processor to skip the soul parse step and just treat the whole input as plain string"""
    func.no_soul_parse = True   # type: ignore
    return func
