"""
Pubsub signaling.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import threading
import weakref

__all__=["topic", "unsubscribe_all", "Listener"]

all_topics = {}

def topic(name):
    with threading.Lock():
        if name in all_topics:
            return all_topics[name]
        instance = all_topics[name] = __Topic(name)
        return instance

def unsubscribe_all(subscriber):
    for topic in all_topics.values():
        topic.unsubscribe(subscriber)


class Listener(object):
    """Base class for all pubsub listeners (subscribers)"""
    def pubsub_event(self, topicname, event):
        """override this event receive method in a subclass"""
        raise NotImplementedError("implement this in subclass")


class __Topic(object):
    def __init__(self, name):
        self.name = name
        self.subscribers = set()

    def subscribe(self, subscriber):
        if not isinstance(subscriber, Listener):
            raise TypeError("subscriber needs to be a Listener")
        self.subscribers.add(weakref.ref(subscriber))

    def unsubscribe(self, subscriber):
        self.subscribers.discard(weakref.ref(subscriber))

    def send(self, event):
        results = []
        for subber_ref in self.subscribers:
            subber=subber_ref()
            if subber is not None:
                results.append(subber.pubsub_event(self.name, event))
        return results
