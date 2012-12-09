"""
Unit tests for text output and formatting

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
from tale.player import TextBuffer
import unittest


class TestTextoutput(unittest.TestCase):
    def test_empty_lines(self):
        output = TextBuffer()
        output.print("")
        output.print("")
        self.assertEqual([], output.get_paragraphs(), "empty strings shouldn't be stored")
        output.print("", format=False)
        output.print("", format=False)
        self.assertEqual([("\n\n", False)], output.get_paragraphs(), "2 empty strings without format should be stored in 1 paragraph with 2 new lines")
        output.print("", end=True)
        output.print("", end=True)
        self.assertEqual([("\n", True), ("\n", True)], output.get_paragraphs(), "2 empty strings with end=true should be stored in 2 paragraphs")
        output.print("", end=True)
        output.print("", end=True)
        output.print("", end=True)
        self.assertEqual([("\n", True), ("\n", True), ("\n", True)], output.get_paragraphs())
        output.print("")
        output.print("1")
        output.print("2")
        output.print("")
        self.assertEqual([("1\n2\n", True)], output.get_paragraphs())

    def test_end(self):
        output = TextBuffer()
        output.print("1", end=True)
        output.print("2", end=True)
        self.assertEqual([("1\n", True), ("2\n", True)], output.get_paragraphs())
        output.print("one")
        output.print("1", end=True)
        output.print("two")
        output.print("2", end=True)
        output.print("three")
        self.assertEqual([("one\n1\n", True), ("two\n2\n", True), ("three\n", True)], output.get_paragraphs())

    def test_whitespace(self):
        output = TextBuffer()
        output.print("1")
        output.print("2")
        output.print("3")
        self.assertEqual([("1\n2\n3\n", True)], output.get_paragraphs())

    def test_strip(self):
        output = TextBuffer()
        output.print("   1   ", format=True)
        self.assertEqual([("1\n", True)], output.get_paragraphs())
        output.print("   1   ", format=False)
        self.assertEqual([("   1   \n", False)], output.get_paragraphs())

    def test_text(self):
        self.fail("textwrapping is going to be implemented somewhere else.. fix this testcase then")  # @todo fix testcase
        wrapper = textwrap.TextWrapper(width=45, initial_indent="@@", subsequent_indent="@@")
        output = TextBuffer(wrapper)
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
        expected = """@@one two three four five six seven eight
@@nine ten eleven twelve thirteen fourteen
@@fifteen sixteen seventeen eighteen nineteen
@@twenty.
@@new paragraph. Yeah.

@@new paragraph after empty line.

@@|   x    x   |
@@|    y    y  |
@@|     z    z |
"""
        self.assertEqual(expected, output.get_paragraphs())


if __name__ == '__main__':
    unittest.main()
