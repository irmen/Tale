"""
Unit tests for console I/O adapter

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import unittest
import sys
import os
from tale.io import console_io
from tale.player import TextBuffer


class TestConsoleIo(unittest.TestCase):
    def setUp(self):
        self._orig_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
    def tearDown(self):
        sys.stdout.close()
        sys.stdout = self._orig_stdout

    def test_basic(self):
        io = console_io.ConsoleIo()
        self.assertTrue(io.supports_delayed_output)
        io.break_pressed(None)
        io.output("line1", "line2")
    def test_async(self):
        io = console_io.ConsoleIo()
        a = io.get_async_input(None)
        a.disable()
        a.enable()
        a.stop()

    def test_text(self):
        output = TextBuffer()
        output.print("one two three four five six seven")
        output.print("eight nine ten eleven twelve thirteen fourteen fifteen")
        output.print("sixteen seventeen eighteen nineteen twenty.")
        output.p()
        output.print("new paragraph.")
        output.print("Yeah.", end=True)
        output.p()
        output.print("new paragraph after empty line.")
        output.p()
        output.p()
        output.print("|   x    x   |", format=False)
        output.print("|    y    y  |", format=False)
        output.print("|     z    z |", format=False)
        expected = """  one two three four five six seven eight
  nine ten eleven twelve thirteen fourteen
  fifteen sixteen seventeen eighteen nineteen
  twenty.
  new paragraph.  Yeah.
\x20\x20
  new paragraph after empty line.
\x20\x20
  |   x    x   |
  |    y    y  |
  |     z    z |
"""
        io = console_io.ConsoleIo()
        formatted = io.render_output(output.get_paragraphs(), indent=2, width=45)
        self.assertEqual(expected, formatted)


if __name__ == '__main__':
    unittest.main()
