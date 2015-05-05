"""
Unit tests for console I/O adapter

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import unittest
import sys
import io
from tale.tio import console_io, styleaware_wrapper, iobase
from tale.player import TextBuffer


class TestConsoleIo(unittest.TestCase):
    def setUp(self):
        self._orig_stdout = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self):
        sys.stdout.close()
        sys.stdout = self._orig_stdout

    def test_basic(self):
        io = console_io.ConsoleIo(None)
        io.break_pressed()
        io.output("line1", "line2")

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
        io = console_io.ConsoleIo(None)
        formatted = io.render_output(output.get_paragraphs(), indent=2, width=45)
        self.assertEqual(expected, formatted)

    def testSmartypants(self):
        self.assertEqual("derp&#8230;", iobase.smartypants("derp..."))
        self.assertEqual("&#8216;txt&#8217;", iobase.smartypants("'txt'"))
        self.assertEqual("&#8220;txt&#8221;", iobase.smartypants('"txt"'))
        self.assertEqual(r"slashes\\slashes", iobase.smartypants(r"slashes\\slashes"))


class TextWrapper(unittest.TestCase):
    def test_wrap(self):
        w = styleaware_wrapper.StyleTagsAwareTextWrapper(width=20)
        wrapped = w.fill("This is some text with or without style tags, to see how the wrapping goes.")
        self.assertEqual("This is some text\n"
                         "with or without\n"
                         "style tags, to see\n"
                         "how the wrapping\n"
                         "goes.", wrapped)
        wrapped = w.fill("This is <bright>some text</> with <bright>or without</> style tags, <bright>to</> see <bright>how the</> wrapping <bright>goes.</>")
        wrapped = iobase.strip_text_styles(wrapped)
        self.assertEqual("This is some text\n"
                         "with or without\n"
                         "style tags, to see \n"
                         "how the wrapping \n"
                         "goes.", wrapped)


if __name__ == '__main__':
    unittest.main()
