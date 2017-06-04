"""
Simple Pubsub signaling. Provides immediate (synchronous) sending,
or store-and-forward sending when the sync() function is called.
Uses weakrefs to not needlessly lock subscribers/topics in memory.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)


Currently defined pubsub topics used by the Tale driver:

  "driver-pending-actions"
      Events are callables to be executed in the server tick loop.
      You can subscribe but only the driver may execute the events.

  "driver-pending-tells"
      Tells (messages) that have to be delivered to actors, after any
      other messages have been processed.
      You can subscribe but only the driver may execute the events.

  "driver-async-dialogs"
      actions that kick off new async dialogs (generators).
      You can subscribe but only the driver may execute the events.

  ("wiretap-location", <location name>)
      Used by the wiretapper on a location

  ("wiretap-living", <living name>)
      Used by the wiretapper on a living

"""

import threading
import time
import weakref
from typing import Dict, List, Tuple, Union, Optional, Set, Any

TopicNameType = Union[str, Tuple]

__all__ = ["topic", "unsubscribe_all", "Listener"]

all_topics = {}  # type: Dict[TopicNameType, Topic]
__topic_lock = threading.Lock()


class Listener:
    """Base class for all pubsub listeners (subscribers)"""
    def pubsub_event(self, topicname: TopicNameType, event: Any) -> Any:
        """override this event receive method in a subclass"""
        raise NotImplementedError("implement this in subclass")

    class NotYet(Exception):
        """raise this from pubsub_event to signal that you don't want to consume the event just yet"""
        pass


class Topic:
    """
    A pubsub topic to send/receive events. You get these from the topic function.
    """
    def __init__(self, name: TopicNameType) -> None:
        self.name = name
        self.subscribers = set()  # type: Set[weakref.ReferenceType[Listener]]
        self.events = []  # type: List[Any]
        self.last_event = time.time()  # type: float

    @property
    def idle_time(self) -> float:
        return time.time() - self.last_event

    def destroy(self) -> None:
        self.sync()
        del all_topics[self.name]
        self.name = "<defunct>"
        del self.subscribers
        del self.events

    def subscribe(self, subscriber: Listener) -> None:
        if not isinstance(subscriber, Listener):
            raise TypeError("subscriber must be a Listener")
        self.subscribers.add(weakref.ref(subscriber))

    def unsubscribe(self, subscriber: Listener) -> None:
        self.subscribers.discard(weakref.ref(subscriber))

    def send(self, event: Any, synchronous: bool=False) -> Optional[List[Any]]:
        self.events.append(event)
        self.last_event = time.time()
        if synchronous:
            return self.sync()
        return None

    def sync(self) -> List[Any]:
        events, self.events = self.events, []
        results = []
        for event in events:
            results.extend(self.__sync_event(event))
        return results

    def __sync_event(self, event: Any) -> List[Any]:
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


def topic(name: TopicNameType) -> Topic:
    """Create a topic object (singleton). Name can be a string or a tuple."""
    with __topic_lock:
        if name in all_topics:
            return all_topics[name]
        instance = all_topics[name] = Topic(name)
        return instance


def sync(topic: TopicNameType=None) -> List:
    """Sync all pending events (i.e. push them to the subscribers)"""
    if topic:
        return all_topics[topic].sync()
    else:
        for t in list(all_topics.values()):
            t.sync()
        return []


def pending(topicname: TopicNameType=None) -> Dict[TopicNameType, Tuple[int, float, int]]:
    """Return a dictionary from topic name to tuple (number of pending events, idle time, num subbers)"""
    with __topic_lock:
        topics = [all_topics[topicname]] if topicname else list(all_topics.values())
        return {t.name: (len(t.events), t.idle_time, len(t.subscribers)) for t in topics}


def unsubscribe_all(subscriber: Listener) -> None:
    """unsubscribe the given subscriber object from all topics that it may have been subscribed to."""
    for topic in list(all_topics.values()):
        topic.unsubscribe(subscriber)
