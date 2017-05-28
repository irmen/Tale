"""
Mud driver (multi user server).

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import time
from .parseresult import ParseResult
from .base import Living, _limbo
from .util import Context, call_periodically
from .driver import Driver
from .story import GameMode
from . import lang
from . import errors


class MudDriver(Driver):
    """
    The Mud 'driver'.
    Multi-user server variant of the single player Driver.
    """
    def __init__(self, restricted=False) -> None:
        super().__init__()
        self.game_mode = GameMode.MUD
        self.restricted = restricted   # restricted mud mode? (no new players allowed)

    def start(self, game: str, mode: GameMode=GameMode.IF, gui: bool=False, web: bool=False,
              wizard: bool=False, delay: int=0, restricted: bool=False) -> None:
        if restricted != self.restricted:
            raise errors.TaleError("restricted mode mismatch in driver start")
        super().start(game, mode, gui, web, wizard, delay, restricted)


class LimboReaper(Living):
    """The Grim Reaper hangs about in Limbo, and makes sure no one stays there for too long."""
    def __init__(self) -> None:
        super().__init__(
            "reaper", "m", "elemental", "Grim Reaper",
            description="He wears black robes with a hood. Where a face should be, there is only nothingness. "
                        "He is carrying a large ominous scythe that looks very, very sharp.",
            short_description="A figure clad in black, carrying a scythe, is also present.")
        self.aliases = {"figure", "death"}
        self.candidates = {}    # type: Dict[base.Living, Tuple[float, int]]  # living (usually a player) --> (first_seen, texts shown)

    def notify_action(self, parsed: ParseResult, actor: Living) -> None:
        if parsed.verb == "say":
            actor.tell("%s just stares blankly at you, not saying a word." % lang.capital(self.title))
        else:
            actor.tell("%s stares blankly at you." % lang.capital(self.title))

    @call_periodically(3)
    def do_reap_souls(self, ctx: Context) -> None:
        # consider all livings currently in Limbo or having their location set to Limbo
        if self.location is not _limbo:
            # we somehow got misplaced, teleport back to limbo
            self.tell_others("{Title} looks around in wonder and says, \"I'm not supposed to be here.\"")
            self.move(_limbo, self)
            return
        in_limbo = {living for living in self.location.livings if living is not self}
        in_limbo.update({conn.player for conn in ctx.driver.all_players.values() if conn.player.location is _limbo})
        now = time.time()
        for candidate in in_limbo:
            if candidate not in self.candidates:
                self.candidates[candidate] = (now, 0)   # a new player first seen
        for candidate in list(self.candidates):
            if candidate not in in_limbo:
                del self.candidates[candidate]   # player no longer present in limbo
                continue
            first_seen, shown = self.candidates[candidate]
            duration = now - first_seen
            # Depending on how long the candidate is being observed, show increasingly threateningly warnings,
            # and eventually killing the candidate (and closing their connection).
            # For wizard players, this is not done and only a short notification is printed.
            if "wizard" in candidate.privileges and duration >= 2 and shown < 1:
                candidate.tell(self.title + " whispers: \"Hello there wizard. Please don't stay for too long.\"")
                shown = 99999
            if duration >= 30 and shown < 1:
                candidate.tell(self.title + " whispers: \"Greetings. Be aware that you must not linger here... Decide swiftly...\"")
                shown = 1
            elif duration >= 50 and shown < 2:
                candidate.tell(self.title + " looms over you and warns: \"You really cannot stay here much longer!\"")
                shown = 2
            elif duration >= 60 and shown < 3:
                candidate.tell(self.title + " menacingly raises his scythe!")
                shown = 3
            elif duration >= 63 and shown < 4:
                candidate.tell(self.title + " swings down his scythe and slices your soul cleanly in half. You are destroyed.")
                shown = 4
            elif duration >= 64 and "wizard" not in candidate.privileges:
                try:
                    conn = ctx.driver.all_players[candidate.name]
                except KeyError:
                    pass   # already gone
                else:
                    ctx.driver._disconnect_mud_player(conn)
            self.candidates[candidate] = (first_seen, shown)
