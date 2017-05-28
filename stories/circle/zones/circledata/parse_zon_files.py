"""
Parse CircleMUD zone files.

Initially based on code by Al Sweigart, but heavily modified since:
http://inventwithpython.com/blog/2012/03/19/circlemud-data-in-xml-format-for-your-text-adventure-game/
"""

import re
from types import SimpleNamespace
from typing import Dict, List
from tale.vfs import VirtualFileSystem


__all__ = ["get_zones"]


zones = {}  # type: Dict[int, SimpleNamespace]
extendedMobPat = re.compile('(.*?):(.*)')


def parse_file(content):
    content = [line.strip() for line in content]

    linenum = 0
    allmobs = []
    alldoors = []
    allobjects = []
    allremove = []

    # import pdb; pdb.set_trace()
    vnumArg = content[linenum][1:]
    linenum += 1
    while content[linenum].startswith('*'): linenum += 1
    zonenameArg = content[linenum][:-1]
    linenum += 1
    while content[linenum].startswith('*'): linenum += 1
    startroomArg, endroomArg, lifespanArg, resetArg = content[linenum].split()
    linenum += 1

    while linenum < len(content):  # read in commands
        line = content[linenum]
        if line.startswith('*'):
            linenum += 1
            continue

        if line == 'S':
            break  # reached end of file

        line = content[linenum].split()

        command = line[0]

        if command == 'M':
            # output.write('m %s' % lineNum)
            #  add a mob
            #  NOTE - I'm ignoring the if-flag for mobs
            allmobs.append({'vnum': line[2], 'max': line[3], 'room': line[4], 'inv': [], 'equip': {}})
        elif command == 'G':
            # output.write('g %s' % lineNum)
            allmobs[-1]['inv'].append({'vnum': line[2], 'max': line[3]})
        elif command == 'E':
            # output.write('e %s' % lineNum)
            allmobs[-1]['equip'][line[4]] = {'vnum': line[2], 'max': line[3]}
        elif command == 'O':
            # output.write('o %s' % lineNum)
            allobjects.append({'vnum': line[2], 'max': line[3], 'room': line[4], 'contains': []})
        elif command == 'P':
            # output.write('p %s' % lineNum)
            obj_to_load = line[2]
            obj_to_put_into = line[4]
            for o in allobjects:
                if o['vnum'] == obj_to_put_into:
                    o['contains'].append({'vnum': obj_to_load, 'max': line[3]})
        elif command == 'D':
            # output.write('d %s' % lineNum)
            alldoors.append({'room': line[2], 'exit': line[3], 'state': line[4]})
        elif command == 'R':
            # output.write('r %s' % lineNum)
            allremove.append({'room': line[2], 'vnum': line[3]})
        linenum += 1

    exitMap = {'0': 'north',
               '1': 'east',
               '2': 'south',
               '3': 'west',
               '4': 'up',
               '5': 'down'}
    doorstateMap = {'0': 'open', '1': 'closed', '2': 'locked'}
    wornMap = {'0': 'light',
               '1': 'rightfinger',
               '2': 'leftfinger',
               '3': 'neck1',
               '4': 'neck2',
               '5': 'body',
               '6': 'head',
               '7': 'legs',
               '8': 'feet',
               '9': 'hands',
               '10': 'arms',
               '11': 'shield',
               '12': 'aboutbody',
               '13': 'waist',
               '14': 'rightwrist',
               '15': 'leftwrist',
               '16': 'wield',
               '17': 'held'}
    resetMap = {'0': 'never', '1': 'afterdeserted', '2': 'asap'}

    zone = SimpleNamespace(
        circle_vnum=int(vnumArg),
        name=zonenameArg,
        startroom=int(startroomArg),
        endroom=int(endroomArg),
        lifespan_minutes=int(lifespanArg),
        resetmode=resetMap[resetArg],
        mobs=[],
        objects=[],
        doors=[]
    )
    for m in allmobs:
        mob = SimpleNamespace(
            circle_vnum=int(m["vnum"]),
            globalmax=int(m["max"]),
            room=int(m["room"]),
            inventory={},
            equipped={}
        )
        for i in m['inv']:
            mob.inventory[int(i["vnum"])] = int(i["max"])
        for k, v in m['equip'].items():
            mob.equipped[int(v["vnum"])] = {
                "globalmax": int(v["max"]),
                "wornon": wornMap[k]
            }
        zone.mobs.append(mob)
    for o in allobjects:
        obj = {
            "vnum": int(o["vnum"]),
            "globalmax": int(o["max"]),
            "room": int(o["room"]),
            "contains": {}   # maps vnum to maximum number of these
        }
        for c in o['contains']:
            obj["contains"][int(c["vnum"])] = int(c["max"])
        zone.objects.append(obj)
    for d in alldoors:
        zone.doors.append({
            "room": int(d["room"]),
            "exit": exitMap[d["exit"]],
            "state": doorstateMap[d["state"]]
        })

    zones[zone.circle_vnum] = zone


def parse_all() -> None:
    vfs = VirtualFileSystem(root_package="zones.circledata", everythingtext=True)
    for filename in vfs["world/zon/index"].text.splitlines():
        if filename == "$":
            break
        data = vfs["world/zon/" + filename].text.splitlines()
        parse_file(data)


def get_zones() -> Dict[int, SimpleNamespace]:
    if not zones:
        parse_all()
        assert len(zones) == 30, "all zones must be loaded"
    return zones


if __name__ == "__main__":
    zones = get_zones()
    print("parsed", len(zones), "zones.")
