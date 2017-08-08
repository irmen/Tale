"""
Race definitions.
Races adapted from Dead Souls 2 mudlib (a superset of the races from Nightmare mudlib).

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import enum
from functools import total_ordering
from typing import NamedTuple, Dict


@total_ordering
class BodySize(enum.Enum):
    # The size of a creature's body. You can compare the sizes.
    MICROSCOPIC = ("microscopic", 1)
    MINISCULE = ("miniscule", 2)
    TINY = ("tiny", 3)
    VERY_SMALL = ("very small", 4)
    SMALL = ("small", 5)
    SOMEWHAT_SMALL = ("somewhat small", 6)
    HUMAN_SIZED = ("human sized", 7)
    SOMEWHAT_LARGE = ("somewhat large", 8)
    LARGE = ("large", 9)
    HUGE = ("huge", 10)
    GIGANTIC = ("gigantic", 11)
    VAST = ("vast", 12)

    # noinspection PyInitNewSignature
    def __init__(self, text, order):
        self.text = text
        self.order = order

    def __lt__(self, other):
        if self.__class__ == other.__class__:
            return self.order < other.order
        return NotImplemented

    def __sub__(self, other):
        if self.__class__ == other.__class__:
            return self.order - other.order
        return NotImplemented

    def adjust(self, steps: int) -> 'BodySize':
        order = self.order + steps
        for size in BodySize.__members__.values():      # type: ignore
            if size.order == order:
                return size
        raise LookupError("there is no BodySize for the resulting numeric size")


class BodyType(enum.Enum):
    HUMANOID = "humanoid"
    QUADRUPED = "quadruped"
    BIPED = "biped"
    CHIROPTEROID = "chiropteroid"
    INSECTOID = "insectoid"
    TENTACLED = "tentacled"
    ARTHROPOD = "arthropod"
    CRUSTACEAN = "crustacean"
    PINNIPED = "pinniped"
    CETACEAN = "cetacean"
    FISH = "fish"
    OCTOPOID = "octopoid"
    NEBULOUS = "nebulous"
    CHIMAERA = "chimaera"
    SNAKE = "snake"
    PLANT = "plant"
    TREE = "tree"
    SPECTRAL = "spectral"
    GEOMETRIC = "geometric"
    GELATINOUS = "gelatinous"
    ORB = "orb"
    AVIAN = "avian"
    WINGED_MAN = "winged man"
    SEMI_BIPEDAL = "semi bipedal"
    FLAT = "flat"
    GASTROPOD = "gastropod"


# mass is in KG.

_races = {
    'amphibian': {
        'body': BodyType.QUADRUPED,
        'language': 'Batrachian',
        'mass': 0.4,
        'size': BodySize.VERY_SMALL
    },
    'android': {
        'body': BodyType.HUMANOID,
        'language': 'English',
        'mass': 120.0,
        'size': BodySize.HUMAN_SIZED
    },
    'ape': {
        'body': BodyType.SEMI_BIPEDAL,
        'language': 'Ur',
        'mass': 120.0,
        'size': BodySize.LARGE
    },
    'arachnid': {
        'body': BodyType.INSECTOID,
        'language': 'Arachnid',
        'mass': 0.2,
        'size': BodySize.TINY
    },
    'artrell': {
        'body': BodyType.INSECTOID,
        'language': 'Artrexcian',
        'mass': 48.0,
        'size': BodySize.SOMEWHAT_SMALL
    },
    'avidryl': {
        'body': BodyType.WINGED_MAN,
        'language': 'Avidryl',
        'mass': 60.0,
        'size': BodySize.HUMAN_SIZED
    },
    'balrog': {
        'body': BodyType.WINGED_MAN,
        'language': 'Balrog',
        'mass': 1200.0,
        'size': BodySize.GIGANTIC
    },
    'bat': {
        'body': BodyType.CHIROPTEROID,
        'language': 'Murcielago',
        'mass': 0.4,
        'size': BodySize.VERY_SMALL
    },
    'bear': {
        'body': BodyType.SEMI_BIPEDAL,
        'language': 'Ursine',
        'mass': 160.0,
        'size': BodySize.LARGE
    },
    'bird': {
        'body': BodyType.AVIAN,
        'language': 'Avian',
        'mass': 0.4,
        'size': BodySize.VERY_SMALL
    },
    'blob': {
        'body': BodyType.SNAKE,
        'language': 'Creosote',
        'mass': 1.6,
        'size': BodySize.SMALL
    },
    'bot': {
        'body': BodyType.ORB,
        'language': 'Bocce',
        'mass': 40.0,
        'size': BodySize.SOMEWHAT_SMALL
    },
    'bugbear': {
        'body': BodyType.SEMI_BIPEDAL,
        'language': 'Insectursine',
        'mass': 18.0,
        'size': BodySize.LARGE
    },
    'cat': {
        'body': BodyType.QUADRUPED,
        'language': 'Feline',
        'mass': 4.0,
        'size': BodySize.SMALL
    },
    'centaur': {
        'body': BodyType.SEMI_BIPEDAL,
        'language': 'Centaurian',
        'mass': 120.0,
        'size': BodySize.LARGE
    },
    'chimera': {
        'body': BodyType.CHIMAERA,
        'language': 'Chimerole',
        'mass': 20.0,
        'size': BodySize.LARGE
    },
    'cow': {
        'body': BodyType.QUADRUPED,
        'language': 'Bovine',
        'mass': 160.0,
        'size': BodySize.LARGE
    },
    'dark-elf': {
        'body': BodyType.HUMANOID,
        'language': 'Edhellen',
        'mass': 60.0,
        'size': BodySize.HUMAN_SIZED
    },
    'deer': {
        'body': BodyType.QUADRUPED,
        'language': 'Tier',
        'mass': 120.0,
        'size': BodySize.HUMAN_SIZED
    },
    'demi-god': {
        'body': BodyType.HUMANOID,
        'language': 'Sublime',
        'mass': 80.0,
        'size': BodySize.HUMAN_SIZED
    },
    'demon': {
        'body': BodyType.WINGED_MAN,
        'language': 'Demoniac',
        'mass': 10.0,
        'size': BodySize.SOMEWHAT_LARGE
    },
    'dog': {
        'body': BodyType.QUADRUPED,
        'language': 'Canine',
        'mass': 20.0,
        'size': BodySize.SOMEWHAT_SMALL
    },
    'dragon': {
        'body': BodyType.SEMI_BIPEDAL,
        'language': 'Dragonate',
        'mass': 1600.0,
        'size': BodySize.HUGE
    },
    'dryad': {
        'body': BodyType.HUMANOID,
        'language': 'Vadinho',
        'mass': 4.0,
        'size': BodySize.SMALL
    },
    'dummy': {
        'body': BodyType.HUMANOID,
        'language': 'Common',
        'mass': 200.0,
        'size': BodySize.LARGE
    },
    'dwarf': {
        'body': BodyType.HUMANOID,
        'language': 'Malkierien',
        'mass': 8.0,
        'size': BodySize.SOMEWHAT_SMALL
    },
    'elemental': {
        'body': BodyType.NEBULOUS,
        'language': 'Periodict',
        'mass': 1600.0,
        'size': BodySize.LARGE
    },
    'elephant': {
        'body': BodyType.QUADRUPED,
        'language': 'Pachydermian',
        'mass': 1600.0,
        'size': BodySize.HUGE
    },
    'elf': {
        'body': BodyType.HUMANOID,
        'language': 'Edhellen',
        'mass': 60.0,
        'size': BodySize.HUMAN_SIZED
    },
    'faerie': {
        'body': BodyType.WINGED_MAN,
        'language': 'Elcharean',
        'mass': 0.2,
        'size': BodySize.TINY
    },
    'fish': {
        'body': BodyType.FISH,
        'language': 'Ichthine',
        'mass': 8.0,
        'size': BodySize.SMALL
    },
    'gargoyle': {
        'body': BodyType.WINGED_MAN,
        'language': 'Gargoyleish',
        'mass': 120.0,
        'size': BodySize.SOMEWHAT_SMALL
    },
    'giant': {
        'body': BodyType.HUMANOID,
        'language': 'Loyavenku',
        'mass': 1600.0,
        'size': BodySize.HUGE
    },
    'gnoll': {
        'body': BodyType.HUMANOID,
        'language': 'Kaydoch',
        'mass': 48.0,
        'size': BodySize.SOMEWHAT_SMALL
    },
    'gnome': {
        'body': BodyType.HUMANOID,
        'language': 'Kaydiyee',
        'mass': 0.4,
        'size': BodySize.VERY_SMALL
    },
    'goblin': {
        'body': BodyType.HUMANOID,
        'language': 'Goblinish',
        'mass': 72.0,
        'size': BodySize.HUMAN_SIZED
    },
    'god': {
        'body': BodyType.NEBULOUS,
        'language': 'Divine',
        'mass': 0.0,
        'size': BodySize.LARGE
    },
    'golem': {
        'body': BodyType.HUMANOID,
        'language': 'Emet',
        'mass': 200.0,
        'size': BodySize.LARGE
    },
    'griffin': {
        'body': BodyType.SEMI_BIPEDAL,
        'language': 'Griffinish',
        'mass': 120.0,
        'size': BodySize.LARGE
    },
    'half-elf': {
        'body': BodyType.HUMANOID,
        'language': 'Edhellen',
        'mass': 60.0,
        'size': BodySize.HUMAN_SIZED
    },
    'half-orc': {
        'body': BodyType.HUMANOID,
        'language': 'Tangetto',
        'mass': 80.0,
        'size': BodySize.HUMAN_SIZED
    },
    'halfling': {
        'body': BodyType.HUMANOID,
        'language': 'Duuk',
        'mass': 20.0,
        'size': BodySize.SMALL
    },
    'hobbit': {
        'body': BodyType.HUMANOID,
        'language': 'Hoboken',
        'mass': 20.0,
        'size': BodySize.SMALL
    },
    'horse': {
        'body': BodyType.QUADRUPED,
        'language': 'Equine',
        'mass': 240.0,
        'size': BodySize.LARGE
    },
    'human': {
        'body': BodyType.HUMANOID,
        'language': 'English',
        'mass': 72.0,
        'size': BodySize.HUMAN_SIZED
    },
    'insect': {
        'body': BodyType.INSECTOID,
        'language': 'Insectoid',
        'mass': 0.04,
        'size': BodySize.MINISCULE
    },
    'kender': {
        'body': BodyType.HUMANOID,
        'language': 'Kendrall',
        'mass': 32.0,
        'size': BodySize.SOMEWHAT_SMALL
    },
    'klingon': {
        'body': BodyType.HUMANOID,
        'language': 'Tlhinghan',
        'mass': 100.0,
        'size': BodySize.SOMEWHAT_LARGE
    },
    'kobold': {
        'body': BodyType.HUMANOID,
        'language': 'Yeik',
        'mass': 52.0,
        'size': BodySize.SOMEWHAT_SMALL
    },
    'lizard': {
        'body': BodyType.QUADRUPED,
        'language': 'Reptilian',
        'mass': 0.4,
        'size': BodySize.VERY_SMALL
    },
    'mech': {
        'body': BodyType.HUMANOID,
        'language': 'English',
        'mass': 400.0,
        'size': BodySize.HUGE
    },
    'nymph': {
        'body': BodyType.HUMANOID,
        'language': 'Nymal',
        'mass': 5.6,
        'size': BodySize.SOMEWHAT_SMALL
    },
    'ogre': {
        'body': BodyType.HUMANOID,
        'language': 'Shangtai',
        'mass': 160.0,
        'size': BodySize.LARGE
    },
    'orc': {
        'body': BodyType.HUMANOID,
        'language': 'Tangetto',
        'mass': 88.0,
        'size': BodySize.SOMEWHAT_LARGE
    },
    'pegasus': {
        'body': BodyType.QUADRUPED,
        'language': 'Voloquine',
        'mass': 120.0,
        'size': BodySize.LARGE
    },
    'pig': {
        'body': BodyType.QUADRUPED,
        'language': 'Porcine',
        'mass': 60.0,
        'size': BodySize.SOMEWHAT_SMALL
    },
    'plant': {
        'body': BodyType.PLANT,
        'language': 'Vegetal',
        'mass': 0.4,
        'size': BodySize.VERY_SMALL
    },
    'primate': {
        'body': BodyType.SEMI_BIPEDAL,
        'language': 'Proto',
        'mass': 60.0,
        'size': BodySize.SMALL
    },
    'replicant': {
        'body': BodyType.HUMANOID,
        'language': 'English',
        'mass': 72.0,
        'size': BodySize.HUMAN_SIZED
    },
    'rodent': {
        'body': BodyType.QUADRUPED,
        'language': 'Rodentian',
        'mass': 0.4,
        'size': BodySize.VERY_SMALL
    },
    'satyr': {
        'body': BodyType.HUMANOID,
        'language': 'Wulinaxian',
        'mass': 6.0,
        'size': BodySize.HUMAN_SIZED
    },
    'sheep': {
        'body': BodyType.QUADRUPED,
        'language': 'Ovine',
        'mass': 40.0,
        'size': BodySize.SOMEWHAT_SMALL
    },
    'slug': {
        'body': BodyType.GASTROPOD,
        'language': 'Clavering',
        'mass': 0.12,
        'size': BodySize.VERY_SMALL
    },
    'snake': {
        'body': BodyType.SNAKE,
        'language': 'Herpetian',
        'mass': 1.6,
        'size': BodySize.SMALL
    },
    'strider': {
        'body': BodyType.HUMANOID,
        'language': 'English',
        'mass': 400.0,
        'size': BodySize.HUGE
    },
    'tortoise': {
        'body': BodyType.QUADRUPED,
        'language': 'Tortois',
        'mass': 3.6,
        'size': BodySize.SMALL
    },
    'tree': {
        'body': BodyType.TREE,
        'language': 'Entish',
        'mass': 160.0,
        'size': BodySize.LARGE
    },
    'troll': {
        'body': BodyType.HUMANOID,
        'language': 'Murdoch',
        'mass': 8.0,
        'size': BodySize.HUMAN_SIZED
    },
    'unicorn': {
        'body': BodyType.QUADRUPED,
        'language': 'Cornequine',
        'mass': 160.0,
        'size': BodySize.LARGE
    },
    'vehicle': {
        'body': BodyType.ORB,
        'language': 'Bocce',
        'mass': 40.0,
        'size': BodySize.LARGE
    },
    'viper': {
        'body': BodyType.SNAKE,
        'language': 'Aspish',
        'mass': 1.2,
        'size': BodySize.SMALL
    },
    'vulcan': {
        'body': BodyType.HUMANOID,
        'language': 'Vulcan',
        'mass': 60.0,
        'size': BodySize.HUMAN_SIZED
    },
    'wraith': {
        'body': BodyType.SPECTRAL,
        'language': 'Revenant',
        'mass': 4.0,
        'size': BodySize.SOMEWHAT_LARGE
    }
}


# Races that can be chosen by players. Can be changed in story configuration.
playable_races = {'human', 'dwarf', 'elf', 'dark-elf', 'half-elf', 'half-orc', 'halfling', 'orc', 'goblin', 'hobbit'}

Flags = NamedTuple("Flags", [("flying", bool),
                             ("limbless", bool),
                             ("nonbiting", bool),
                             ("swimming", bool),
                             ("nonmeat", bool),
                             ("playable", bool)])

Race = NamedTuple("Race", [("name", str),
                           ("body", BodyType),
                           ("language", str),
                           ("mass", float),
                           ("size", BodySize),
                           ("flags", Flags)])


races = {}  # type: Dict[str, Race]


def _create_race_defs() -> None:
    flying_races = {'avidryl', 'bat', 'bird', 'bot', 'demon', 'dragon', 'faerie',
                    'gargoyle', 'griffin', 'insect', 'pegasus', 'vehicle', 'wraith'}
    limbless_races = {'blob', 'elemental', 'fish', 'plant', 'slug', 'snake', 'tree', 'vehicle', 'viper'}
    nonbiting_races = {'android', 'bot', 'cow', 'dark-elf', 'deer', 'dummy', 'elemental',
                       'elf', 'faerie', 'god', 'golem', 'mech', 'plant', 'strider', 'vehicle', 'vulcan'}
    swimming_races = {'amphibian', 'android', 'artrell', 'bear', 'bot', 'bugbear', 'cat', 'dark-elf',
                      'demi-god', 'demon', 'dragon', 'elephant', 'elf', 'fish', 'giant', 'gnoll',
                      'gnome', 'goblin', 'god', 'half-elf', 'halfling', 'hobbit', 'human', 'kender',
                      'lizard', 'nymph', 'replicant', 'rodent', 'troll', 'vehicle', 'vulcan'}
    nonmeat_races = {'android', 'balrog', 'bot', 'dummy', 'elemental', 'god', 'golem', 'mech',
                     'plant', 'strider', 'tree', 'vehicle', 'wraith'}

    global races
    for race, attrs in _races.items():
        flags = Flags(flying=race in flying_races,
                      limbless=race in limbless_races,
                      nonbiting=race in nonbiting_races,
                      swimming=race in swimming_races,
                      nonmeat=race in nonmeat_races,
                      playable=race in playable_races)
        races[race] = Race(name=race, body=attrs["body"], language=attrs["language"],           # type: ignore
                           mass=attrs["mass"], size=attrs["size"], flags=flags)
    _all_races = set(_races)
    assert len(swimming_races - _all_races) == 0
    assert len(flying_races - _all_races) == 0
    assert len(limbless_races - _all_races) == 0
    assert len(nonbiting_races - _all_races) == 0
    assert len(nonmeat_races - _all_races) == 0
    assert len(playable_races - _all_races) == 0


_create_race_defs()
del _create_race_defs
