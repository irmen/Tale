"""
Parse CircleMUD mob files.

Initially based on code by Al Sweigart, but heavily modified since:
http://inventwithpython.com/blog/2012/03/19/circlemud-data-in-xml-format-for-your-text-adventure-game/
"""

import re
from types import SimpleNamespace
from typing import Dict, List
from tale.vfs import VirtualFileSystem


__all__ = ["get_mobs"]


mobs = {}  # type: Dict[int, SimpleNamespace]
extendedMobPat = re.compile('(.*?):(.*)')


def parse_file(content):

    content = [line.strip() for line in content]

    readstate = 'vNum'
    linenum = 0

    while linenum < len(content):
        line = content[linenum]

        if readstate == 'vNum':
            if line == '$':
                break  # reached end of file
            vNumArg = line[1:]
            aliasArg = content[linenum + 1][:-1].split()
            shortDescArg = content[linenum + 2][:-1]
            readstate = 'longdesc'
            linenum += 3
        elif readstate == 'longdesc':
            doneLineNum = linenum
            while content[doneLineNum] != '~':
                doneLineNum += 1
            longDescArg = '\n'.join(content[linenum:doneLineNum])
            linenum = doneLineNum + 1
            readstate = 'detaileddesc'
        elif readstate == 'detaileddesc':
            doneLineNum = linenum
            while content[doneLineNum] != '~':
                doneLineNum += 1
            detailedDescArg = '\n'.join(content[linenum:doneLineNum])
            linenum = doneLineNum + 1
            readstate = 'bitVector'

        elif readstate == 'bitVector':
            actionBitVectorArg, affectBitVectorArg, alignmentArg, typeArg = content[linenum].split()

            linenum += 1
            readstate = 'level'
        elif readstate == 'level':
            levelArg, thacoArg, acArg, maxhpArg, bareHandDmgArg = content[linenum].split()
            goldArg, xpArg = content[linenum + 1].split()
            loadArg, defaultPosArg, sexArg = content[linenum + 2].split()
            linenum += 3

            extendedMobArg = {}
            if not content[linenum].startswith('#'):
                # this is the extended mob format.

                while content[linenum] not in ('E', '$'):
                    mo = extendedMobPat.match(content[linenum])
                    extendedMobArg[mo.group(1).strip()] = mo.group(2).strip()
                    linenum += 1
                if content[linenum] != '$':
                    linenum += 1

            # process this mob
            actionAttribs = []
            if 'a' in actionBitVectorArg: actionAttribs.append('special')
            if 'b' in actionBitVectorArg: actionAttribs.append('sentinel')
            if 'c' in actionBitVectorArg: actionAttribs.append('scavenger')
            if 'd' in actionBitVectorArg: actionAttribs.append('isnpc')
            if 'e' in actionBitVectorArg: actionAttribs.append('aware')
            if 'f' in actionBitVectorArg: actionAttribs.append('aggressive')
            if 'g' in actionBitVectorArg: actionAttribs.append('stayzone')
            if 'h' in actionBitVectorArg: actionAttribs.append('wimpy')
            if 'i' in actionBitVectorArg: actionAttribs.append('aggrevil')
            if 'j' in actionBitVectorArg: actionAttribs.append('aggrgood')
            if 'k' in actionBitVectorArg: actionAttribs.append('aggrneutral')
            if 'l' in actionBitVectorArg: actionAttribs.append('memory')
            if 'm' in actionBitVectorArg: actionAttribs.append('helper')
            if 'n' in actionBitVectorArg: actionAttribs.append('nocharm')
            if 'o' in actionBitVectorArg: actionAttribs.append('nosummon')
            if 'p' in actionBitVectorArg: actionAttribs.append('nosleep')
            if 'q' in actionBitVectorArg: actionAttribs.append('nobash')
            if 'r' in actionBitVectorArg: actionAttribs.append('noblind')

            affectAttribs = []
            if 'a' in affectBitVectorArg: affectAttribs.append('blind')
            if 'b' in affectBitVectorArg: affectAttribs.append('invisible')
            if 'c' in affectBitVectorArg: affectAttribs.append('detectalign')
            if 'd' in affectBitVectorArg: affectAttribs.append('detectinvis')
            if 'e' in affectBitVectorArg: affectAttribs.append('detectmagic')
            if 'f' in affectBitVectorArg: affectAttribs.append('senselife')
            if 'g' in affectBitVectorArg: affectAttribs.append('waterwalk')
            if 'h' in affectBitVectorArg: affectAttribs.append('sanctuary')
            if 'i' in affectBitVectorArg: affectAttribs.append('group')
            if 'j' in affectBitVectorArg: affectAttribs.append('curse')
            if 'k' in affectBitVectorArg: affectAttribs.append('infravision')
            if 'l' in affectBitVectorArg: affectAttribs.append('poison')
            if 'm' in affectBitVectorArg: affectAttribs.append('protectevil')
            if 'n' in affectBitVectorArg: affectAttribs.append('protectgood')
            if 'o' in affectBitVectorArg: affectAttribs.append('sleep')
            if 'p' in affectBitVectorArg: affectAttribs.append('notrack')
            if 's' in affectBitVectorArg: affectAttribs.append('sneak')
            if 't' in affectBitVectorArg: affectAttribs.append('hide')
            if 'v' in affectBitVectorArg: affectAttribs.append('charm')

            pos = {'0': 'dead',
                   '1': 'mortallywounded',
                   '2': 'incapacitated',
                   '3': 'stunned',
                   '4': 'sleeping',
                   '5': 'resting',
                   '6': 'sitting',
                   '7': 'fighting',
                   '8': 'standing'}
            loadArg = pos[loadArg]
            defaultPosArg = pos[defaultPosArg]

            sexArg = {'0': 'n',
                      '1': 'm',
                      '2': 'f'}[sexArg]

            if 'BareHandAttack' in extendedMobArg:
                extendedMobArg['BareHandAttack'] = {'0': 'hit/hits',
                                                    '1': 'sting/stings',
                                                    '2': 'whip/whips',
                                                    '3': 'slash/slashes',
                                                    '4': 'bite/bites',
                                                    '5': 'bludgeon/bludgeons',
                                                    '6': 'crush/crushes',
                                                    '7': 'pound/pounds',
                                                    '8': 'claw/claws',
                                                    '9': 'maul/mauls',
                                                    '10': 'thrash/thrashes',
                                                    '11': 'pierce/pierces',
                                                    '12': 'blast/blasts',
                                                    '13': 'punch/punches',
                                                    '14': 'stab/stabs'}[extendedMobArg['BareHandAttack']]

            mob = SimpleNamespace(
                circle_vnum=int(vNumArg),
                alignment=int(alignmentArg),
                type=typeArg,
                level=int(levelArg),
                thac0=int(thacoArg),
                ac=int(acArg),
                maxhp_dice=maxhpArg,
                barehanddmg_dice=bareHandDmgArg,
                gold=int(goldArg),
                xp=int(xpArg),
                loadposition=loadArg,
                defaultposition=defaultPosArg,
                gender=sexArg,
                aliases=list(aliasArg),   # ordered, the first is the best
                shortdesc=shortDescArg.replace("\n", " ") or None,
                longdesc=longDescArg.replace("\n", " ") or None,
                detaileddesc=detailedDescArg.replace("\n", " ") or None,
                actions=set(actionAttribs),
                affection=set(affectAttribs),
                extended={k.lower(): v for k, v in extendedMobArg.items()}
            )
            mobs[mob.circle_vnum] = mob
            readstate = 'vNum'


def parse_all() -> None:
    vfs = VirtualFileSystem(root_package="zones.circledata", everythingtext=True)
    for filename in vfs["world/mob/index"].text.splitlines():
        if filename == "$":
            break
        data = vfs["world/mob/" + filename].text.splitlines()
        parse_file(data)


def get_mobs() -> Dict[int, SimpleNamespace]:
    if not mobs:
        parse_all()
        assert len(mobs) == 569, "all mobs must be loaded"
    return mobs


if __name__ == "__main__":
    mobs = get_mobs()
    print("parsed", len(mobs), "mobs.")
