"""
Unittests for Pubsub

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import unittest
import gc
from tale.pubsub import topic, unsubscribe_all, Listener

class Subber(Listener):
    def __init__(self, name):
        self.messages=[]
        self.name = name
    def pubsub_event(self, topicname, event):
        self.messages.append((topicname, event))
        return self.name
    def clear(self):
        self.messages=[]


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

    def test_pubsub(self):
        s = topic("test1")
        subber = Subber("sub1")
        subber2 = Subber("sub2")
        s.subscribe(subber)
        s.subscribe(subber)
        s.subscribe(subber2)
        s.subscribe(subber2)
        s2 = topic("test1")
        result = s2.send([1, 2, 3])
        self.assertEqual(2, len(result))
        self.assertTrue("sub1" in result)
        self.assertTrue("sub2" in result)
        # check explicit unsubscribe
        s2.unsubscribe(subber)
        s2.unsubscribe(subber)
        s2.unsubscribe(subber2)
        result = s2.send("after unsubscribing")
        self.assertEqual(0, len(result))

    def test_weakrefs(self):
        s = topic("test222")
        subber = Subber("sub1")
        s.subscribe(subber)
        del subber
        gc.collect()
        result = s.send("after gc")
        self.assertEqual(0, len(result))

    def test_weakrefs2(self):
        class Wiretap(Listener):
            def __init__(self):
                self.messages=[]
            def create_tap(self):
                tap = topic("wiretaptest")
                tap.subscribe(self)
            def pubsub_event(self, topicname, event):
                self.messages.append((topicname, event))
                return 99
        wiretap = Wiretap()
        wiretap.create_tap()
        t = topic("wiretaptest")
        result = t.send("hi")
        self.assertEqual(1, len(result))
        self.assertEqual([('wiretaptest', 'hi')], wiretap.messages)
        del wiretap
        gc.collect()
        result = t.send("after gc")
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
        self.assertEqual([('testA', 'one'), ('testB', 'two'), ('testC', 'three')], subber.messages)
        subber.clear()
        unsubscribe_all(subber)
        unsubscribe_all(subber)
        s1.send("one")
        s2.send("two")
        s3.send("three")
        self.assertEqual([], subber.messages)



if __name__ == '__main__':
    unittest.main()
