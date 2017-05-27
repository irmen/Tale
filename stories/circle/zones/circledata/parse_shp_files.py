"""
Parse CirleMUD shop files.

Initially based on code by Al Sweigart, but heavily modified since:
http://inventwithpython.com/blog/2012/03/19/circlemud-data-in-xml-format-for-your-text-adventure-game/
"""

import re
from types import SimpleNamespace
from typing import Dict, List
from tale.vfs import VirtualFileSystem


__all__ = ["get_shops"]


extendedMobPat = re.compile('(.*?):(.*)')
shops = {}   # type: Dict[int, SimpleNamespace]


def parse_file(content):
    content = [line.strip() for line in content][1:]  # skip the first "CircleMUD v3.0 Shop File~" line
    linenum = 0

    while linenum < len(content):
        line = content[linenum]

        if line == '$~':
            break  # reached end of file
        vNumArg = line[1:-1]
        linenum += 1

        forSaleVNumArg = []
        # read in the items for sale
        while content[linenum] != '-1':
            forSaleVNumArg.append(content[linenum])
            linenum += 1
        linenum += 1  # skip "-1" line

        profitWhenSellingArg = content[linenum]
        linenum += 1
        profitWhenBuyingArg = content[linenum]
        linenum += 1

        buyTypeArg = []
        while content[linenum] != '-1':
            if content[linenum] == 'LIQ CONTAINER':
                buyTypeArg.append('drinkcontainer')
            else:
                buyTypeArg.append(content[linenum].lower())
            linenum += 1
        linenum += 1  # skip "-1" line

        playertobuydoesnotexistArg = content[linenum][3:-1]
        linenum += 1
        playertoselldoesnotexistArg = content[linenum][3:-1]
        linenum += 1
        shopdoesnotbuyArg = content[linenum][3:-1]
        linenum += 1
        shopcannotaffordArg = content[linenum][3:-1]
        linenum += 1
        playercannotaffordArg = content[linenum][3:-1]
        linenum += 1
        shopsolditemArg = content[linenum][3:-1]
        linenum += 1
        shopboughtitemArg = content[linenum][3:-1]
        linenum += 1
        temperArg = content[linenum]
        linenum += 1

        if shopboughtitemArg == 'Oops - %d a minor bug - please report!':
            shopboughtitemArg = ''

        if temperArg == '-1':
            temperArg = None
        elif temperArg == '0':
            temperArg = 'puke'
        elif temperArg == '1':
            temperArg = 'smoke'
        else:
            temperArg = None

        bitvector = content[linenum]
        linenum += 1
        willFightArg = bitvector in ('1', '3')
        willBankArg = bitvector in ('2', '3')

        shopkeeperMobArg = content[linenum]
        linenum += 1
        wontdealwithArg = content[linenum]
        linenum += 1

        shopRoomsArg = []
        while content[linenum] != '-1':
            shopRoomsArg.append(content[linenum])
            linenum += 1
        linenum += 1  # skip "-1" line

        open1Arg = content[linenum]
        linenum += 1
        close1Arg = content[linenum]
        linenum += 1
        open2Arg = content[linenum]
        linenum += 1
        close2Arg = content[linenum]
        linenum += 1

        # don't show open2 and close2 if they are both 0
        if open2Arg == '0' and close2Arg == '0':
            open2Arg = None
            close2Arg = None

        wontdealattr = set()
        wontdealwithArg = int(wontdealwithArg)
        if wontdealwithArg >= 64:
            wontdealwithArg -= 64
            wontdealattr.add('warrior')
        if wontdealwithArg >= 32:
            wontdealwithArg -= 32
            wontdealattr.add('thief')
        if wontdealwithArg >= 16:
            wontdealwithArg -= 16
            wontdealattr.add('cleric')
        if wontdealwithArg >= 8:
            wontdealwithArg -= 8
            wontdealattr.add('magicuser')
        if wontdealwithArg >= 4:
            wontdealwithArg -= 4
            wontdealattr.add('neutral')
        if wontdealwithArg >= 2:
            wontdealwithArg -= 2
            wontdealattr.add('evil')
        if wontdealwithArg >= 1:
            wontdealwithArg -= 1
            wontdealattr.add('good')

        shop = SimpleNamespace(
            circle_vnum=int(vNumArg),
            sellprofit=float(profitWhenSellingArg),
            buyprofit=float(profitWhenBuyingArg),
            shopkeeper=int(shopkeeperMobArg),
            fights=willFightArg,
            banks=willBankArg,
            open1=int(open1Arg),
            close1=int(close1Arg),
            open2=int(open2Arg) if open2Arg else None,
            close2=int(close2Arg) if close2Arg else None,
            forsale={int(vnum) for vnum in forSaleVNumArg},
            willbuy=set(buyTypeArg),
            msg_playercantbuy=playertobuydoesnotexistArg,
            msg_playercantsell=playertoselldoesnotexistArg,
            msg_shopdoesnotbuy=shopdoesnotbuyArg,
            msg_shopcantafford=shopcannotaffordArg,
            msg_playercantafford=playercannotaffordArg,
            msg_shopsolditem=shopsolditemArg,
            msg_shopboughtitem=shopboughtitemArg,
            msg_temper=temperArg,
            rooms={int(vnum) for vnum in shopRoomsArg},
            wontdealwith=wontdealattr
        )
        shops[shop.circle_vnum] = shop


def parse_all() -> None:
    vfs = VirtualFileSystem(root_package="zones.circledata", everythingtext=True)
    for filename in vfs["world/shp/index"].text.splitlines():
        if filename == "$":
            break
        data = vfs["world/shp/" + filename].text.splitlines()
        parse_file(data)


def get_shops() -> Dict[int, SimpleNamespace]:
    if not shops:
        parse_all()
        assert len(shops) == 46, "all shops must be loaded"
    return shops


if __name__ == "__main__":
    shops = get_shops()
    print("parsed", len(shops), "shops.")
