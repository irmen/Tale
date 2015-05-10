# coding=utf-8
"""
Simple Pubsub signaling. Provides immediate (synchronous) sending,
or store-and-forward sending when the sync() function is called.
Uses weakrefs to not needlessly lock subscribers/topics in memory.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import weakref
import threading


__all__ = ["topic", "unsubscribe_all", "Listener"]

all_topics = {}
__topic_lock = threading.Lock()


def topic(name):
    """Create a topic object (singleton). Name can be a string or a tuple."""
    with __topic_lock:
        if name in all_topics:
            return all_topics[name]
        instance = all_topics[name] = Topic(name)
        return instance


def sync(topic=None):
    """Sync all pending events (i.e. push them to the subscribers)"""
    if topic:
        return all_topics[topic].sync()
    else:
        for t in all_topics.values():
            t.sync()


def pending(topic=None):
    """Return a dictionary from topic name to list of pending events"""
    with __topic_lock:
        names = [topic] if topic else all_topics.keys()
        return {name: all_topics[name].events.copy() for name in names}


def unsubscribe_all(subscriber):
    """unsubscribe the given subscriber object from all topics that it may have been subscribed to."""
    for topic in all_topics.values():
        topic.unsubscribe(subscriber)


class Listener(object):
    """Base class for all pubsub listeners (subscribers)"""
    def pubsub_event(self, topicname, event):
        """override this event receive method in a subclass"""
        raise NotImplementedError("implement this in subclass")

    class NotYet(Exception):
        """raise this from pubsub_event to signal that you don't want to consume the event just yet"""
        pass


class Topic(object):
    def __init__(self, name):
        self.name = name
        self.subscribers = set()
        self.events = []

    def subscribe(self, subscriber):
        if not isinstance(subscriber, Listener):
            raise TypeError("subscriber needs to be a Listener")
        self.subscribers.add(weakref.ref(subscriber))

    def unsubscribe(self, subscriber):
        self.subscribers.discard(weakref.ref(subscriber))

    def send(self, event, synchronous=False):
        self.events.append(event)
        if synchronous:
            return self.sync()

    def sync(self):
        events, self.events = self.events, []
        results = []
        for event in events:
            results.extend(self.__sync_event(event))
        return results

    def __sync_event(self, event):
        results = []
        for subber_ref in self.subscribers:
            subber = subber_ref()
            if subber is not None:
                try:
                    result = subber.pubsub_event(self.name, event)
                    results.append(result)
                except Listener.NotYet:
                    pass
        return results
