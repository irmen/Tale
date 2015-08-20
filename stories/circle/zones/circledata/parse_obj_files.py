"""
Parse CircleMUD obj files.

Based on code by Al Sweigart;
http://inventwithpython.com/blog/2012/03/19/circlemud-data-in-xml-format-for-your-text-adventure-game/
"""

import os
import re
import io

__all__ = ["get_objs"]


class Obj(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __repr__(self):
        return "<Obj #%d: %s>" % (self.vnum, self.shortdesc)


objs = {}
extendedMobPat = re.compile('(.*?):(.*)')


def parse_file(objFile):
    with io.open(objFile) as fp:
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
            #if shortDescArg == 'a scroll of recall':
            #    pass#import pdb; pdb.set_trace()
            longDescArg = content[lineNum + 3][:-1]
            actionDescArg = content[lineNum + 4][:-1]
            readState = 'bitVector'
            lineNum += 5
        #elif readState == 'longdesc':
        #    doneLineNum = lineNum
        #    while content[doneLineNum] != '~':
        #        doneLineNum += 1
        #    longDescArg = '\n'.join(content[lineNum:doneLineNum])
        #    lineNum = doneLineNum + 1
        #    readState = 'actiondesc'
        #elif readState == 'actiondesc':
        #    doneLineNum = lineNum
        #    while content[doneLineNum] != '~':
        #        doneLineNum += 1
        #    actionDescArg = '\n'.join(content[lineNum:doneLineNum])
        #    lineNum = doneLineNum + 1
        #    readState = 'bitVector'

        elif readState == 'bitVector':
            typeFlagArg, effectsBitVectorArg, wearBitVectorArg = content[lineNum].split()
            value0Arg, value1Arg, value2Arg, value3Arg = content[lineNum + 1].split()
            weightArg, costArg, rentArg = content[lineNum + 2].split()
            lineNum += 3
            readState = 'extradesc'
        elif readState == 'extradesc':
            extendedArg = []
            affectArg = {}
            while not content[lineNum].startswith('#') and not content[lineNum].startswith('$'):
                # this is the extended mob format.
                if content[lineNum] == 'E':
                    lineNum += 1
                    #import pdb; pdb.set_trace()
                    doneLineNum = lineNum
                    while content[doneLineNum] != '~':
                        doneLineNum += 1
                    extendedArg.append((content[lineNum][:-1].split(), '\n'.join(content[lineNum + 1:doneLineNum])))  # keywords list, desc string
                    lineNum = doneLineNum + 1

                elif content[lineNum] == 'A':
                    lineNum += 1
                    affectline = content[lineNum].split()
                    affectArg[affectline[0]] = affectline[1]
                    lineNum += 1

            # process this obj
            typeFlagArg = {'1': 'light',
                           '2': 'scroll',
                           '3': 'wand',
                           '4': 'staff',
                           '5': 'weapon',
                           '6': 'fireweapon',
                           '7': 'missile',
                           '8': 'treasure',
                           '9': 'armor',
                           '10': 'potion',
                           '11': 'worn',
                           '12': 'other',
                           '13': 'trash',
                           '14': 'trap',
                           '15': 'container',
                           '16': 'note',
                           '17': 'drinkcontainer',
                           '18': 'key',
                           '19': 'food',
                           '20': 'money',
                           '21': 'pen',
                           '22': 'boat',
                           '23': 'fountain'}[typeFlagArg]

            effectAttribs = []
            if 'a' in effectsBitVectorArg: effectAttribs.append('glow')
            if 'b' in effectsBitVectorArg: effectAttribs.append('hum')
            if 'c' in effectsBitVectorArg: effectAttribs.append('norent')
            if 'd' in effectsBitVectorArg: effectAttribs.append('nodonate')
            if 'e' in effectsBitVectorArg: effectAttribs.append('noinvis')
            if 'f' in effectsBitVectorArg: effectAttribs.append('invis')
            if 'g' in effectsBitVectorArg: effectAttribs.append('cantenchant')
            if 'h' in effectsBitVectorArg: effectAttribs.append('nodrop')
            if 'i' in effectsBitVectorArg: effectAttribs.append('bless')
            if 'j' in effectsBitVectorArg: effectAttribs.append('antigood')
            if 'k' in effectsBitVectorArg: effectAttribs.append('antievil')
            if 'l' in effectsBitVectorArg: effectAttribs.append('antineutral')
            if 'm' in effectsBitVectorArg: effectAttribs.append('antimagicuser')
            if 'n' in effectsBitVectorArg: effectAttribs.append('anticleric')
            if 'o' in effectsBitVectorArg: effectAttribs.append('antithief')
            if 'p' in effectsBitVectorArg: effectAttribs.append('antiwarrior')
            if 'q' in effectsBitVectorArg: effectAttribs.append('nosell')

            wearAttribs = []
            if wearBitVectorArg.isdigit():
                wearBitVectorArg = int(wearBitVectorArg)
                # on a side note, why did they use a bit vector for this? Can you wear a piece of armor on your feet and head?
                # It seems like they just needed the "take" bit to be set or not. I'm not sure why a piece of armor wouldn't be takeable,
                # or why they make "takeable" specific to armors instead of all items.
                if wearBitVectorArg >= 16384:
                    wearBitVectorArg -= 16384
                    wearAttribs.append('hold')
                if wearBitVectorArg >= 8192:
                    wearBitVectorArg -= 8192
                    wearAttribs.append('wield')
                if wearBitVectorArg >= 4096:
                    wearBitVectorArg -= 4096
                    wearAttribs.append('wrist')
                if wearBitVectorArg >= 2048:
                    wearBitVectorArg -= 2048
                    wearAttribs.append('waist')
                if wearBitVectorArg >= 1024:
                    wearBitVectorArg -= 1024
                    wearAttribs.append('about')
                if wearBitVectorArg >= 512:
                    wearBitVectorArg -= 512
                    wearAttribs.append('shield')
                if wearBitVectorArg >= 256:
                    wearBitVectorArg -= 256
                    wearAttribs.append('arms')
                if wearBitVectorArg >= 128:
                    wearBitVectorArg -= 128
                    wearAttribs.append('hands')
                if wearBitVectorArg >= 64:
                    wearBitVectorArg -= 64
                    wearAttribs.append('feet')
                if wearBitVectorArg >= 32:
                    wearBitVectorArg -= 32
                    wearAttribs.append('legs')
                if wearBitVectorArg >= 16:
                    wearBitVectorArg -= 16
                    wearAttribs.append('head')
                if wearBitVectorArg >= 8:
                    wearBitVectorArg -= 8
                    wearAttribs.append('body')
                if wearBitVectorArg >= 4:
                    wearBitVectorArg -= 4
                    wearAttribs.append('neck')
                if wearBitVectorArg >= 2:
                    wearBitVectorArg -= 2
                    wearAttribs.append('finger')
                if wearBitVectorArg < 1:
                    #wearBitVectorArg -= 1
                    wearAttribs.append('canttake')
            else:
                if 'a' in wearBitVectorArg: wearAttribs.append('takeable')
                if 'b' in wearBitVectorArg: wearAttribs.append('finger')
                if 'c' in wearBitVectorArg: wearAttribs.append('neck')
                if 'd' in wearBitVectorArg: wearAttribs.append('body')
                if 'e' in wearBitVectorArg: wearAttribs.append('head')
                if 'f' in wearBitVectorArg: wearAttribs.append('legs')
                if 'g' in wearBitVectorArg: wearAttribs.append('feet')
                if 'h' in wearBitVectorArg: wearAttribs.append('hands')
                if 'i' in wearBitVectorArg: wearAttribs.append('arms')
                if 'j' in wearBitVectorArg: wearAttribs.append('shield')
                if 'k' in wearBitVectorArg: wearAttribs.append('about')
                if 'l' in wearBitVectorArg: wearAttribs.append('waist')
                if 'm' in wearBitVectorArg: wearAttribs.append('wrist')
                if 'n' in wearBitVectorArg: wearAttribs.append('wield')
                if 'o' in wearBitVectorArg: wearAttribs.append('hold')

            valueDefs = {'light': [None, None, 'capacity', None],
                         'scroll': ['level', 'spell1', 'spell2', 'spell3'],
                         'wand': ['level', 'capacity', 'remaining', 'spell'],
                         'staff': ['level', 'capacity', 'remaining', 'spell'],
                         'weapon': [None, 'numdice', 'sizedice', 'damagetype'],
                         'fireweapon': [None, None, None, None],
                         'missile': [None, None, None, None],
                         'treasure': [None, None, None, None],
                         'armor': ['ac', None, None, None],
                         'potion': ['level', 'spell1', 'spell2', 'spell3'],
                         'worn': [None, None, None, None],
                         'other': [None, None, None, None],
                         'trash': [None, None, None, None],
                         'trap': [None, None, None, None],
                         'container': ['capacity', 'containertype', 'keynum', None],
                         'note': ['language', None, None, None],
                         'drinkcontainer': ['capacity', 'remaining', 'drinktype', 'ispoisoned'],
                         'key': [None, None, None, None],
                         'food': ['filling', None, None, 'ispoisoned'],
                         'money': ['amount', None, None, None],
                         'pen': [None, None, None, None],
                         'boat': [None, None, None, None],
                         'fountain': ['capacity', 'remaining', 'drinktype', 'ispoisoned']}
            drinkTypeMap = {'0': 'water',
                            '1': 'beer',
                            '2': 'wine',
                            '3': 'ale',
                            '4': 'darkale',
                            '5': 'whisky',
                            '6': 'lemonade',
                            '7': 'firebreath',
                            '8': 'localspecial',
                            '9': 'slime',
                            '10': 'milk',
                            '11': 'tea',
                            '12': 'coffee',
                            '13': 'blood',
                            '14': 'saltwater',
                            '15': 'clearwater'}
            damagetypeMap = {
                '0': 'hit/hits',
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
                '14': 'stab/stabs'}

            affectTypes = {
                '0': 'none',
                '1': 'strength',
                '2': 'dexterity',
                '3': 'intelligence',
                '4': 'wisdom',
                '5': 'constitution',
                '6': 'charisma',
                '7': 'class',
                '8': 'level',
                '9': 'age',
                '10': 'charweight',
                '11': 'charheight',
                '12': 'mana',
                '13': 'hit',
                '14': 'move',
                '15': 'gold',
                '16': 'experience',
                '17': 'ac',
                '18': 'hitroll',
                '19': 'damageroll',
                '20': 'saveparalysis',
                '21': 'saverods',
                '22': 'savepetrification',
                '23': 'savebreath',
                '24': 'savespell'}

            spellNumbers = {'28': 'heal', '29': 'invisible', '26': 'fireball', '32': 'magic missile', '24': 'enchant weapon', '25': 'energy drain',
                            '23': 'earthquake', '27': 'harm', '20': 'detect magic', '21': 'detect poison', '22': 'dispel evil', '49': 'group recall',
                            '46': 'dispel good', '47': 'group armor', '44': 'sense life', '45': 'animate dead', '42': 'word of recall', '43': 'remove poison',
                            '40': 'summon', '41': 'ventriloquate', '1': 'armor', '3': 'bless', '2': 'teleport', '5': 'burning hands', '4': 'blindness',
                            '7': 'charm', '6': 'call lightning', '9': 'clone', '8': 'chill touch', '201': 'identify', '39': 'strength', '12': 'create food',
                            '11': 'control weather', '10': 'color spray', '13': 'create water', '38': 'sleep', '15': 'cure critic', '14': 'cure blind',
                            '17': 'curse', '16': 'cure light', '19': 'detect invis', '18': 'detect align', '31': 'locate object', '30': 'lightning bolt',
                            '51': 'waterwalk', '36': 'sanctuary', '35': 'remove curse', '34': 'prot from evil', '33': 'poison', '37': 'shocking grasp',
                            '48': 'group heal', '50': 'infravision'}

            obj = Obj(
                vnum=int(vNumArg),
                aliases=list(aliasArg),  # ordered, the first is the best
                type=typeFlagArg,
                weight=int(weightArg),
                cost=int(costArg),
                rent=int(rentArg),
                shortdesc=shortDescArg.replace("\n", " ") or None,
                longdesc=longDescArg.replace("\n", " ") or None,
                # actiondesc=actionDescArg or None,  # there is never an action desc??
                effects=set(effectAttribs),
                wear=set(wearAttribs),
            )

            if valueDefs[typeFlagArg] != [None, None, None, None]:
                #import pdb; pdb.set_trace()
                typespecificArg = {}
                for i in range(4):
                    key = valueDefs[typeFlagArg][i]
                    value = (value0Arg, value1Arg, value2Arg, value3Arg)[i]
                    if key is not None:
                        if key == 'damagetype':
                            value = damagetypeMap[value]
                        elif key == 'containertype':
                            value = int(value)
                            if value >= 8:
                                typespecificArg['locked'] = True
                                value -= 8
                            if value >= 4:
                                typespecificArg['closed'] = True
                                value -= 4
                            if value >= 2:
                                typespecificArg['pickproof'] = True
                                value -= 2
                            if value >= 1:
                                typespecificArg['closeable'] = True
                                value -= 1
                            key = None
                        elif key == 'keynum' and (value == '0' or value == '-1'):
                            key = None
                        elif key == 'ispoisoned':
                            if value == '0':
                                key = None  # don't put in "ispoisoned" attribute if not poisoned.
                            else:
                                value = True
                        elif key in ('spell1', 'spell2', 'spell3', 'spell'):
                            if value == '-1':
                                key = None
                            else:
                                value = spellNumbers[value]
                        elif key == 'drinktype':
                            value = drinkTypeMap[value]

                        if key is not None:
                            try:
                                typespecificArg[key] = int(value)
                            except ValueError:
                                typespecificArg[key] = value

                obj.typespecific = typespecificArg or {}

            obj.extradesc = []
            for arg in extendedArg:
                desc = {}
                desc["keywords"] = set(arg[0])
                desc["text"] = arg[1].replace("\n", " ")
                obj.extradesc.append(desc)
            obj.affects = {}
            for k, v in affectArg.items():
                obj.affects[affectTypes[k]] = int(v)

            objs[obj.vnum] = obj
            readState = 'vNum'


def parse_all():
    datadir = os.path.join(os.path.dirname(__file__), "world/obj")
    for filename in os.listdir(datadir):
        if not filename.endswith('.obj'):
            continue
        parse_file(os.path.join(datadir, filename))


def get_objs():
    if not objs:
        parse_all()
        assert len(objs) == 678
    return objs


if __name__ == "__main__":
    objs = get_objs()
    print("parsed", len(objs), "objs.")
