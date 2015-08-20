"""
Parse CircleMUD zone files.

Based on code by Al Sweigart;
http://inventwithpython.com/blog/2012/03/19/circlemud-data-in-xml-format-for-your-text-adventure-game/
"""

import os
import re
import io


__all__ = ["get_zones"]


class Zone(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __repr__(self):
        return "<Zone #%d: %s>" % (self.vnum, self.name)


class MobRef(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __repr__(self):
        return "<MobRef to #%d>" % self.vnum


zones = {}
extendedMobPat = re.compile('(.*?):(.*)')


def parse_file(zonFile):
    with io.open(zonFile) as fp:
        content = [line.strip() for line in fp]

    lineNum = 0
    allmobs = []
    alldoors = []
    allobjects = []
    allremove = []

    #import pdb; pdb.set_trace()
    vnumArg = content[lineNum][1:]
    lineNum += 1
    while content[lineNum].startswith('*'): lineNum += 1
    zonenameArg = content[lineNum][:-1]
    lineNum += 1
    while content[lineNum].startswith('*'): lineNum += 1
    startroomArg, endroomArg, lifespanArg, resetArg = content[lineNum].split()
    lineNum += 1

    while lineNum < len(content):  # read in commands
        line = content[lineNum]
        if line.startswith('*'):
            lineNum += 1
            continue

        if line == 'S':
            break  # reached end of file

        line = content[lineNum].split()

        command = line[0]

        if command == 'M':
            #output.write('m %s' % lineNum)
            # add a mob
            # NOTE - I'm ignoring the if-flag for mobs
            allmobs.append({'vnum': line[2], 'max': line[3], 'room': line[4], 'inv': [], 'equip': {}})
        elif command == 'G':
            #output.write('g %s' % lineNum)
            allmobs[-1]['inv'].append({'vnum': line[2], 'max': line[3]})
        elif command == 'E':
            #output.write('e %s' % lineNum)
            allmobs[-1]['equip'][line[4]] = {'vnum': line[2], 'max': line[3]}
        elif command == 'O':
            #output.write('o %s' % lineNum)
            allobjects.append({'vnum': line[2], 'max': line[3], 'room': line[4], 'contains': []})
        elif command == 'P':
            #output.write('p %s' % lineNum)
            obj_to_load = line[2]
            obj_to_put_into = line[4]
            for o in allobjects:
                if o['vnum'] == obj_to_put_into:
                    o['contains'].append({'vnum': obj_to_load, 'max': line[3]})
        elif command == 'D':
            #output.write('d %s' % lineNum)
            alldoors.append({'room': line[2], 'exit': line[3], 'state': line[4]})
        elif command == 'R':
            #output.write('r %s' % lineNum)
            allremove.append({'room': line[2], 'vnum': line[3]})
        lineNum += 1

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

    zone = Zone(
        vnum=int(vnumArg),
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
        mob = MobRef(
            vnum=int(m["vnum"]),
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
            "contains": {}
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

    zones[zone.vnum] = zone


def parse_all():
    datadir = os.path.join(os.path.dirname(__file__), "world/zon")
    for filename in os.listdir(datadir):
        if not filename.endswith('.zon'):
            continue
        parse_file(os.path.join(datadir, filename))


def get_zones():
    if not zones:
        parse_all()
        assert len(zones) == 30
    return zones


if __name__ == "__main__":
    zones = get_zones()
    print("parsed", len(zones), "zones.")
