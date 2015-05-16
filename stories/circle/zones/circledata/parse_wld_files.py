"""
Parse CircleMUD world files.

Based on code by Al Sweigart;
http://inventwithpython.com/blog/2012/03/19/circlemud-data-in-xml-format-for-your-text-adventure-game/
"""

import os
import io


__all__ = ["get_rooms"]


class Room(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __repr__(self):
        return "<Room #%d: %s>" % (self.vnum, self.name)


class Exit(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs


rooms = {}


def parse_file(wldFile):
    with io.open(wldFile) as fp:
        content = [line.strip() for line in fp]

    readState = 'vNum'
    descArg = []
    lineNum = 0

    while lineNum < len(content):
        line = content[lineNum]

        if readState == 'vNum':
            if line == '$':
                break  # reached end of file
            vNumArg = line[1:]
            nameArg = content[lineNum + 1][:-1]
            readState = 'desc'
            lineNum += 2
        elif readState == 'desc':
            doneLineNum = lineNum
            while content[doneLineNum] != '~':
                doneLineNum += 1
            descArg = '\n'.join(content[lineNum:doneLineNum])
            lineNum = doneLineNum + 1
            readState = 'bitVector'
        elif readState == 'bitVector':
            zoneArg, bitVectorArg, sectorTypeArg = line.split()
            sectorTypeArg = {'0': 'inside',
                             '1': 'city',
                             '2': 'field',
                             '3': 'forest',
                             '4': 'hills',
                             '5': 'mountain',
                             '6': 'water_swim',
                             '7': 'water_noswim',
                             '8': 'underwater',
                             '9': 'flying'}[sectorTypeArg]
            lineNum += 1
            readState = 'exitAndDesc'
        elif readState == 'exitAndDesc':
            extraDescsArg = []
            exitsArg = []
            while content[lineNum] != 'S':
                if content[lineNum] == 'E':
                    doneLineNum = lineNum + 1
                    while content[doneLineNum] != '~':
                        doneLineNum += 1
                    extraDescsArg.append({'keywords': content[lineNum + 1][:-1],
                                          'desc': '\n'.join(content[lineNum + 2:doneLineNum])})
                    lineNum = doneLineNum + 1
                elif content[lineNum].startswith('D'):
                    exitDirection = {'0': 'north',
                                     '1': 'east',
                                     '2': 'south',
                                     '3': 'west',
                                     '4': 'up',
                                     '5': 'down'}[content[lineNum][1:2]]
                    doneLineNum = lineNum + 1
                    while content[doneLineNum] != '~':
                        doneLineNum += 1
                    exitDesc = '\n'.join(content[lineNum + 1:doneLineNum])
                    exitKeywords = content[doneLineNum + 1][:-1].split()
                    exitDoorFlag, exitKeyNumber, exitRoomLinked = content[doneLineNum + 2].split()
                    exitDoorFlag = {'0': 'nodoor',
                                    '1': 'normal',
                                    '2': 'pickproof'}[exitDoorFlag]
                    exitsArg.append({'direction': exitDirection,
                                     'desc': exitDesc,
                                     'keywords': exitKeywords,
                                     'type': exitDoorFlag,
                                     'keynum': exitKeyNumber,
                                     'roomlinked': exitRoomLinked})
                    lineNum = doneLineNum + 3

            # process this room
            attribs = []
            if 'a' in bitVectorArg: attribs.append('dark')
            if 'b' in bitVectorArg: attribs.append('death')
            if 'c' in bitVectorArg: attribs.append('nomob')
            if 'd' in bitVectorArg: attribs.append('indoors')
            if 'e' in bitVectorArg: attribs.append('peaceful')
            if 'f' in bitVectorArg: attribs.append('soundproof')
            if 'g' in bitVectorArg: attribs.append('notrack')
            if 'h' in bitVectorArg: attribs.append('nomagic')
            if 'i' in bitVectorArg: attribs.append('tunnel')
            if 'j' in bitVectorArg: attribs.append('private')
            if 'k' in bitVectorArg: attribs.append('godroom')
            if 'l' in bitVectorArg: attribs.append('house')
            if 'm' in bitVectorArg: attribs.append('house_crash')
            if 'n' in bitVectorArg: attribs.append('atrium')
            if 'o' in bitVectorArg: attribs.append('olc')
            if 'p' in bitVectorArg: attribs.append('bfs_mark')

            room = Room(
                vnum=int(vNumArg),
                name=nameArg,
                type=sectorTypeArg,
                zone=int(zoneArg),
                attributes=set(attribs),
                desc=descArg.replace("\n", " ") or None,
                exits={},
                extradesc=[]
            )
            for exitArg in exitsArg:
                xt = Exit(
                    direction=exitArg["direction"],
                    type=exitArg["type"],
                    key=int(exitArg["keynum"]) if exitArg["keynum"] else None,
                    roomlink=int(exitArg["roomlinked"]),
                    keywords=set(exitArg["keywords"]),
                    desc=exitArg["desc"].replace("\n", " ") if exitArg["desc"] else None
                )
                room.exits[xt.direction] = xt
            for arg in extraDescsArg:
                desc = {"keywords": set(arg["keywords"].split()), "text": arg["desc"].replace("\n", " ")}
                room.extradesc.append(desc)

            rooms[room.vnum] = room
            descArg = []
            readState = 'vNum'
            lineNum += 1


def parse_all():
    datadir = os.path.join(os.path.dirname(__file__), "world/wld")
    for filename in os.listdir(datadir):
        if not filename.endswith('.wld'):
            continue
        parse_file(os.path.join(datadir, filename))


def get_rooms():
    if not rooms:
        parse_all()
        assert len(rooms) == 1878
    return rooms


if __name__ == "__main__":
    rooms = get_rooms()
    print("parsed", len(rooms), "rooms.")
