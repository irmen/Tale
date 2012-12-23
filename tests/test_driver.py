"""
Unittests for the driver

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import unittest
import heapq
import datetime
import tale.driver as the_driver
import tale.globalcontext
import tale.cmds.normal
import tale.cmds.wizard
import tale.base
import tale.util


class TestDriver(unittest.TestCase):
    def testAttributes(self):
        d = the_driver.Driver()
        self.assertEqual({}, d.state)
        self.assertEqual({}, tale.globalcontext.mud_context.state)
        self.assertTrue(tale.globalcontext.mud_context.state is d.state)
        self.assertEqual(d, tale.globalcontext.mud_context.driver)


class TestDeferreds(unittest.TestCase):
    def testSortable(self):
        d1 = the_driver.Deferred(5, "owner", "callable", None, None)
        d2 = the_driver.Deferred(2, "owner", "callable", None, None)
        d3 = the_driver.Deferred(4, "owner", "callable", None, None)
        d4 = the_driver.Deferred(1, "owner", "callable", None, None)
        d5 = the_driver.Deferred(3, "owner", "callable", None, None)
        deferreds = sorted([d1, d2, d3, d4, d5])
        dues = [d.due for d in deferreds]
        self.assertEqual([1, 2, 3, 4, 5], dues)

    def test_numeric_deferreds(self):
        thing = tale.base.Item("thing")
        driver = the_driver.Driver()
        now = datetime.datetime.now()
        driver.game_clock = tale.util.GameDateTime(now, 1)
        with self.assertRaises(ValueError):
            driver.defer(3601, thing, "unexisting_method")
        with self.assertRaises(ValueError):
            driver.defer("blerp", thing, "move")
        driver.defer(3601, thing, "move")
        deferred = driver.deferreds[0]
        after = deferred.due - now
        self.assertEqual(3601, after.seconds)

    def test_datetime_deferreds(self):
        thing = tale.base.Item("thing")
        driver = the_driver.Driver()
        now = datetime.datetime.now()
        driver.game_clock = tale.util.GameDateTime(now, 1)
        due = driver.game_clock.plus_realtime(datetime.timedelta(seconds=3601))
        driver.defer(due, thing, "move")
        deferred = driver.deferreds[0]
        after = deferred.due - now
        self.assertEqual(3601, after.seconds)

    def testHeapq(self):
        d1 = the_driver.Deferred(5, "owner", "callable", None, None)
        d2 = the_driver.Deferred(2, "owner", "callable", None, None)
        d3 = the_driver.Deferred(4, "owner", "callable", None, None)
        d4 = the_driver.Deferred(1, "owner", "callable", None, None)
        d5 = the_driver.Deferred(3, "owner", "callable", None, None)
        heap = [d1, d2, d3, d4, d5]
        heapq.heapify(heap)
        dues = []
        while heap:
            dues.append(heapq.heappop(heap).due)
        self.assertEqual([1, 2, 3, 4, 5], dues)

    def testCallable(self):
        class Thing(object):
            def __init__(self):
                self.x = []
            def append(self, value, driver):
                assert driver is the_driver
                self.x.append(value)
        t = Thing()
        d = the_driver.Deferred(1, t, "append", [42], None)
        d(driver=the_driver)
        self.assertEqual([42], t.x)
        t = Thing()
        d = the_driver.Deferred(1, None, t.append, [42], None)
        d(driver=the_driver)
        self.assertEqual([42], t.x)


class TestVarious(unittest.TestCase):
    def testCommandsLoaded(self):
        self.assertGreater(len(tale.cmds.normal.all_commands), 1)
        self.assertGreater(len(tale.cmds.wizard.all_commands), 1)

    def testEnableNotifyActionSet(self):
        for cmd in tale.cmds.normal.all_commands.values():
            self.assertIsNotNone(cmd.__doc__)
            self.assertTrue(cmd.enable_notify_action in (True, False))
        for cmd in tale.cmds.wizard.all_commands.values():
            self.assertIsNotNone(cmd.__doc__)
            self.assertFalse(cmd.enable_notify_action, "all wizard commands must have enable_notify_action set to False")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
