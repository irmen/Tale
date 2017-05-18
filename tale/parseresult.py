"""
Helper stuff for command parsing.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from typing import Sequence, Dict, Optional, List


class ParseResult:
    class WhoInfo:
        def __init__(self, seqnr: int = 0) -> None:
            self.sequence = seqnr
            self.previous_word = None  # type: Optional[str]

        def __str__(self) -> str:
            return "[seq=%d, prev_word=%s]" % (self.sequence, self.previous_word)

    def __init__(self, verb: str, adverb: str=None, message: str=None, bodypart: str=None, qualifier: str=None,
                 args: List[str]=None, who_info: Dict=None, who_order: Sequence=None,
                 unrecognized: Sequence=None, unparsed: str="") -> None:
        self.verb = verb
        self.adverb = adverb
        self.message = message
        self.bodypart = bodypart
        self.qualifier = qualifier
        self.who_info = who_info or {}      # WhoInfo for all objects parsed  (note: who-objects can be items, livings, and exits!)
        self.who_order = who_order or []    # the order of the occurrence of the objects in the input text
        self.args = args or []
        self.unrecognized = unrecognized or []
        self.unparsed = unparsed
        if self.who_order and not self.who_info:
            self.recalc_who_info()

    def recalc_who_info(self) -> None:
        self.who_info = {}
        for sequence, who in enumerate(self.who_order):
            self.who_info[who] = ParseResult.WhoInfo(sequence)

    def __str__(self) -> str:
        who_info_str = [" %s->%s" % (living.name, info) for living, info in self.who_info.items()]
        s = [
            "ParseResult:",
            " verb=%s" % self.verb,
            " qualifier=%s" % self.qualifier,
            " adverb=%s" % self.adverb,
            " bodypart=%s" % self.bodypart,
            " message=%s" % self.message,
            " args=%s" % self.args,
            " unrecognized=%s" % self.unrecognized,
            " who_info=%s" % "\n   ".join(who_info_str),
            " who_order=%s" % self.who_order,
            " unparsed=%s" % self.unparsed
        ]
        return "\n".join(s)
