from BaseClasses import Location
from .data.tournaments import TOURNAMENTS, HAR_NAMES, HAR_STAT_NAMES, PILOT_STAT_NAMES

BASE_ID = 20970000

# ID layout:
#   20971000+  match locations (sequential across all tournaments)
#   20972000+  tournament win locations (one per tournament)
#   20973000+  HAR buy locations  (har * 6 * MAX_HAR_LEVELS + stat * MAX_HAR_LEVELS + level-1)
#   20975000+  pilot stat buy locations (stat * MAX_PILOT_LEVELS + level-1)

MAX_HAR_LEVELS   = 20   # option ceiling
MAX_PILOT_LEVELS = 50   # option ceiling
HAR_BUY_STRIDE   = len(HAR_STAT_NAMES) * MAX_HAR_LEVELS


class OMFLocation(Location):
    game = "One Must Fall: 2097"


def match_location_id(global_idx: int) -> int:
    return BASE_ID + 1000 + global_idx


def tournament_win_id(tournament_idx: int) -> int:
    return BASE_ID + 2000 + tournament_idx


def har_buy_location_id(har_idx: int, stat_idx: int, level: int) -> int:
    return BASE_ID + 3000 + har_idx * HAR_BUY_STRIDE + stat_idx * MAX_HAR_LEVELS + (level - 1)


def pilot_buy_location_id(stat_idx: int, level: int) -> int:
    return BASE_ID + 5000 + stat_idx * MAX_PILOT_LEVELS + (level - 1)


def _build_location_table() -> dict[str, int]:
    """Build the full table of all possible locations (max options)."""
    table: dict[str, int] = {}

    idx = 0
    for t in TOURNAMENTS:
        for pilot_name, _, restricted in t["pilots"]:
            if not restricted:
                table[f"{t['name']} - Beat {pilot_name}"] = match_location_id(idx)
                idx += 1

    for ti, t in enumerate(TOURNAMENTS):
        table[f"Win {t['name']}"] = tournament_win_id(ti)

    for hi, har in enumerate(HAR_NAMES):
        for si, stat in enumerate(HAR_STAT_NAMES):
            for lvl in range(1, MAX_HAR_LEVELS + 1):
                table[f"Buy {har} {stat} Upgrade {lvl}"] = har_buy_location_id(hi, si, lvl)

    for pi, stat in enumerate(PILOT_STAT_NAMES):
        for lvl in range(1, MAX_PILOT_LEVELS + 1):
            table[f"Train {stat} Level {lvl}"] = pilot_buy_location_id(pi, lvl)

    return table


LOCATION_NAME_TO_ID: dict[str, int] = _build_location_table()

LOCATION_GROUPS: dict[str, set[str]] = {
    "Match Checks":      {
        f"{t['name']} - Beat {p}" for t in TOURNAMENTS for p, _, r in t["pilots"] if not r
    },
    "Tournament Checks": {f"Win {t['name']}" for t in TOURNAMENTS},
    "Buy Checks":        {
        f"Buy {har} {stat} Upgrade {lvl}"
        for har in HAR_NAMES for stat in HAR_STAT_NAMES for lvl in range(1, MAX_HAR_LEVELS + 1)
    },
    "Training Checks":   {
        f"Train {stat} Level {lvl}"
        for stat in PILOT_STAT_NAMES for lvl in range(1, MAX_PILOT_LEVELS + 1)
    },
}
