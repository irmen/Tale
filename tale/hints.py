"""
Hints system.
Provides clues about what to do next, based on what the player
has already achieved and several other parameters (such as their
current location). Also provides the recap log to be able to get up to speed
with certain key events and actions that the player performed earlier.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division, unicode_literals
from collections import namedtuple

Hint = namedtuple("Hint", "state location filter text")


class HintSystem(object):
    def __init__(self):
        self.init([])

    def init(self, hints):
        """Specify new hints and reset active states and hints"""
        self.all_hints = hints
        self.active_hints = []
        self.states = []
        self.recap_log = []
        self.state(None)

    def has_hints(self):
        return len(self.all_hints) > 0

    def state(self, state, recap_message=None):
        """Activate a new possible set of hints based on the new state. Also remember optional recap message belonging to this state."""
        if state not in self.states:
            self.states.append(state)
            if recap_message:
                self.recap_log.append(recap_message)
            self.active_hints = []
            for state in reversed(self.states):
                new_hints = [hint for hint in self.all_hints if hint.state == state]
                if new_hints:
                    self.active_hints = new_hints
                    return

    def hint(self, player):
        """Return the hints that are active for the given state, most specific ones have priority."""
        candidates = [hint for hint in self.active_hints if hint.location and hint.location == player.location]
        if not candidates:
            candidates = [hint for hint in self.active_hints if not hint.location]
        candidates2 = [hint for hint in candidates if hint.filter and hint.filter(self.states, player)]
        if not candidates2:
            candidates2 = [hint for hint in candidates if not hint.filter]
        if candidates2:
            return " ".join(hint.text for hint in candidates2)
        return None

    def recap(self):
        """Return the list of recap messages thus far."""
        return self.recap_log
