# Pre-parsed from vanilla OMF:2097 TRN files.
# Ordered by registration fee (natural progression order).

from enum import IntEnum


class HARID(IntEnum):
    JAGUAR   = 0
    SHADOW   = 1
    THORN    = 2
    PYROS    = 3
    ELECTRA  = 4
    KATANA   = 5
    SHREDDER = 6
    FLAIL    = 7
    GARGOYLE = 8
    CHRONOS  = 9
    NOVA     = 10
    RANDOM   = 255  # game assigns a random HAR to pilot

HAR_NAMES = [
    "Jaguar", "Shadow", "Thorn", "Pyros", "Electra",
    "Katana", "Shredder", "Flail", "Gargoyle", "Chronos", "Nova",
]

# Enhancement levels per HAR, indexed to match HAR_NAMES.
HAR_ENHANCEMENT_COUNTS = [
    2,  # Jaguar
    3,  # Shadow
    2,  # Thorn
    2,  # Pyros
    2,  # Electra
    3,  # Katana
    2,  # Shredder
    2,  # Flail
    2,  # Gargoyle
    1,  # Chronos
    0,  # Nova
]

HAR_STAT_NAMES = [
    "ARM Power", "LEG Power", "ARM Speed", "LEG Speed", "Armor", "Stun Resist",
]

PILOT_STAT_NAMES = ["Power", "Agility", "Endurance"]

# Pilot tuples: (name, har_id, restricted)
# restricted=True: pilot has secret/conditional appearance requirements.
# These pilots are excluded from generated TRNs and have no AP location.

TOURNAMENTS = [
    {
        "name": "North American Open",
        "filename": "NORTH_AM.TRN",
        "registration_fee": 1500,
        "pilots": [
            ("Raven",        HARID.PYROS,    False),
            ("Crystal",      HARID.JAGUAR,   False),
            ("Ibrahim",      HARID.THORN,    False),
            ("Jack",         HARID.SHADOW,   False),
            ("Dr. Lynn Yarr",HARID.JAGUAR,   False),
            ("Shirro",       HARID.THORN,    False),
            ("Milano",       HARID.JAGUAR,   False),
            ("Jean Paul",    HARID.SHADOW,   False),
            ("Steffan",      HARID.JAGUAR,   False),
            ("Cossette",     HARID.SHADOW,   False),
            # ("ICEMAN",       HARID.SHADOW,   True),  # req_difficulty
            # ("Jazzy",        HARID.JAGUAR,   True),  # req_difficulty
            # ("Christian",    HARID.JAGUAR,   True),  # req_difficulty
            # ("Steel Claw",   HARID.THORN,    True),  # req_difficulty
        ],
    },
    {
        "name": "Katushai Challenge",
        "filename": "KATUSHAI.TRN",
        "registration_fee": 3000,
        "pilots": [
            ("Jaqouline",    HARID.RANDOM,   False),
            ("Prince Vassar",HARID.RANDOM,   False),
            ("Steel Claw",   HARID.FLAIL,    False),
            ("Killian",      HARID.SHADOW,   False),
            ("Marissa",      HARID.RANDOM,   False),
            ("Nathaniel",    HARID.RANDOM,   False),
            ("Ariel",        HARID.GARGOYLE, False),
            ("Eva O'Ryan",   HARID.RANDOM,   False),
            ("Jacob",        HARID.RANDOM,   False),
            ("James",        HARID.ELECTRA,  False),
            ("Steffan",      HARID.JAGUAR,   False),
            # ("Angel",        HARID.GARGOYLE, True),  # req_difficulty
            # ("Selenna",      HARID.KATANA,   True),  # req_difficulty
            # ("Devan Shell",  HARID.FLAIL,    True),  # req_difficulty
        ],
    },
    {
        "name": "WAR Invitational",
        "filename": "WAR.TRN",
        "registration_fee": 5000,
        "pilots": [
            ("Nicoli",       HARID.SHADOW,   False),
            ("Bruce",        HARID.RANDOM,   False),
            ("Selenna",      HARID.KATANA,   False),
            ("Crystal",      HARID.GARGOYLE, False),
            ("Jahrod",       HARID.RANDOM,   False),
            ("Marissa",      HARID.RANDOM,   False),
            ("Christian",    HARID.SHREDDER, False),
            ("Rolland",      HARID.RANDOM,   False),
            ("Scarlet",      HARID.RANDOM,   False),
            ("Milano",       HARID.RANDOM,   False),
            ("Veronica",     HARID.RANDOM,   False),
            # ("Eva Earlong",  HARID.SHADOW,   True),  # req_difficulty
            # ("Bethany",      HARID.SHREDDER, True),  # req_difficulty
            # ("Killian",      HARID.ELECTRA,  True),  # req_difficulty
        ],
    },
    {
        "name": "World Championship",
        "filename": "WORLD.TRN",
        "registration_fee": 10000,
        "pilots": [
            ("Ian Tavares",  HARID.NOVA,     False),
            ("Jaqouline",    HARID.RANDOM,   False),
            ("Bruce",        HARID.RANDOM,   False),
            ("Prince Vassar",HARID.RANDOM,   False),
            ("Selenna",      HARID.KATANA,   False),
            ("Jahrod",       HARID.RANDOM,   False),
            ("Raven",        HARID.KATANA,   False),
            ("Steel Claw",   HARID.FLAIL,    False),
            ("Jack",         HARID.SHREDDER, False),
            ("Christian",    HARID.SHREDDER, False),
            ("Crystal",      HARID.ELECTRA,  False),
            ("Rolland",      HARID.RANDOM,   False),
            ("Eva O'Ryan",   HARID.RANDOM,   False),
            ("Killian",      HARID.SHADOW,   False),
            ("Marissa",      HARID.RANDOM,   False),
            ("Ibrahim",      HARID.THORN,    False),
            ("Scarlet",      HARID.RANDOM,   False),
            ("Milano",       HARID.JAGUAR,   False),
            ("Nathaniel",    HARID.RANDOM,   False),
            ("Veronica",     HARID.RANDOM,   False),
            ("Ariel",        HARID.GARGOYLE, False),
            ("Dr. Lynn Yarr",HARID.GARGOYLE, False),
            ("Shirro",       HARID.FLAIL,    False),
            ("Jacob",        HARID.RANDOM,   False),
            ("Jean Paul",    HARID.CHRONOS,  False),
            ("James",        HARID.ELECTRA,  False),
            ("Steffan",      HARID.JAGUAR,   False),
            ("Cossette",     HARID.CHRONOS,  False),
            # ("ICEMAN",       HARID.KATANA,   True),  # req_difficulty
            # ("Angel",        HARID.ELECTRA,  True),  # req_difficulty
            # ("Nicoli",       HARID.NOVA,     True),  # req_difficulty
            # ("Jazzy",        HARID.SHREDDER, True),  # req_difficulty
            # ("Eva Earlong",  HARID.GARGOYLE, True),  # req_difficulty
            # ("Bethany",      HARID.NOVA,     True),  # req_difficulty
            # ("Devan Shell",  HARID.THORN,    True),  # req_difficulty
        ],
    },
]
