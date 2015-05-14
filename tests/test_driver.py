"""
Unittests for the driver

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import unittest
import heapq
import datetime
import os
import inspect
import pickle
import tale.driver as the_driver
import tale.cmds.normal
import tale.cmds.wizard
import tale.base
import tale.util
import tale.demo
from tale.cmds.decorators import cmd, wizcmd, disabled_in_gamemode
from tests.supportstuff import Thing


def module_level_func(ctx):
    assert ctx is not None


def module_level_func_without_ctx():
    pass


class TestDeferreds(unittest.TestCase):
    def testSortable(self):
        t1 = datetime.datetime(1995, 1, 1)
        t2 = datetime.datetime(1996, 1, 1)
        t3 = datetime.datetime(1997, 1, 1)
        t4 = datetime.datetime(1998, 1, 1)
        t5 = datetime.datetime(1999, 1, 1)
        d1 = the_driver.Deferred(t5, os.getcwd, None, None)
        d2 = the_driver.Deferred(t2, os.getcwd, None, None)
        d3 = the_driver.Deferred(t4, os.getcwd, None, None)
        d4 = the_driver.Deferred(t1, os.getcwd, None, None)
        d5 = the_driver.Deferred(t3, os.getcwd, None, None)
        deferreds = sorted([d1, d2, d3, d4, d5])
        dues = [d.due for d in deferreds]
        self.assertEqual([t1, t2, t3, t4, t5], dues)

    def test_numeric_deferreds(self):
        thing = tale.base.Item("thing")
        driver = the_driver.Driver()
        now = datetime.datetime.now()
        driver.game_clock = tale.util.GameDateTime(now, 1)
        with self.assertRaises(ValueError):
            driver.defer("blerp", thing.move)
        driver.defer(3601, thing.move)
        deferred = driver.deferreds[0]
        after = deferred.due - now
        self.assertEqual(3601, after.seconds)

    def test_datetime_deferreds(self):
        thing = tale.base.Item("thing")
        driver = the_driver.Driver()
        now = datetime.datetime.now()
        driver.game_clock = tale.util.GameDateTime(now, 1)
        due = driver.game_clock.plus_realtime(datetime.timedelta(seconds=3601))
        driver.defer(due, thing.move)
        deferred = driver.deferreds[0]
        after = deferred.due - now
        self.assertEqual(3601, after.seconds)

    def testHeapq(self):
        t1 = datetime.datetime(1995, 1, 1)
        t2 = datetime.datetime(1996, 1, 1)
        t3 = datetime.datetime(1997, 1, 1)
        t4 = datetime.datetime(1998, 1, 1)
        t5 = datetime.datetime(1999, 1, 1)
        d1 = the_driver.Deferred(t5, os.getcwd, None, None)
        d2 = the_driver.Deferred(t2, os.getcwd, None, None)
        d3 = the_driver.Deferred(t4, os.getcwd, None, None)
        d4 = the_driver.Deferred(t1, os.getcwd, None, None)
        d5 = the_driver.Deferred(t3, os.getcwd, None, None)
        heap = [d1, d2, d3, d4, d5]
        heapq.heapify(heap)
        dues = []
        while heap:
            dues.append(heapq.heappop(heap).due)
        self.assertEqual([t1, t2, t3, t4, t5], dues)

    def testCallable(self):
        def scoped_function():
            pass
        t = Thing()
        d = the_driver.Deferred(None, t.append, [42], None)
        ctx = tale.util.Context(driver="driver", clock=None, config=None, player_connection=None)
        d(ctx=ctx)
        self.assertEqual([42], t.x)
        d = the_driver.Deferred(None, module_level_func, [], None)
        d(ctx=ctx)
        d = the_driver.Deferred(None, module_level_func_without_ctx, [], None)
        d(ctx=ctx)
        with self.assertRaises(ValueError):
            the_driver.Deferred(None, scoped_function, [], None)
        with self.assertRaises(ValueError):
            d = the_driver.Deferred(None, lambda a, ctx=None: 1, [42], None)

    def testSerializable(self):
        target = Thing()
        deferreds = [the_driver.Deferred(datetime.datetime.now(), target.append, [1, 2, 3], {"kwarg": 42}),
                     the_driver.Deferred(datetime.datetime.now(), os.getcwd, [], None),
                     the_driver.Deferred(datetime.datetime.now(), module_level_func, [], None)]
        ser = pickle.dumps(deferreds, pickle.HIGHEST_PROTOCOL)
        data = pickle.loads(ser)
        self.assertEqual(deferreds, data)

    def testDue_realtime(self):
        # test due timings where the gameclock == realtime clock
        game_clock = tale.util.GameDateTime(datetime.datetime(2013, 7, 18, 15, 29, 59, 123))
        due = game_clock.plus_realtime(datetime.timedelta(seconds=60))
        d = the_driver.Deferred(due, os.getcwd, None, None)
        result = d.when_due(game_clock)
        self.assertIsInstance(result, datetime.timedelta)
        self.assertEqual(datetime.timedelta(seconds=60), result)
        result = d.when_due(game_clock, True)   # realtime
        self.assertEqual(datetime.timedelta(seconds=60), result)
        game_clock.add_gametime(datetime.timedelta(seconds=20))   # +20 gametime seconds
        result = d.when_due(game_clock)   # not realtime (game time)
        self.assertEqual(datetime.timedelta(seconds=40), result)
        result = d.when_due(game_clock, True)   # realtime
        self.assertEqual(datetime.timedelta(seconds=40), result)

    def testDue_gametime(self):
        # test due timings where the gameclock == 10 times realtime clock
        game_clock = tale.util.GameDateTime(datetime.datetime(2013, 7, 18, 15, 29, 59, 123), 10)   # 10 times realtime
        due = game_clock.plus_realtime(datetime.timedelta(seconds=60))      # due in (realtime) 60 seconds (600 gametime seconds)
        d = the_driver.Deferred(due, os.getcwd, None, None)
        result = d.when_due(game_clock)   # not realtime
        self.assertIsInstance(result, datetime.timedelta)
        self.assertEqual(datetime.timedelta(seconds=10 * 60), result)
        result = d.when_due(game_clock, True)   # realtime
        self.assertEqual(datetime.timedelta(seconds=60), result)
        game_clock.add_gametime(datetime.timedelta(seconds=20))   # +20 gametime seconds (=2 realtime seconds)
        result = d.when_due(game_clock)   # not realtime (game time)
        self.assertEqual(datetime.timedelta(seconds=580), result)
        result = d.when_due(game_clock, True)   # realtime
        self.assertEqual(datetime.timedelta(seconds=58), result)


class TestVarious(unittest.TestCase):
    def testCommandsLoaded(self):
        self.assertGreater(len(tale.cmds.normal.all_commands), 1)
        self.assertGreater(len(tale.cmds.wizard.all_commands), 1)

    def testEnableNotifyActionSetAndDocstring(self):
        for cmd in tale.cmds.normal.all_commands.values():
            self.assertIsNotNone(cmd.__doc__, "all commands must have docstring")
            self.assertTrue(cmd.enable_notify_action in (True, False))
        for cmd in tale.cmds.wizard.all_commands.values():
            self.assertIsNotNone(cmd.__doc__, "all commands must have docstring")
            self.assertFalse(cmd.enable_notify_action, "all wizard commands must have enable_notify_action set to False")

    def testStoryVerify(self):
        gamedir = os.path.dirname(inspect.getabsfile(tale.demo))
        d = the_driver.Driver()
        d.start(["--game", gamedir, "--verify"])


@cmd
@disabled_in_gamemode("if")
def func1(player, parsed, ctx):
    pass

@cmd
def func2(player, parsed, ctx):
    pass

@cmd
def func3(player, parsed, ctx):
    pass

@wizcmd
def func4(player, parsed, ctx):
    pass


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.cmds = the_driver.Commands()
        self.cmds.add("verb1", func1)
        self.cmds.add("verb2", func2)
        self.cmds.add("verb3", func2, "wizard")
        self.cmds.add("verb4", func3, "noob")

    def testCommandsOverrideFail(self):
        with self.assertRaises(KeyError):
            self.cmds.override("verbXXX", func2)

    def testCommandsOverride(self):
        self.cmds.override("verb4", func2, "noob")

    def testCommandsAdjust(self):
        wiz = self.cmds.get(["wizard"])
        self.assertEqual({"verb1", "verb2", "verb3"}, set(wiz.keys()))
        wiz = self.cmds.get([None])
        self.assertEqual({"verb1", "verb2"}, set(wiz.keys()))
        self.cmds.adjust_available_commands("if")
        wiz = self.cmds.get(["wizard"])
        self.assertEqual({"verb2", "verb3"}, set(wiz.keys()))
        wiz = self.cmds.get([None])
        self.assertEqual({"verb2"}, set(wiz.keys()))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
