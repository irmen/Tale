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
from tale.story import Storybase
from tests.supportstuff import TestDriver


class StoryCaseBase(object):
    def setUp(self):
        self.verbs = tale.soul.VERBS.copy()
        sys.path.insert(0, self.directory)
        mud_context.driver = TestDriver()
        mud_context.config = Storybase()._get_config()

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
        self.assertEqual("Zed is me", s.name)

    def test_zones(self):
        import zones.houses
        self.assertEqual("Living room", zones.houses.livingroom.name)
        import zones.magnolia_st
        self.assertEqual("Pharmacy", zones.magnolia_st.pharmacy.name)
        import zones.rose_st
        self.assertEqual("Butcher shop", zones.rose_st.butcher.name)


class TestDemoStory(StoryCaseBase, unittest.TestCase):
    directory = os.path.abspath(os.path.join(os.path.dirname(tale.__file__), "../stories/demo"))

    def test_story(self):
        import story
        s = story.Story()
        self.assertEqual("Tale Demo", s.name)

    def test_zones(self):
        import zones.town
        import zones.wizardtower
        self.assertEqual("Alley of doors", zones.town.alley.name)
        self.assertEqual("Tower kitchen", zones.wizardtower.kitchen.name)


class TestBuiltinDemoStory(StoryCaseBase, unittest.TestCase):
    directory = "demo-story-dummy-path"

    def test_story(self):
        import tale.demo.story
        s = tale.demo.story.Story()
        self.assertEqual("Tale demo story", s.name)
        config = s._get_config()
        self.assertEqual(config.author_address, s.author_address)

    def test_zones(self):
        import tale.demo.zones.house
        self.assertEqual("garfield", tale.demo.zones.house.cat.name)


if __name__ == '__main__':
    unittest.main()
