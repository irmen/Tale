"""
Unit tests for demo story

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import unittest
from tale import driver
from tale import soul
import tale
import os
import imp
import sys


class TestStory(object):
    def setUp(self):
        self.olddir = os.getcwd()
        os.chdir(self.directory)
        imp.reload(soul)
        sys.path.insert(0, '.')

    def tearDown(self):
        os.chdir(self.olddir)
        del sys.path[0]
        del sys.modules["story"]

    def test_load_config(self):
        story = __import__("story", level=0)
        s = story.Story()
        self.assertEqual(19, len(s.config))

    def test_story(self):
        d = driver.Driver()
        d.start(["-v", "-g", "."])


class TestBuiltinDemoStory(TestStory, unittest.TestCase):
    directory = os.path.join(os.path.dirname(tale.__file__), "demo")


class TestZedStory(TestStory, unittest.TestCase):
    directory = "../stories/zed_is_me"


class TestDemoStory(TestStory, unittest.TestCase):
    directory = "../stories/demo"


if __name__ == '__main__':
    unittest.main()
