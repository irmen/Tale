# coding=utf-8
"""
Hints system.
Provides clues about what to do next, based on what the player
has already achieved and several other parameters (such as their
current location). Also provides the recap log to be able to get up to speed
with certain key events and actions that the player performed earlier.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals


class Hint(object):
    def __init__(self, checkpoint, location, text):
        """
        Define a new hint. checkpoint=game checkpoint (string) for which the hint is active.
        location=location where the hint applies to (can be None).
        text=the hint text to show.
        """
        self.checkpoint = checkpoint
        self.location = location
        self.text = text

    def active(self, checkpoints, player):
        """override and return True/False to enable/disable the hint for specific checkpoints or player state"""
        return None  # default implementation does nothing

    def __eq__(self, other):
        return vars(self) == vars(other)


class HintSystem(object):
    def __init__(self):
        self.init([])

    def init(self, hints):
        """Specify new hints and reset active states and hints"""
        self.all_hints = hints
        self.active_hints = []
        self.checkpoints = []
        self.recap_log = []
        self.checkpoint(None)

    def has_hints(self):
        return len(self.all_hints) > 0

    def checkpoint(self, checkpoint, recap_message=None):
        """
        Activate a new possible set of hints based on the newly activated checkpoint.
        Also remember optional recap message belonging to this state.
        Note that checkpoints stack.
        """
        if checkpoint not in self.checkpoints:
            self.checkpoints.append(checkpoint)
            if recap_message:
                self.recap_log.append(recap_message)
            self.active_hints = []
            for checkpoint in reversed(self.checkpoints):
                new_hints = [hint for hint in self.all_hints if hint.checkpoint == checkpoint]
                if new_hints:
                    self.active_hints = new_hints
                    return

    def hint(self, player):
        """Return the hints that are active for the current checkpoints, most specific ones have priority."""
        candidates = [hint for hint in self.active_hints if hint.location and hint.location == player.location]
        if not candidates:
            candidates = [hint for hint in self.active_hints if not hint.location]
        candidates2 = [hint for hint in candidates if hint.active(self.checkpoints, player)]
        if not candidates2:
            candidates2 = [hint for hint in candidates if hint.active(self.checkpoints, player) is None]
        if candidates2:
            return " ".join(hint.text for hint in candidates2)
        return None

    def recap(self):
        """Return the list of recap messages thus far."""
        return self.recap_log
