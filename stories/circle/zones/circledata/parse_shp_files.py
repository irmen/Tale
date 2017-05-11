"""
Parse CirleMUD shop files.

Based on code by Al Sweigart;
http://inventwithpython.com/blog/2012/03/19/circlemud-data-in-xml-format-for-your-text-adventure-game/
"""

import pathlib
import re
from types import SimpleNamespace
from typing import Dict

__all__ = ["get_shops"]


extendedMobPat = re.compile('(.*?):(.*)')
shops = {}   # type: Dict[int, SimpleNamespace]


def parse_file(shpfile: pathlib.Path) -> None:
    with shpfile.open() as fp:
        content = fp.readlines()

    content = [line.strip() for line in content][1:]  # skip the first "CircleMUD v3.0 Shop File~" line

    lineNum = 0

    while lineNum < len(content):
        line = content[lineNum]

        if line == '$~':
            break  # reached end of file
        vNumArg = line[1:-1]
        lineNum += 1

        forSaleVNumArg = []
        # read in the items for sale
        while content[lineNum] != '-1':
            forSaleVNumArg.append(content[lineNum])
            lineNum += 1
        lineNum += 1  # skip "-1" line

        profitWhenSellingArg = content[lineNum]
        lineNum += 1
        profitWhenBuyingArg = content[lineNum]
        lineNum += 1

        buyTypeArg = []
        while content[lineNum] != '-1':
            if content[lineNum] == 'LIQ CONTAINER':
                buyTypeArg.append('drinkcontainer')
            else:
                buyTypeArg.append(content[lineNum].lower())
            lineNum += 1
        lineNum += 1  # skip "-1" line

        playertobuydoesnotexistArg = content[lineNum][3:-1]
        lineNum += 1
        playertoselldoesnotexistArg = content[lineNum][3:-1]
        lineNum += 1
        shopdoesnotbuyArg = content[lineNum][3:-1]
        lineNum += 1
        shopcannotaffordArg = content[lineNum][3:-1]
        lineNum += 1
        playercannotaffordArg = content[lineNum][3:-1]
        lineNum += 1
        shopsolditemArg = content[lineNum][3:-1]
        lineNum += 1
        shopboughtitemArg = content[lineNum][3:-1]
        lineNum += 1
        temperArg = content[lineNum]
        lineNum += 1

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

        bitvector = content[lineNum]
        lineNum += 1
        willFightArg = bitvector in ('1', '3')
        willBankArg = bitvector in ('2', '3')

        shopkeeperMobArg = content[lineNum]
        lineNum += 1
        wontdealwithArg = content[lineNum]
        lineNum += 1

        shopRoomsArg = []
        while content[lineNum] != '-1':
            shopRoomsArg.append(content[lineNum])
            lineNum += 1
        lineNum += 1  # skip "-1" line

        open1Arg = content[lineNum]
        lineNum += 1
        close1Arg = content[lineNum]
        lineNum += 1
        open2Arg = content[lineNum]
        lineNum += 1
        close2Arg = content[lineNum]
        lineNum += 1

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
            vnum=int(vNumArg),
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
        shops[shop.vnum] = shop


def parse_all() -> None:
    datadir = pathlib.Path(__file__).parent / "world/shp"
    for file in datadir.glob("*.shp"):
        parse_file(file)


def get_shops() -> Dict[int, SimpleNamespace]:
    if not shops:
        parse_all()
        assert len(shops) == 46
    return shops


if __name__ == "__main__":
    shops = get_shops()
    print("parsed", len(shops), "shops.")
