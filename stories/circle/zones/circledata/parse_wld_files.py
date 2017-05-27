"""
Parse CircleMUD world files.

Initially based on code by Al Sweigart, but heavily modified since:
http://inventwithpython.com/blog/2012/03/19/circlemud-data-in-xml-format-for-your-text-adventure-game/
"""

from types import SimpleNamespace
from typing import Dict, List
from tale.vfs import VirtualFileSystem


__all__ = ["get_rooms"]


rooms = {}  # type: Dict[int, SimpleNamespace]


def parse_file(content):
    content = [line.strip() for line in content]

    readstate = 'vNum'
    descarg = ''
    linenum = 0

    while linenum < len(content):
        line = content[linenum]

        if readstate == 'vNum':
            if line == '$':
                break  # reached end of file
            vNumArg = line[1:]
            nameArg = content[linenum + 1][:-1]
            readstate = 'desc'
            linenum += 2
        elif readstate == 'desc':
            doneLineNum = linenum
            while content[doneLineNum] != '~':
                doneLineNum += 1
            descarg = '\n'.join(content[linenum:doneLineNum])
            linenum = doneLineNum + 1
            readstate = 'bitVector'
        elif readstate == 'bitVector':
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
            linenum += 1
            readstate = 'exitAndDesc'
        elif readstate == 'exitAndDesc':
            extraDescsArg = []
            exitsArg = []
            while content[linenum] != 'S':
                if content[linenum] == 'E':
                    doneLineNum = linenum + 1
                    while content[doneLineNum] != '~':
                        doneLineNum += 1
                    extraDescsArg.append({'keywords': content[linenum + 1][:-1],
                                          'desc': '\n'.join(content[linenum + 2:doneLineNum])})
                    linenum = doneLineNum + 1
                elif content[linenum].startswith('D'):
                    exitDirection = {'0': 'north',
                                     '1': 'east',
                                     '2': 'south',
                                     '3': 'west',
                                     '4': 'up',
                                     '5': 'down'}[content[linenum][1:2]]
                    doneLineNum = linenum + 1
                    while content[doneLineNum] != '~':
                        doneLineNum += 1
                    exitDesc = '\n'.join(content[linenum + 1:doneLineNum])
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
                    linenum = doneLineNum + 3

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

            room = SimpleNamespace(
                circle_vnum=int(vNumArg),
                name=nameArg,
                type=sectorTypeArg,
                zone=int(zoneArg),
                attributes=set(attribs),
                desc=descarg.replace("\n", " ") or None,
                exits={},
                extradesc=[]
            )
            for exitArg in exitsArg:
                xt = SimpleNamespace(
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

            rooms[room.circle_vnum] = room
            descarg = ''
            readstate = 'vNum'
            linenum += 1


def parse_all() -> None:
    vfs = VirtualFileSystem(root_package="zones.circledata", everythingtext=True)
    for filename in vfs["world/wld/index"].text.splitlines():
        if filename == "$":
            break
        data = vfs["world/wld/" + filename].text.splitlines()
        parse_file(data)


def get_rooms() -> Dict[int, SimpleNamespace]:
    if not rooms:
        parse_all()
        assert len(rooms) == 1878, "all rooms must be loaded"
    return rooms


if __name__ == "__main__":
    rooms = get_rooms()
    print("parsed", len(rooms), "rooms.")
