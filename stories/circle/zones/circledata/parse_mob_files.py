"""
Parse CircleMUD mob files.

Based on code by Al Sweigart;
http://inventwithpython.com/blog/2012/03/19/circlemud-data-in-xml-format-for-your-text-adventure-game/
"""

import os
import re
import io

__all__ = ["get_mobs"]

mobs = {}
extendedMobPat = re.compile('(.*?):(.*)')


class Mob(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __repr__(self):
        return "<Mob #%d: %s>" % (self.vnum, self.shortdesc)


def parse_mobs(mobFile):
    with io.open(mobFile) as fp:
        content = [line.strip() for line in fp]

    readState = 'vNum'
    lineNum = 0

    while lineNum < len(content):
        line = content[lineNum]

        if readState == 'vNum':
            if line == '$':
                break  # reached end of file
            vNumArg = line[1:]
            aliasArg = content[lineNum + 1][:-1].split()
            shortDescArg = content[lineNum + 2][:-1]
            readState = 'longdesc'
            lineNum += 3
        elif readState == 'longdesc':
            doneLineNum = lineNum
            while content[doneLineNum] != '~':
                doneLineNum += 1
            longDescArg = '\n'.join(content[lineNum:doneLineNum])
            lineNum = doneLineNum + 1
            readState = 'detaileddesc'
        elif readState == 'detaileddesc':
            doneLineNum = lineNum
            while content[doneLineNum] != '~':
                doneLineNum += 1
            detailedDescArg = '\n'.join(content[lineNum:doneLineNum])
            lineNum = doneLineNum + 1
            readState = 'bitVector'

        elif readState == 'bitVector':
            actionBitVectorArg, affectBitVectorArg, alignmentArg, typeArg = content[lineNum].split()

            lineNum += 1
            readState = 'level'
        elif readState == 'level':
            levelArg, thacoArg, acArg, maxhpArg, bareHandDmgArg = content[lineNum].split()
            goldArg, xpArg = content[lineNum + 1].split()
            loadArg, defaultPosArg, sexArg = content[lineNum + 2].split()
            lineNum += 3

            extendedMobArg = {}
            if not content[lineNum].startswith('#'):
                # this is the extended mob format.

                while content[lineNum] not in ('E', '$'):
                    mo = extendedMobPat.match(content[lineNum])
                    extendedMobArg[mo.group(1).strip()] = mo.group(2).strip()
                    lineNum += 1
                if content[lineNum] != '$':
                    lineNum += 1

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

            mob = Mob(vnum=int(vNumArg),
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
            mobs[mob.vnum] = mob
            readState = 'vNum'


def parse_all():
    # xvfs = vfs.VirtualFileSystem(root_package="zones")
    datadir = os.path.join(os.path.dirname(__file__), "world/mob")
    for mobFile in os.listdir(datadir):
        if not mobFile.endswith('.mob'):
            continue
        parse_mobs(os.path.join(datadir, mobFile))


def get_mobs():
    if not mobs:
        parse_all()
        assert len(mobs) == 569
    return mobs


if __name__ == "__main__":
    mobs = get_mobs()
    print("parsed", len(mobs), "mobs.")
