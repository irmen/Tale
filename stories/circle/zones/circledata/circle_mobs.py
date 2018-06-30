"""
The mob classes of the Circle game.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import re
import random
from types import SimpleNamespace
from typing import Type, List, Set, Dict
from tale.base import Living, Item
from tale.util import Context, call_periodically, roll_dice
from tale.shop import Shopkeeper
from tale.errors import ActionRefused
from .parse_mob_files import get_mobs


__all__ = ("converted_mobs", "mobs_with_special", "make_mob", "init_circle_mobs")


mobs = {}   # type: Dict[int, SimpleNamespace]


def init_circle_mobs() -> None:
    global mobs
    mobs = get_mobs()
    print(len(mobs), "mobs loaded.")


class CircleMob(Living):
    """Monster NPC having tailored behavior to suit circle data"""
    def init(self) -> None:
        self.circle_vnum = 0
        self.actions = set()   # type: Set[str]
        super().init()

    def do_wander(self, ctx: Context) -> None:
        # Let the mob wander randomly.
        direction = self.select_random_move()
        if direction:
            if "stayzone" in self.actions and self.location.circle_zone != direction.target.circle_zone:
                return   # mob must stay in its own zone
            # @todo avoid certain directions, conditions, etc
            self.move(direction.target, self, direction_names=direction.names)

    def do_scavenge(self, ctx: Context) -> None:
        # Pick up the most valuable item in the room.
        most_valuable = None   # type: Item
        for item in self.location.items:
            try:
                item.allow_item_move(self, "take")
                if most_valuable is None or item.value > most_valuable.value:
                    most_valuable = item
            except ActionRefused:
                pass
        if most_valuable:
            try:
                most_valuable.move(self, self, verb="take")
                self.tell_others("{Actor} picks up %s." % most_valuable.title)
            except ActionRefused:
                pass

    def do_special(self, ctx: Context) -> None:
        # The special behavior of the mob. Not all mobs have these flags set!
        if "sentinel" not in self.actions:
            if random.random() <= 0.333:
                self.do_wander(ctx)
        if "scavenger" in self.actions:
            if random.random() < 0.1:
                self.do_scavenge(ctx)


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


# the various mob types, see spec_assign.c/assign_mobiles()
circle_mob_class = {
    1: MPuff,

    # Immortal Zone
    1200: MReceptionist,
    1201: MPostmaster,
    1202: MJanitor,

    # Midgaard
    3005: MReceptionist,
    3010: MPostmaster,
    3020: MGuildmaster,
    3021: MGuildmaster,
    3022: MGuildmaster,
    3023: MGuildmaster,
    3024: MGuildguard,
    3025: MGuildguard,
    3026: MGuildguard,
    3027: MGuildguard,
    3059: MCityguard,
    3060: MCityguard,
    3061: MJanitor,
    3062: MFido,
    3066: MFido,
    3067: MCityguard,
    3068: MJanitor,
    3095: MCryogenicist,
    3105: MMayor,

    # MORIA
    4000: MSnake,
    4001: MSnake,
    4053: MSnake,
    4100: MMagicuser,
    4102: MSnake,
    4103: MThief,

    # Redferne's
    7900: MCityguard,

    # PYRAMID
    5300: MSnake,
    5301: MSnake,
    5304: MThief,
    5305: MThief,
    5309: MMagicuser,  # should breath fire
    5311: MMagicuser,
    5313: MMagicuser,  # should be a cleric
    5314: MMagicuser,  # should be a cleric
    5315: MMagicuser,  # should be a cleric
    5316: MMagicuser,  # should be a cleric
    5317: MMagicuser,

    # High Tower Of Sorcery
    2501: MMagicuser,  # should likely be cleric
    2504: MMagicuser,
    2507: MMagicuser,
    2508: MMagicuser,
    2510: MMagicuser,
    2511: MThief,
    2514: MMagicuser,
    2515: MMagicuser,
    2516: MMagicuser,
    2517: MMagicuser,
    2518: MMagicuser,
    2520: MMagicuser,
    2521: MMagicuser,
    2522: MMagicuser,
    2523: MMagicuser,
    2524: MMagicuser,
    2525: MMagicuser,
    2526: MMagicuser,
    2527: MMagicuser,
    2528: MMagicuser,
    2529: MMagicuser,
    2530: MMagicuser,
    2531: MMagicuser,
    2532: MMagicuser,
    2533: MMagicuser,
    2534: MMagicuser,
    2536: MMagicuser,
    2537: MMagicuser,
    2538: MMagicuser,
    2540: MMagicuser,
    2541: MMagicuser,
    2548: MMagicuser,
    2549: MMagicuser,
    2552: MMagicuser,
    2553: MMagicuser,
    2554: MMagicuser,
    2556: MMagicuser,
    2557: MMagicuser,
    2559: MMagicuser,
    2560: MMagicuser,
    2562: MMagicuser,
    2564: MMagicuser,

    # SEWERS
    7006: MSnake,
    7009: MMagicuser,
    7200: MMagicuser,
    7201: MMagicuser,
    7202: MMagicuser,

    # FOREST
    6112: MMagicuser,
    6113: MSnake,
    6114: MMagicuser,
    6115: MMagicuser,
    6116: MMagicuser,  # should be a cleric
    6117: MMagicuser,

    # ARACHNOS
    6302: MMagicuser,
    6309: MMagicuser,
    6312: MMagicuser,
    6314: MMagicuser,
    6315: MMagicuser,

    # Desert
    5004: MMagicuser,
    5005: MGuildguard,  # brass dragon
    5010: MMagicuser,
    5014: MMagicuser,

    # Drow City
    5103: MMagicuser,
    5104: MMagicuser,
    5107: MMagicuser,
    5108: MMagicuser,

    # Old Thalos
    5200: MMagicuser,
    5201: MMagicuser,
    5209: MMagicuser,

    # New Thalos
    # 5481 - Cleric (or Mage... but he IS a high priest... *shrug*)
    5404: MReceptionist,
    5421: MMagicuser,
    5422: MMagicuser,
    5423: MMagicuser,
    5424: MMagicuser,
    5425: MMagicuser,
    5426: MMagicuser,
    5427: MMagicuser,
    5428: MMagicuser,
    5434: MCityguard,
    5440: MMagicuser,
    5455: MMagicuser,
    5461: MCityguard,
    5462: MCityguard,
    5463: MCityguard,
    5482: MCityguard,

    5400: MGuildmaster_Mage,
    5401: MGuildmaster_Cleric,
    5402: MGuildmaster_Warrior,
    5403: MGuildmaster_Thief,
    5456: MGuildguard_Mage,
    5457: MGuildguard_Cleric,
    5458: MGuildguard_Warrior,
    5459: MGuildguard_Thief,

    # ROME
    12009: MMagicuser,
    12018: MCityguard,
    12020: MMagicuser,
    12021: MCityguard,
    12025: MMagicuser,
    12030: MMagicuser,
    12031: MMagicuser,
    12032: MMagicuser,

    # DWARVEN KINGDOM
    6500: MCityguard,
    6502: MMagicuser,
    6509: MMagicuser,
    6516: MMagicuser,


    # mob classes from the King Welmar's Castle zone (150): (see castle.c)

    15000: MCastleGuard,  # Gwydion
    15001: MKingWelmar,  # Our dear friend: the King
    15003: MCastleGuard,  # Jim
    15004: MCastleGuard,  # Brian
    15005: MCastleGuard,  # Mick
    15006: MCastleGuard,  # Matt
    15007: MCastleGuard,  # Jochem
    15008: MCastleGuard,  # Anne
    15009: MCastleGuard,  # Andrew
    15010: MCastleGuard,  # Bertram
    15011: MCastleGuard,  # Jeanette
    15012: MPeter,  	# Peter
    15013: MTrainingMaster,  # The training master
    15015: MThief,       # Ergan... have a better idea?
    15016: MJames,  	# James the Butler
    15017: MCleaning,  # Ze Cleaning Fomen
    15020: MTim,  	# Tim: Tom's twin
    15021: MTom,  	# Tom: Tim's twin
    15024: MDicknDavid,  # Dick: guard of the Treasury
    15025: MDicknDavid,  # David: Dicks brother
    15026: MJerry,  	# Jerry: the Gambler
    15027: MCastleGuard,  # Michael
    15028: MCastleGuard,  # Hans
    15029: MCastleGuard,  # Boris
    15032: MMagicuser,  # Pit Fiend, have something better?  Use it
}


# various caches, DO NOT CLEAR THESE, or duplicates might be spawned
converted_mobs = set()   # type: Set[int]
mobs_with_special = set()     # type: Set[CircleMob]


def make_mob(vnum: int, mob_class: Type[CircleMob]=CircleMob) -> Living:
    """Create an instance of an item for the given vnum"""
    c_mob = mobs[vnum]
    name = c_mob.aliases[0]
    aliases = set(c_mob.aliases[1:])   # type: Set[str]
    title = c_mob.shortdesc
    if title.startswith("the ") or title.startswith("The "):
        title = title[4:]
    if title.startswith("a ") or title.startswith("A "):
        title = title[2:]
    # for now, we take the stats from the 'human' race because the circle data lacks race and stats
    # @todo map circle mobs on races?
    mob_class = circle_mob_class.get(vnum, mob_class)
    mob = mob_class(name, c_mob.gender, race="human", title=title, descr=c_mob.detaileddesc, short_descr=c_mob.longdesc)
    mob.circle_vnum = vnum  # keep the vnum
    if hasattr(c_mob, "extradesc"):
        for ed in c_mob.extradesc:
            mob.add_extradesc(ed["keywords"], ed["text"])
    mob.aliases = aliases
    mob.aggressive = "aggressive" in c_mob.actions
    mob.money = float(c_mob.gold)
    mob.stats.alignment = c_mob.alignment
    mob.stats.xp = c_mob.xp
    number, sides, hp = map(int, re.match(r"(\d+)d(\d+)\+(\d+)$", c_mob.maxhp_dice).groups())
    if number > 0 and sides > 0:
        hp += roll_dice(number, sides)[0]
    mob.stats.hp = hp
    mob.stats.maxhp_dice = c_mob.maxhp_dice
    mob.stats.level = max(1, c_mob.level)   # 1..50
    # convert AC -10..10 to more modern 0..20   (naked person(0)...plate armor(10)...battletank(20))
    # special elites can go higher (limit 100), weaklings with utterly no defenses can go lower (limit -100)
    mob.stats.ac = max(-100, min(100, 10 - c_mob.ac))
    mob.stats.attack_dice = c_mob.barehanddmg_dice
    assert isinstance(c_mob.actions, set)
    mob.actions = c_mob.actions
    if "special" in c_mob.actions:
        # this mob has the 'special' flag which means it has special programmed behavior that must periodically be triggered
        # movement of the mob is one thing that this takes care of (if the mob is not sentinel)
        mobs_with_special.add(mob)
    # @todo load position? (standing/sleeping/sitting...)
    # @todo convert thac0 to appropriate attack stat (armor penetration? to-hit bonus?)
    # @todo actions, affection,...
    converted_mobs.add(vnum)
    return mob
