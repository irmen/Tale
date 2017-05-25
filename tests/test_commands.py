"""
Unit tests for commands definitions and decorators

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import pytest
from typing import Generator
from tale.cmds.decorators import *
from tale.cmds.normal import cmd as builtin_cmd
from tale.cmds.wizard import wizcmd as builtin_wizcmd
from tale.story import GameMode
from tale.player import Player
from tale.parseresult import ParseResult
from tale.util import Context
from tale.errors import TaleError


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
            cmd("foo")
        with pytest.raises(TypeError):
            wizcmd("foo")
        with pytest.raises(TypeError):
            builtin_cmd()
        with pytest.raises(TypeError):
            builtin_wizcmd()
        with pytest.raises(TypeError):
            builtin_cmd(44)
        with pytest.raises(TypeError):
            builtin_cmd("name", "alias1", 44)
        with pytest.raises(TypeError):
            builtin_wizcmd(44)
        with pytest.raises(TypeError):
            builtin_wizcmd("name", "alias1", 44)

    def test_cmd_decorator(self):
        with pytest.raises(TaleError):
            def wrongfunc():
                pass
            cmd(wrongfunc)

        def cmdfunc(player: Player, parsed: ParseResult, ctx: Context) -> None:
            """some docstring"""
            pass

        def cmdgenerator(player: Player, parsed: ParseResult, ctx: Context) -> Generator:
            """some docstring"""
            yield 42

        result = cmd(cmdfunc)
        assert not result.is_generator
        result = cmd(cmdgenerator)
        assert result.is_generator

    def test_wizcmd_decorator(self):
        with pytest.raises(TaleError):
            def wrongfunc():
                pass
            wizcmd(wrongfunc)

        def wizfunc(player: Player, parsed: ParseResult, ctx: Context) -> None:
            """some docstring"""
            pass

        def wizgenerator(player: Player, parsed: ParseResult, ctx: Context) -> Generator:
            """some docstring"""
            yield 42

        result = wizcmd(wizfunc)
        assert not result.is_generator
        result = wizcmd(wizgenerator)
        assert result.is_generator
