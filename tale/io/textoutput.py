"""
Formatted Text output.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import print_function, division, unicode_literals
__all__ = ["TextOutput"]


class Paragraph(object):
    def __init__(self, format=True):
        self.format = format
        self.lines = []

    def add(self, line):
        self.lines.append(line)

    def raw(self):
        return "\n".join(self.lines) + "\n"

    def render(self, textwrapper):
        if not self.lines:
            return "" if self.format else "\n"
        if self.format:
            return textwrapper.fill(" ".join(self.lines)) + "\n"
        else:
            if textwrapper and textwrapper.initial_indent:
                indent = textwrapper.initial_indent
                indented_lines = [indent + line for line in self.lines]
                result = "\n".join(indented_lines)
            else:
                result = "\n".join(self.lines)
            return result + "\n"  # end the last line with a newline


class TextOutput(object):
    def __init__(self, textwrapper):
        self.textwrapper = textwrapper
        self.width = textwrapper.width if textwrapper else 0
        self.init()

    def init(self):
        self.paragraphs = []
        self.in_paragraph = False

    def p(self):
        """Paragraph terminator. Start new paragraph on next line."""
        if not self.in_paragraph:
            self.__new_paragraph(False)
        self.in_paragraph = False

    def __new_paragraph(self, format):
        p = Paragraph(format)
        self.paragraphs.append(p)
        self.in_paragraph = True
        return p

    def print(self, line, end=False, format=True):
        """
        Write a line of text. A single space is inserted between lines, if format=True.
        If end=True, the current paragraph is ended and a new one begins.
        If format=True, the text will be formatted when output, otherwise it is outputted as-is.
        """
        if not line and format and not end:
            return
        if self.in_paragraph:
            p = self.paragraphs[-1]
        else:
            p = self.__new_paragraph(format)
        if p.format != format:
            p = self.__new_paragraph(format)
        if format:
            line = line.strip()
        p.add(line)
        if end:
            self.in_paragraph = False

    def raw(self, clear=True):
        lines = [p.raw() for p in self.paragraphs]
        if clear:
            self.init()
        return lines

    def render(self):
        self.textwrapper.width = self.width  # can be updated in the meantime, so adjust the with.
        formatted_paragraphs = [p.render(self.textwrapper) for p in self.paragraphs]
        self.init()
        return "".join(formatted_paragraphs)
