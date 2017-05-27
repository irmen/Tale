"""
Unit tests for demo story

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import pathlib
import sys
import unittest

import tale
import tale.verbdefs
from tale import mud_context
from tale.story import StoryConfig, StoryBase, StoryConfigError
from tests.supportstuff import FakeDriver


class StoryCaseBase:
    def setUp(self):
        self.verbs = tale.verbdefs.VERBS.copy()
        sys.path.insert(0, str(self.directory))
        mud_context.driver = FakeDriver()
        mud_context.config = StoryConfig()
        mud_context.resources = mud_context.driver.resources

    def tearDown(self):
        # this is a bit of a hack, to "clean up" after a story test.
        # it more or less gets the job done to be able to load the next story.
        del sys.path[0]
        tale.verbdefs.VERBS = self.verbs
        for m in list(sys.modules.keys()):
            if m.startswith("zones") or m == "story":
                del sys.modules[m]


class TestZedStory(StoryCaseBase, unittest.TestCase):
    directory = pathlib.Path("./stories/zed_is_me").resolve()

    def test_story(self):
        import story
        s = story.Story()
        self.assertEqual("Zed is me", s.config.name)

    def test_zones(self):
        import zones.houses
        self.assertEqual("Living room", zones.houses.livingroom.name)
        import zones.magnolia_st
        self.assertEqual("Pharmacy", zones.magnolia_st.pharmacy.name)
        import zones.rose_st
        self.assertEqual("Butcher shop", zones.rose_st.butcher.name)


class TestDemoStory(StoryCaseBase, unittest.TestCase):
    directory = pathlib.Path("./stories/demo").resolve()

    def test_story(self):
        import story
        s = story.Story()
        self.assertEqual("Tale Demo", s.config.name)

    def test_zones(self):
        import zones.town
        import zones.wizardtower
        self.assertEqual("Alley of doors", zones.town.alley.name)
        self.assertEqual("Tower kitchen", zones.wizardtower.kitchen.name)


class TestCircleStory(StoryCaseBase, unittest.TestCase):
    directory = pathlib.Path("./stories/circle").resolve()

    def test_story(self):
        import story
        s = story.Story()
        self.assertEqual("Circle", s.config.name)

    def test_zones_and_vnums(self):
        import zones.midgaard_city
        from zones import make_location, make_item, make_mob, make_shop
        self.assertEqual("The Temple Of Midgaard", zones.midgaard_city.temple.name)
        o = make_mob(5017)
        self.assertEqual("camel", o.name)
        self.assertEqual(5017, o.circle_vnum)
        o = make_location(901)
        self.assertEqual("The Riverbank", o.name)
        self.assertEqual(901, o.circle_vnum)
        o = make_item(3308)
        self.assertEqual("apple", o.name)
        self.assertEqual(3308, o.circle_vnum)
        o = make_shop(5411)
        self.assertEqual("puke", o.action_temper)
        self.assertEqual({"trash", "light", "treasure", "container", "food"}, o.willbuy)
        self.assertEqual(5411, o.circle_vnum)


class TestBuiltinDemoStory(StoryCaseBase, unittest.TestCase):
    directory = pathlib.Path("demo-story-dummy-path")

    def test_story_verify(self):
        s = StoryBase()
        with self.assertRaises(StoryConfigError):
            s._verify(FakeDriver())
        s.config.name = "dummy"
        s._verify(FakeDriver())
        s.config = 1234
        with self.assertRaises(StoryConfigError):
            s._verify(FakeDriver())

    def test_storyconfig(self):
        c1 = StoryConfig()
        c2 = StoryConfig()
        self.assertIsNone(c1.name)
        self.assertEqual(c1, c2)
        c2.name = "dummy"
        self.assertNotEqual(c1, c2)

    def test_story(self):
        import tale.demo.story
        s = tale.demo.story.Story()
        s._verify(FakeDriver())
        self.assertEqual("Tale demo story", s.config.name)

    def test_zones(self):
        import tale.demo.zones.house
        self.assertEqual("garfield", tale.demo.zones.house.cat.name)


if __name__ == '__main__':
    unittest.main()
