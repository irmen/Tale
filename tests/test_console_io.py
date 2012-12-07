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
        self.assertTrue(console_io.supports_delayed_output)
        def print(*lines):
            pass
        console_io.print = print
        console_io.break_pressed(None)
        console_io.output("line1", "line2")
        del console_io.print
    def test_async(self):
        a = console_io.AsyncInput(None)
        a.disable()
        a.enable()
        a.stop()


if __name__ == '__main__':
    unittest.main()
