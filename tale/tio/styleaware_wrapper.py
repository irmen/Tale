"""
Textwrapper that doesn't count the length of the embedded formatting tags.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import re
import textwrap
from typing import List

tag_split_re = re.compile("(<[a-z/]+?>)")
tag_re = re.compile("<[a-z/]+?>$")


class StyleTagsAwareTextWrapper(textwrap.TextWrapper):
    """
    A TextWrapper subclass that doesn't count the length of Tale's style tags
    when filling up the lines (the style tags don't have visible width).
    Unfortunately the line filling loop is embedded in a larger method,
    that we need to override fully (_wrap_chunks)...
    """
    def _wrap_chunks(self, chunks: List[str]) -> List[str]:
        lines = []  # type: List[str]
        if self.width <= 0:
            raise ValueError("invalid width %r (must be > 0)" % self.width)

        # split any style tags <abcde> or </> into separate chunks
        chunks2 = []
        for chunk in chunks:
            chunks2.extend(tag_split_re.split(chunk))
        chunks = chunks2
        del chunks2

        chunks.reverse()  # for pop()
        while chunks:
            cur_line = []
            cur_len = 0
            if lines:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent
            width = self.width - len(indent)
            if self.drop_whitespace and chunks[-1].strip() == '' and lines:
                del chunks[-1]

            while chunks:
                chunk = chunks[-1]
                if not chunk:
                    chunks.pop()
                    continue
                length = 0 if tag_re.match(chunk) else len(chunk)   # don't count length of any styling tags
                if cur_len + length <= width:
                    cur_line.append(chunks.pop())
                    cur_len += length
                else:
                    break  # line full

            if chunks and len(chunks[-1]) > width:
                self._handle_long_word(chunks, cur_line, cur_len, width)
            if self.drop_whitespace and cur_line and cur_line[-1].strip() == '':
                del cur_line[-1]
            if cur_line:
                lines.append(indent + ''.join(cur_line))

        return lines


if __name__ == "__main__":
    w = StyleTagsAwareTextWrapper(width=20)
    print(w.fill("this is some normal text, without any style tags"))
    print(w.fill("this <bright>is some</> <bright>styled</> text, <bright>with</> some <bright>style</> tags"))
