"""
Unit tests for console I/O adapter

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import unittest
from tale.io import console_io


class TestConsoleIo(unittest.TestCase):
    def test_basic(self):
        io = console_io.ConsoleIo()
        self.assertTrue(io.supports_delayed_output)
        def print(*lines):
            pass
        io.print = print
        io.break_pressed(None)
        io.output("line1", "line2")
        del io.print
    def test_async(self):
        io = console_io.ConsoleIo()
        a = io.get_async_input(None)
        a.disable()
        a.enable()
        a.stop()


if __name__ == '__main__':
    unittest.main()
