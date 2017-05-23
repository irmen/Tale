"""
Unittests for Pubsub

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import gc
import time
import unittest

from tale.pubsub import topic, unsubscribe_all, Listener, sync, pending


class Subber(Listener):
    def __init__(self, name):
        self.messages = []
        self.name = name

    def pubsub_event(self, topicname, event):
        self.messages.append((topicname, event))
        return self.name

    def clear(self):
        self.messages = []


class RefusingSubber(Subber):
    def pubsub_event(self, topicname, event):
        raise Listener.NotYet


class TestPubsub(unittest.TestCase):
    def test_global_namespace(self):
        s1 = topic("s1")
        s2 = topic("s2")
        s3 = topic("s1")
        self.assertTrue(s1 is s3)
        self.assertFalse(s1 is s2)

    def test_aggregate_topic_name(self):
        s1 = topic(("t", 42))
        s2 = topic(("t", 55))
        s3 = topic(("t", 42))
        self.assertTrue(s1 is s3)
        self.assertFalse(s1 is s2)

    def test_pubsub_sync(self):
        sync()
        s = topic("testsync")
        subber = Subber("sub1")
        subber2 = Subber("sub2")
        s.subscribe(subber)
        s.subscribe(subber)
        s.subscribe(subber2)
        s.subscribe(subber2)
        result = s.send([1, 2, 3], True)
        self.assertEqual([("testsync", [1, 2, 3])], subber.messages)
        self.assertEqual([("testsync", [1, 2, 3])], subber2.messages)
        self.assertEqual(2, len(result))
        self.assertTrue("sub1" in result)
        self.assertTrue("sub2" in result)
        # check explicit unsubscribe
        s.unsubscribe(subber)
        s.unsubscribe(subber)
        s.unsubscribe(subber2)
        result = s.send("after unsubscribing", True)
        self.assertEqual(0, len(result))

    def test_pubsub_async(self):
        sync()
        s = topic("test1async")
        subber = Subber("sub1")
        subber2 = Subber("sub2")
        s.subscribe(subber)
        s.subscribe(subber2)
        s2 = topic("test1async")
        result = s2.send("event1")
        self.assertIsNone(result)
        self.assertEqual([], subber.messages)
        self.assertEqual([], subber2.messages)
        events, idle, subbers = pending()["test1async"]
        self.assertEqual(1, events)
        result = sync()
        events, idle, subbers = pending()["test1async"]
        self.assertEqual(0, events)
        self.assertEqual([], result)
        self.assertEqual([("test1async", "event1")], subber.messages)
        self.assertEqual([("test1async", "event1")], subber2.messages)
        subber.clear()
        subber2.clear()
        s2.send("event2")
        result = sync("test1async")
        self.assertEqual(2, len(result))
        self.assertTrue("sub1" in result)
        self.assertTrue("sub2" in result)
        self.assertEqual([("test1async", "event2")], subber.messages)
        self.assertEqual([("test1async", "event2")], subber2.messages)

    def test_notyet(self):
        s = topic("notyet")
        subber = RefusingSubber("refuser")
        s.subscribe(subber)
        s.send("event", True)
        self.assertEqual([], subber.messages)

    def test_weakrefs(self):
        s = topic("test222")
        subber = Subber("sub1")
        s.subscribe(subber)
        del subber
        gc.collect()
        result = s.send("after gc", True)
        self.assertEqual(0, len(result))

    def test_weakrefs2(self):
        class Wiretap(Listener):
            def __init__(self):
                self.messages = []

            def create_tap(self):
                tap = topic("wiretaptest")
                tap.subscribe(self)

            def pubsub_event(self, topicname, event):
                self.messages.append((topicname, event))
                return 99

        wiretap = Wiretap()
        wiretap.create_tap()
        t = topic("wiretaptest")
        result = t.send("hi", True)
        self.assertEqual(1, len(result))
        self.assertEqual([('wiretaptest', 'hi')], wiretap.messages)
        del wiretap
        gc.collect()
        result = t.send("after gc", True)
        self.assertEqual(0, len(result))

    def test_unsubscribe_all(self):
        s1 = topic("testA")
        s2 = topic("testB")
        s3 = topic("testC")
        subber = Subber("sub1")
        s1.subscribe(subber)
        s2.subscribe(subber)
        s3.subscribe(subber)
        s1.send("one")
        s2.send("two")
        s3.send("three")
        sync()
        self.assertEqual({('testA', 'one'), ('testB', 'two'), ('testC', 'three')}, set(subber.messages))
        subber.clear()
        unsubscribe_all(subber)
        unsubscribe_all(subber)
        s1.send("one")
        s2.send("two")
        s3.send("three")
        sync()
        self.assertEqual([], subber.messages)

    def test_destroy(self):
        sync()
        s1 = topic("testA")
        s2 = topic("testB")
        s1.send("123")
        p = pending()
        self.assertIn("testA", p)
        self.assertIn("testB", p)
        s1.destroy()
        self.assertEqual("<defunct>", s1.name)
        p = pending()
        self.assertNotIn("testA", p)
        self.assertIn("testB", p)
        s2.destroy()
        p = pending()
        self.assertNotIn("testA", p)
        self.assertNotIn("testB", p)

    def test_idletime(self):
        sync()
        s = topic("testA")
        self.assertLess(s.idle_time, 0.1)
        time.sleep(0.2)
        self.assertGreater(s.idle_time, 0.1)
        s.send("event")
        self.assertLess(s.idle_time, 0.1)


if __name__ == '__main__':
    unittest.main()
