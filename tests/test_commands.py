"""
Unit tests for commands definitions and decorators

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import pytest
import inspect
from typing import Generator
import tale.cmds
from tale.cmds import cmdfunc_signature_valid, disable_notify_action, disabled_in_gamemode, overrides_soul, no_soul_parse, cmd, wizcmd
from tale.story import GameMode
from tale.player import Player
from tale.util import Context
from tale.errors import TaleError
from tale.base import ParseResult


class TestCommandDecorators:
    def test_simple_decorators(self):

        @disable_notify_action
        @disabled_in_gamemode(GameMode.IF)
        @overrides_soul
        @no_soul_parse
        def func():
            pass

        assert func.enable_notify_action == False
        assert func.disabled_in_mode == GameMode.IF
        assert func.overrides_soul == True
        assert func.no_soul_parse == True

    def test_signature_checker(self):
        def wrong_func(a, b):
            pass

        def ok_func(player: Player, parsed: ParseResult, ctx: Context) -> None:
            """some docstring"""
            pass

        def ok_func2(player, parsed, ctx):
            """some docstring"""
            pass

        def wrong_func2(player: Player, parsed: ParseResult, ctx: Context) -> None:
            pass  # no docstring, otherwise ok

        def wrong_func3(player, parsed, context):
            pass

        assert cmdfunc_signature_valid(ok_func)
        assert cmdfunc_signature_valid(ok_func2)
        assert not cmdfunc_signature_valid(wrong_func)
        assert not cmdfunc_signature_valid(wrong_func2)
        assert not cmdfunc_signature_valid(wrong_func3)

    def test_decorators_arg_check(self):
        with pytest.raises(TypeError):
            cmd()
        with pytest.raises(TypeError):
            wizcmd()
        with pytest.raises(TypeError):
            cmd(44)
        with pytest.raises(TypeError):
            wizcmd(44)
        with pytest.raises(TypeError):
            cmd("name", "alias1", 42)
        with pytest.raises(TypeError):
            wizcmd("name", "alias1", 42)

    def test_cmd_decorator(self):
        x = cmd("something")
        assert inspect.isfunction(x)
        x = cmd("something", "alias1", "alias2")
        assert inspect.isfunction(x)
        with pytest.raises(TaleError):
            def wrongfunc():
                pass
            cmd("wrongfunc")(wrongfunc)

        def cmdfunc(player: Player, parsed: ParseResult, ctx: Context) -> None:
            """some docstring"""
            pass

        def cmdgenerator(player: Player, parsed: ParseResult, ctx: Context) -> Generator:
            """some docstring"""
            yield 42

        result = cmd("cmdfunc")(cmdfunc)
        assert not result.is_generator
        result = cmd("cmdgenerator")(cmdgenerator)
        assert result.is_generator
        assert "cmdfunc" in tale.cmds._all_commands
        assert "cmdfunc" not in tale.cmds._all_wizard_commands

    def test_wizcmd_decorator(self):
        x = wizcmd("something")
        assert inspect.isfunction(x)
        x = wizcmd("something", "alias1", "alias2")
        assert inspect.isfunction(x)
        with pytest.raises(TaleError):
            def wrongfunc():
                pass
            wizcmd("wrongfunc")(wrongfunc)

        def wizfunc(player: Player, parsed: ParseResult, ctx: Context) -> None:
            """some docstring"""
            pass

        def wizgenerator(player: Player, parsed: ParseResult, ctx: Context) -> Generator:
            """some docstring"""
            yield 42

        result = wizcmd("wizfunc")(wizfunc)
        assert not result.is_generator
        result = wizcmd("wizgenerator")(wizgenerator)
        assert result.is_generator
        assert "!wizfunc" in tale.cmds._all_wizard_commands
        assert "wizfunc" not in tale.cmds._all_wizard_commands
        assert "!wizfunc" not in tale.cmds._all_commands
        assert "wizfunc" not in tale.cmds._all_commands

    def test_no_duplicates(self):
        def testfunc(player: Player, parsed: ParseResult, ctx: Context) -> None:
            """some docstring"""
            pass
        cmd("name1")(testfunc)
        with pytest.raises(ValueError) as x:
            cmd("name1")(testfunc)
        assert str(x.value) == "command defined more than once: name1"
        wizcmd("name1")(testfunc)
        wizcmd("name1")(testfunc)


class TestNormalCommandFunctions():
    # @todo tests for normal command functions
    #     normal.replace_items()
    #     normal.take_stuff()
    #     normal.give_stuff()
    #     normal.print_item_removal()
    #     normal.remove_is_are_args()
    pass


class TestWizardCommandFunctions():
    # @todo tests for wizard command functions
    pass
