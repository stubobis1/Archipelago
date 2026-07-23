from BaseClasses import Item, ItemClassification
from .data.tournaments import HAR_NAMES, HAR_STAT_NAMES, PILOT_STAT_NAMES, HAR_ENHANCEMENT_COUNTS

BASE_ID = 20970000

# ID layout:
#   20970000 – 20970010  HAR unlocks (one per HAR)
#   20970100 – 20970165  HAR stat progressives (11 HARs × 6 stats)
#   20970200 – 20970202  Pilot stat progressives (3 stats)
#   20970300             Money (Small)
#   20970301             Money (Large)
#   20970302             Nothing
#   20970400 – 20970409  HAR enhancement progressives (one ID per HAR with enhancements)


class OMFItem(Item):
    game = "One Must Fall: 2097"


def har_unlock_id(har_idx: int) -> int:
    return BASE_ID + har_idx


def har_stat_item_id(har_idx: int, stat_idx: int) -> int:
    return BASE_ID + 100 + har_idx * len(HAR_STAT_NAMES) + stat_idx


def pilot_stat_item_id(stat_idx: int) -> int:
    return BASE_ID + 200 + stat_idx


def har_enhancement_item_id(har_idx: int) -> int:
    return BASE_ID + 400 + har_idx


MONEY_SMALL_ID = BASE_ID + 300
MONEY_LARGE_ID = BASE_ID + 301
NOTHING_ID     = BASE_ID + 302


def _build_item_table() -> dict[str, int]:
    table: dict[str, int] = {}
    for i, har in enumerate(HAR_NAMES):
        table[f"{har} Unlock"] = har_unlock_id(i)
    for hi, har in enumerate(HAR_NAMES):
        for si, stat in enumerate(HAR_STAT_NAMES):
            table[f"Progressive {har} {stat}"] = har_stat_item_id(hi, si)
    for pi, stat in enumerate(PILOT_STAT_NAMES):
        table[f"Progressive {stat}"] = pilot_stat_item_id(pi)
    for hi, har in enumerate(HAR_NAMES):
        if HAR_ENHANCEMENT_COUNTS[hi] > 0:
            table[f"Progressive {har} Enhancement"] = har_enhancement_item_id(hi)
    table["Money (Small)"] = MONEY_SMALL_ID
    table["Money (Large)"] = MONEY_LARGE_ID
    table["Nothing"]       = NOTHING_ID
    return table


ITEM_NAME_TO_ID: dict[str, int] = _build_item_table()

ITEM_GROUPS: dict[str, set[str]] = {
    "HAR Unlocks":      {f"{har} Unlock" for har in HAR_NAMES},
    "HAR Upgrades":     {f"Progressive {har} {stat}" for har in HAR_NAMES for stat in HAR_STAT_NAMES},
    "HAR Enhancements": {f"Progressive {har} Enhancement" for har, count in zip(HAR_NAMES, HAR_ENHANCEMENT_COUNTS) if count > 0},
    "Pilot Upgrades":   {f"Progressive {stat}" for stat in PILOT_STAT_NAMES},
    "Money":            {"Money (Small)", "Money (Large)"},
}


def _classify(name: str) -> ItemClassification:
    if "Unlock" in name:
        return ItemClassification.progression  # gates HAR buy locations
    if "Progressive" in name:
        return ItemClassification.useful
    return ItemClassification.filler


def create_item(world, name: str) -> OMFItem:
    return OMFItem(name, _classify(name), ITEM_NAME_TO_ID[name], world.player)


def get_filler_item_name(world) -> str:
    return world.random.choice(["Money (Small)", "Money (Large)", "Nothing"])
