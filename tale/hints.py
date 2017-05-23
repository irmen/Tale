"""
Hints system.
Provides clues about what to do next, based on what the player
has already achieved and several other parameters (such as their
current location). Also provides the recap log to be able to get up to speed
with certain key events and actions that the player performed earlier.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from typing import Sequence, Optional, Any, List, Union

from .base import Location, Living


class Hint:
    def __init__(self, checkpoint: str, location: Location, text: str) -> None:
        """
        Define a new hint. checkpoint=game checkpoint (string) for which the hint is active.
        location=location where the hint applies to (can be None).
        text=the hint text to show.
        """
        self.checkpoint = checkpoint
        self.location = location
        self.text = text

    def active(self, checkpoints: Sequence[str], player: Living) -> Union[bool, None]:
        """override and return True/False to enable/disable the hint for specific checkpoints or player state"""
        return None  # default implementation does nothing

    def __eq__(self, other: Any) -> bool:
        if self.__class__ == other.__class__:
            return vars(self) == vars(other)
        return NotImplemented


class HintSystem:
    def __init__(self) -> None:
        self.init([])

    def init(self, hints: Sequence[Hint]) -> None:
        """Specify new hints and reset active states and hints"""
        self.all_hints = hints
        self.active_hints = []  # type: List[Hint]
        self.checkpoints = []  # type: List[str]
        self.recap_log = []  # type: List[str]
        self.checkpoint(None)

    def has_hints(self) -> bool:
        return len(self.all_hints) > 0

    def checkpoint(self, checkpoint: str, recap_message: str=None) -> bool:
        """
        Activate a new possible set of hints based on the newly activated checkpoint.
        It returns True if the checkpoint was newly recorded, False if it was known already.
        Also remember optional recap message belonging to this state.
        Note that checkpoints stack.
        """
        if checkpoint in self.checkpoints:
            return False
        self.checkpoints.append(checkpoint)
        if recap_message:
            self.recap_log.append(recap_message)
        self.active_hints = []
        for checkpoint in reversed(self.checkpoints):
            new_hints = [hint for hint in self.all_hints if hint.checkpoint == checkpoint]
            if new_hints:
                self.active_hints = new_hints
                break
        return True

    def hint(self, player: Living) -> Optional[str]:
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

    def recap(self) -> Sequence[str]:
        """Return the list of recap messages thus far."""
        return self.recap_log
