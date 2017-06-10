"""
Package containing the mob classes of the game.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import random
from tale.base import Living
from tale.util import Context, call_periodically
from tale.shop import Shopkeeper


__all__ = ("CircleMob", "MPostmaster", "MCityguard", "MReceptionist", "MCryogenicist", "MFido",
           "MGuildmaster", "MGuildguard", "MJanitor", "MMagicuser", "MMayor", "MPuff", "MSnake", "MThief",
           "MGuildguard_Cleric", "MGuildguard_Mage", "MGuildguard_Thief", "MGuildguard_Warrior",
           "MGuildmaster_Cleric", "MGuildmaster_Mage", "MGuildmaster_Thief", "MGuildmaster_Warrior",
           "MCastleGuard", "MJames", "MCleaning", "MDicknDavid", "MJerry", "MKingWelmar",
           "MPeter", "MTim", "MTom", "MTrainingMaster", "MShopkeeper")


class CircleMob(Living):
    """Monster NPC having tailored behavior to suit circle data"""
    def init(self) -> None:
        self.circle_vnum = 0
        super().init()

    def do_wander(self, ctx: Context) -> None:
        # Let the mob wander randomly. Note: not all mobs do this!
        direction = self.select_random_move()
        if direction:
            self.move(direction.target, self)
        ctx.driver.defer(random.randint(20, 60), self.do_wander)   # @todo timings


# @todo implement the behavior of the various mob classes (see spec_procs.c / castle.c)


class MShopkeeper(CircleMob, Shopkeeper):
    # most of the behavior is already present in Shopkeeper.
    pass


class MPostmaster(CircleMob):
    pass


class MCityguard(CircleMob):
    pass


class MReceptionist(CircleMob):
    pass


class MCryogenicist(CircleMob):
    pass


class MGuildguard(CircleMob):
    pass


class MGuildmaster(CircleMob):
    pass


class MPuff(CircleMob):
    """Puff the dragon"""
    @call_periodically(10)
    def do_special(self, ctx: Context) -> None:
        r = random.randint(0, 30)
        if r == 0:
            self.do_socialize("say \"My god!  It's full of stars!\"")
        elif r == 1:
            self.do_socialize("say \"How'd all those fish get up here?\"")
        elif r == 2:
            self.do_socialize("say \"I'm a very female dragon.\"")
        elif r == 3:
            self.do_socialize("say \"I've got a peaceful, easy feeling.\"")


class MFido(CircleMob):
    pass


class MJanitor(CircleMob):
    pass


class MMayor(CircleMob):
    pass


class MSnake(CircleMob):
    pass


class MThief(CircleMob):
    pass


class MMagicuser(CircleMob):
    pass


class MGuildmaster_Mage(MGuildmaster):
    pass


class MGuildmaster_Cleric(MGuildmaster):
    pass


class MGuildmaster_Warrior(MGuildmaster):
    pass


class MGuildmaster_Thief(MGuildmaster):
    pass


class MGuildguard_Mage(CircleMob):
    pass


class MGuildguard_Cleric(CircleMob):
    pass


class MGuildguard_Warrior(CircleMob):
    pass


class MGuildguard_Thief(CircleMob):
    pass


# mobs from the Castle zone (150): (see castle.c)

class MCastleGuard(CircleMob):
    pass


class MJames(CircleMob):
    pass


class MCleaning(CircleMob):
    pass


class MDicknDavid(CircleMob):
    pass


class MTim(CircleMob):
    pass


class MTom(CircleMob):
    pass


class MKingWelmar(CircleMob):
    pass


class MTrainingMaster(CircleMob):
    pass


class MPeter(CircleMob):
    pass


class MJerry(CircleMob):
    pass
