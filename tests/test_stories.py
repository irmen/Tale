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
from tale import mud_context
from tale.driver import StoryConfig
from tests.supportstuff import DummyDriver


class StoryCaseBase(object):
    def setUp(self):
        self.verbs = tale.soul.VERBS.copy()
        sys.path.insert(0, self.directory)
        mud_context.driver = DummyDriver()
        mud_context.config = StoryConfig()

    def tearDown(self):
        # this is a bit of a hack, to "clean up" after a story test.
        # it more or less gets the job done to be able to load the next story.
        del sys.path[0]
        tale.soul.VERBS = self.verbs
        for m in list(sys.modules.keys()):
            if m.startswith("zones") or m == "story":
                del sys.modules[m]


class TestZedStory(StoryCaseBase, unittest.TestCase):
    directory = os.path.abspath(os.path.join(os.path.dirname(tale.__file__), "../stories/zed_is_me"))
    def test_story(self):
        import story
        s = story.Story()
        self.assertEqual("Zed is me", s.config.name)
        self.assertEqual(19, len(vars(s.config)))
    def test_zones(self):
        import zones.house
        self.assertEqual("Living room", zones.house.livingroom.name)


class TestDemoStory(StoryCaseBase, unittest.TestCase):
    directory = os.path.abspath(os.path.join(os.path.dirname(tale.__file__), "../stories/demo"))
    def test_story(self):
        import story
        s = story.Story()
        self.assertEqual(19, len(vars(s.config)))
        self.assertEqual("Tale Demo", s.config.name)
    def test_zones(self):
        import zones.town
        import zones.wizardtower
        self.assertEqual("Alley of doors", zones.town.alley.name)
        self.assertEqual("Tower kitchen", zones.wizardtower.kitchen.name)


class TestBuiltinDemoStory(StoryCaseBase, unittest.TestCase):
    directory = "."
    def test_story(self):
        import tale.demo.story
        s = tale.demo.story.Story()
        self.assertEqual(19, len(vars(s.config)))
        self.assertEqual("Tale demo story", s.config.name)
        config = StoryConfig.copy_from(s.config)
        self.assertEqual(config.author_address, s.config.author_address)
    def test_zones(self):
        import tale.demo.zones.house
        self.assertEqual("garfield", tale.demo.zones.house.cat.name)


if __name__ == '__main__':
    unittest.main()
