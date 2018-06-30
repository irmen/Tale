"""
Parse CircleMUD zone files.

Initially based on code by Al Sweigart, but has now been fully rewritten:
http://inventwithpython.com/blog/2012/03/19/circlemud-data-in-xml-format-for-your-text-adventure-game/

File format description:
http://www.circlemud.org/pub/CircleMUD/3.x/uncompressed/circle-3.1/doc/building.pdf
"""

from typing import Dict, Iterator, List, Optional, Tuple
from tale.vfs import VirtualFileSystem


__all__ = ["get_zones"]


class ZMobile:
    __slots__ = ("vnum", "max_exist", "room", "comment", "inventory", "equip")

    def __init__(self, vnum: int, max_exist: int, room: int, comment: str) -> None:
        self.vnum = vnum
        self.max_exist = max_exist
        self.room = room
        self.comment = comment
        self.inventory = []  # type: List[ZObject]
        self.equip = {}   # type: Dict[str, ZObject]


class ZObject:
    __slots__ = ("vnum", "max_exist", "room", "contains")

    def __init__(self, vnum: int, max_exist: int, room: Optional[int]) -> None:
        self.vnum = vnum
        self.max_exist = max_exist
        self.room = room
        self.contains = []    # type: List[Tuple[int, int]]


class ZDoorstate:
    __slots__ = ("room", "exit", "state")

    def __init__(self, room: int, exit: str, state: str) -> None:
        self.room = room
        self.exit = exit
        self.state = state


class ZZone:
    __slots__ = ("vnum", "name", "startroom", "endroom", "lifespan_minutes", "resetmode", "mobs", "objects", "doorstates", "removes")

    def __init__(self, vnum: int) -> None:
        self.vnum = vnum
        self.name = ""
        self.startroom = -1
        self.endroom = -1
        self.lifespan_minutes = -1
        self.resetmode = ""
        self.mobs = []    # type: List[ZMobile]
        self.objects = []    # type: List[ZObject]
        self.doorstates = []    # type: List[ZDoorstate]
        self.removes = []    # type: List[Tuple[int, int]]    # (room, item)


def parse_file(content: str) -> ZZone:
    equip_positions = {
        0: 'light',
        1: 'rightfinger',
        2: 'leftfinger',
        3: 'neck1',
        4: 'neck2',
        5: 'body',
        6: 'head',
        7: 'legs',
        8: 'feet',
        9: 'hands',
        10: 'arms',
        11: 'shield',
        12: 'aboutbody',
        13: 'waist',
        14: 'rightwrist',
        15: 'leftwrist',
        16: 'wield',
        17: 'held'
    }

    exit_map = {
        0: 'north',
        1: 'east',
        2: 'south',
        3: 'west',
        4: 'up',
        5: 'down'
    }

    doorstate_map = {
        0: 'open',
        1: 'closed',
        2: 'locked'  # and closed as well
    }

    reset_modes = {
        0: 'never',
        1: 'deserted',
        2: 'asap'
    }

    def iter_lines(src: str) -> Iterator[str]:
        for line in src.splitlines():
            if not line.startswith("*"):
                yield line

    lines = iter_lines(content)
    zone = ZZone(int(next(lines)[1:]))
    name = next(lines)
    if name[-1] != "~":
        raise ValueError("zone name must end with ~")
    zone.name = name[:-1]
    zone.startroom, zone.endroom, zone.lifespan_minutes, resetmode = map(int, next(lines).split())
    zone.resetmode = reset_modes[resetmode]
    prev_executed = True
    all_mobs = {}  # type: Dict[int, ZMobile]
    all_objs = []  # type: List[ZObject]     # most recently loaded appended at the end
    last_mobile_vnum = -1
    while True:
        line = next(lines)
        if line == "S":
            break
        cmd, iff, *args = line.split(maxsplit=5)
        if iff == '0' or prev_executed:
            prev_executed = True
            if cmd == 'M':
                zm = ZMobile(int(args[0]), int(args[1]), int(args[2]), args[3] if len(args) == 4 else None)
                all_mobs[zm.vnum] = zm
                zone.mobs.append(zm)
                last_mobile_vnum = zm.vnum
            elif cmd == 'O':
                zo = ZObject(int(args[0]), int(args[1]), int(args[2]))
                all_objs.append(zo)
                zone.objects.append(zo)
            elif cmd == 'G':
                zm = all_mobs[last_mobile_vnum]
                zo = ZObject(int(args[0]), int(args[1]), None)
                all_objs.append(zo)
                zm.inventory.append(zo)
            elif cmd == 'E':
                zm = all_mobs[last_mobile_vnum]
                equip_pos = equip_positions[int(args[2])]
                zo = ZObject(int(args[0]), int(args[1]), None)
                all_objs.append(zo)
                zm.equip[equip_pos] = zo
            elif cmd == 'P':
                container_vnum = int(args[2])
                for container in reversed(all_objs):
                    if container.vnum == container_vnum:
                        container.contains.append((int(args[0]), int(args[1])))   # (vnum, max_exist)
                        break
                else:
                    descr = "?" if len(args) < 4 else args[3]
                    print("zone %d: attempt to put %s (%s) in non-existing container %s" % (zone.vnum, args[0], descr, args[2]))
                    # prev_executed = False
            elif cmd == 'D':
                zone.doorstates.append(ZDoorstate(int(args[0]), exit_map[int(args[1])], doorstate_map[int(args[2])]))
            elif cmd == 'R':
                zone.removes.append((int(args[0]), int(args[1])))    # (room, object)
            else:
                raise ValueError("invalid zone command: " + cmd)
    return zone


_zones = {}  # type: Dict[int, ZZone]


def get_zones(vfs: VirtualFileSystem = None) -> Dict[int, ZZone]:
    if not _zones:
        vfs = vfs or VirtualFileSystem(root_package="zones.circledata", everythingtext=True)
        for filename in vfs["world/zon/index"].text.splitlines():
            if filename == "$":
                break
            zone = parse_file(vfs["world/zon/" + filename].text)
            _zones[zone.vnum] = zone
        assert len(_zones) == 30, "all zones must be loaded"
    return _zones


if __name__ == "__main__":
    vfs = VirtualFileSystem(root_path=".", everythingtext=True)
    result = get_zones(vfs=vfs)
    print("parsed", len(result), "zones.")
