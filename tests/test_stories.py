"""
Unit tests for demo story

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import unittest
import os
import sys
import tale
from tale import driver, mud_context
from tale.util import ReadonlyAttributes
from tests.supportstuff import DummyDriver


mud_context.driver = DummyDriver()
import tale.demo.story
import tale.demo.zones.house


class StoryCaseBase(object):
    def setUp(self):
        self.verbs = tale.soul.VERBS.copy()
        self.modules=set(sys.modules.keys())

    def tearDown(self):
        # this is a bit of a hack, to "clean up" after a story test.
        # it more or less gets the job done to be able to load the next story.
        del sys.path[0]
        for module in list(sys.modules.keys()):
            if module.startswith("zones") or module=="story" or module=="cmds":
                del sys.modules[module]
        tale.soul.VERBS = self.verbs

    def test_story(self):
        d = driver.Driver()
        args = ReadonlyAttributes(delay=1, verify=True, mode="if", gui=None, game=self.directory)
        d._start(args)
        self.assertEqual(19, len(d.story.config))
        self.assertTrue(d.verified_ok)


class TestZedStory(StoryCaseBase, unittest.TestCase):
    directory = os.path.abspath(os.path.join(os.path.dirname(tale.__file__), "../stories/zed_is_me"))


class TestDemoStory(StoryCaseBase, unittest.TestCase):
    directory = os.path.abspath(os.path.join(os.path.dirname(tale.__file__), "../stories/demo"))


@unittest.skipIf(sys.version_info>=(3,0), "cannot test builtin story with python 3")
class TestBuiltinDemoStory(StoryCaseBase, unittest.TestCase):
    directory = os.path.abspath(os.path.join(os.path.dirname(tale.__file__), "demo"))


class TestBuiltinDemoStoryBasic(unittest.TestCase):
    def test_basic_story_properties(self):
        s = tale.demo.story.Story()
        self.assertEqual(19, len(s.config))
        self.assertEqual("garfield", tale.demo.zones.house.cat.name)
    


if __name__ == '__main__':
    unittest.main()
