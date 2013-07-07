"""
Unittests for deque (because Jython's deque needs to be patched
to support the maxlen parameter)

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import unittest

from tale import jythonpatch
from collections import deque


class TestDeque(unittest.TestCase):
    def test_maxlen_add(self):
        d = deque("test", maxlen=5)
        d.append("a")
        d.append("b")
        d.append("c")
        self.assertEqual(5, len(d))
        self.assertEqual(['s', 't', 'a', 'b', 'c'], list(d))
        d.appendleft("x")
        d.appendleft("y")
        d.appendleft("z")
        self.assertEqual(5, len(d))
        self.assertEqual(['z', 'y', 'x', 's', 't'], list(d))

    def test_maxlen_extend(self):
        d = deque("test", maxlen=5)
        d = deque("test", maxlen=5)
        d.extend("abc")
        self.assertEqual(5, len(d))
        self.assertEqual(['s', 't', 'a', 'b', 'c'], list(d))
        d.extendleft("xyz")
        self.assertEqual(5, len(d))
        self.assertEqual(['z', 'y', 'x', 's', 't'], list(d))

    def test_add(self):
        d = deque("test")
        d.append("a")
        d.append("b")
        d.append("c")
        self.assertEqual(7, len(d))
        self.assertEqual(['t', 'e', 's', 't', 'a', 'b', 'c'], list(d))
        d.appendleft("x")
        d.appendleft("y")
        d.appendleft("z")
        self.assertEqual(10, len(d))
        self.assertEqual(['z', 'y', 'x', 't', 'e', 's', 't', 'a', 'b', 'c'], list(d))

    def test_extend(self):
        d = deque("test")
        d = deque("test")
        d.extend("abc")
        self.assertEqual(7, len(d))
        self.assertEqual(['t', 'e', 's', 't', 'a', 'b', 'c'], list(d))
        d.extendleft("xyz")
        self.assertEqual(10, len(d))
        self.assertEqual(['z', 'y', 'x', 't', 'e', 's', 't', 'a', 'b', 'c'], list(d))


if __name__ == '__main__':
    unittest.main()
