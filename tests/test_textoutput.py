"""
Unit tests for text output and formatting

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import unittest
import textwrap
from tale.io import textoutput


class TestTextoutput(unittest.TestCase):
    def test_paragraph(self):
        wrapper = textwrap.TextWrapper(width=20)
        p = textoutput.Paragraph(True)
        self.assertEqual("", p.render(wrapper), "completely empty paragraph should produce empty string")
        p = textoutput.Paragraph(True)
        p.add("")
        self.assertEqual("\n", p.render(wrapper), "paragraph with empty line should become single newline")
        p = textoutput.Paragraph(True)
        p.add("1")
        self.assertEqual("1\n", p.render(wrapper))
        p.add("2")
        self.assertEqual("1 2\n", p.render(wrapper))
        p.format = False
        self.assertEqual("1\n2\n", p.render(wrapper))

    def test_empty_lines(self):
        wrapper = textwrap.TextWrapper(width=20)
        output = textoutput.TextOutput(wrapper)
        output.print("")
        output.print("")
        self.assertEqual([], output.raw(), "empty strings shouldn't be stored")
        output.print("", format=False)
        output.print("", format=False)
        self.assertEqual(["\n\n"], output.raw(), "2 empty strings without format should be stored in 1 paragraph with 2 new lines")
        output.print("", end=True)
        output.print("", end=True)
        self.assertEqual(["\n", "\n"], output.raw(), "2 empty strings with end=true should be stored in 2 paragraphs")
        output.print("")
        output.print("")
        self.assertEqual("", output.render())
        output.print("", end=True)
        output.print("", end=True)
        output.print("", end=True)
        self.assertEqual("\n\n\n", output.render())
        output.print("")
        output.print("1")
        output.print("2")
        output.print("")
        self.assertEqual(["1\n2\n"], output.raw())
        output.print("")
        output.print("1")
        output.print("2")
        output.print("")
        self.assertEqual("1 2\n", output.render())

    def test_end_raw(self):
        output = textoutput.TextOutput(None)
        output.print("1", end=True)
        output.print("2", end=True)
        self.assertEqual(["1\n", "2\n"], output.raw())
        output.print("one")
        output.print("1", end=True)
        output.print("two")
        output.print("2", end=True)
        output.print("three")
        self.assertEqual(["one\n1\n", "two\n2\n", "three\n"], output.raw())

    def test_whitespace(self):
        wrapper = textwrap.TextWrapper(width=20)
        output = textoutput.TextOutput(wrapper)
        output.print("1")
        output.print("2")
        output.print("3")
        self.assertEqual("1 2 3\n", output.render(), "a space must be inserted between different print statements")

    def test_end(self):
        wrapper = textwrap.TextWrapper(width=20)
        output = textoutput.TextOutput(wrapper)
        output.print("1", end=True)
        output.print("2", end=True)
        self.assertEqual("1\n2\n", output.render())
        output.print("one")
        output.print("1", end=True)
        output.print("two")
        output.print("2", end=True)
        output.print("three")
        self.assertEqual("one 1\ntwo 2\nthree\n", output.render())

    def test_strip(self):
        wrapper = textwrap.TextWrapper(width=20)
        output = textoutput.TextOutput(wrapper)
        output.print("   1   ", format=True)
        self.assertEqual("1\n", output.render())
        output.print("   1   ", format=False)
        self.assertEqual("   1   \n", output.render())

    def test_text(self):
        wrapper = textwrap.TextWrapper(width=45, initial_indent="@@", subsequent_indent="@@")
        output = textoutput.TextOutput(wrapper)
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
        self.assertEqual(expected, output.render())


if __name__ == '__main__':
    unittest.main()
