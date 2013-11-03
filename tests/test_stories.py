"""
Unit tests for demo story

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import unittest
from tale import driver
from tale.util import ReadonlyAttributes
import tale
import os
import sys


class TestStory(object):
    def setUp(self):
        sys.path.insert(0, self.directory)
        self.verbs = tale.soul.VERBS.copy()

    def tearDown(self):
        del sys.path[0]
        if "story" in sys.modules:
            del sys.modules["story"]
        tale.soul.VERBS = self.verbs

    def test_story(self):
        story = __import__("story", level=0)
        s = story.Story()
        self.assertEqual(19, len(s.config))
        d = driver.Driver()
        args = ReadonlyAttributes(delay=1, verify=True, mode="if", gui=None, game=None)
        d._start(args, story)
        self.assertTrue(d.verified_ok)


class TestBuiltinDemoStory(TestStory, unittest.TestCase):
    directory = os.path.abspath(os.path.join(os.path.dirname(tale.__file__), "demo"))


class TestZedStory(TestStory, unittest.TestCase):
    directory = os.path.abspath(os.path.join(os.path.dirname(tale.__file__), "../stories/zed_is_me"))


class TestDemoStory(TestStory, unittest.TestCase):
    directory = os.path.abspath(os.path.join(os.path.dirname(tale.__file__), "../stories/demo"))


if __name__ == '__main__':
    unittest.main()
