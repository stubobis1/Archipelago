from BaseClasses import Region, ItemClassification
from .data.tournaments import TOURNAMENTS, HAR_NAMES, HAR_STAT_NAMES, PILOT_STAT_NAMES
from .Items import OMFItem
from .Locations import (
    OMFLocation, match_location_id, tournament_win_id,
    har_buy_location_id, pilot_buy_location_id,
)

if False:
    from . import OMFWorld  # type hint only


def create_regions(world: "OMFWorld") -> None:
    player         = world.player
    mw             = world.multiworld
    har_stat_max   = world.options.har_stat_max.value
    pilot_stat_max = world.options.pilot_stat_max.value
    include_buy    = bool(world.options.include_buy_locations.value)
    goal_idx       = world.options.goal_tournament.value

    menu = Region("Menu", player, mw)
    mw.regions.append(menu)

    # Tournament regions — all accessible from Menu (money enforces ordering in-game).
    match_idx = 0
    for ti, t in enumerate(TOURNAMENTS):
        region = Region(t["name"], player, mw)

        for pilot_name, _, restricted in t["pilots"]:
            if not restricted:
                loc = OMFLocation(player, f"{t['name']} - Beat {pilot_name}",
                                  match_location_id(match_idx), region)
                region.locations.append(loc)
            match_idx += 1

        win_loc = OMFLocation(player, f"Win {t['name']}",
                              tournament_win_id(ti), region)
        region.locations.append(win_loc)

        mw.regions.append(region)
        menu.connect(region)

    # HAR buy regions — one per HAR, gated by HAR unlock item.
    if include_buy:
        for hi, har in enumerate(HAR_NAMES):
            region = Region(f"{har} Mechlab", player, mw)
            for si, stat in enumerate(HAR_STAT_NAMES):
                for lvl in range(1, har_stat_max + 1):
                    loc = OMFLocation(
                        player, f"Buy {har} {stat} Upgrade {lvl}",
                        har_buy_location_id(hi, si, lvl), region,
                    )
                    region.locations.append(loc)
            mw.regions.append(region)
            menu.connect(region, rule=lambda state, h=har: state.has(f"{h} Unlock", player))

        train_region = Region("Pilot Training", player, mw)
        for pi, stat in enumerate(PILOT_STAT_NAMES):
            for lvl in range(1, pilot_stat_max + 1):
                loc = OMFLocation(
                    player, f"Train {stat} Level {lvl}",
                    pilot_buy_location_id(pi, lvl), train_region,
                )
                train_region.locations.append(loc)
        mw.regions.append(train_region)
        menu.connect(train_region)

    # Victory event — separate event location (address=None) in the goal region.
    # The game client calls StatusUpdate(GOAL) when done; this event expresses logical completion.
    goal_all = goal_idx == 4
    if goal_all:
        goal_region_name = TOURNAMENTS[-1]["name"]
    else:
        goal_region_name = TOURNAMENTS[goal_idx]["name"]

    goal_region = mw.get_region(goal_region_name, player)
    victory_loc = OMFLocation(player, "Victory", None, goal_region)  # type: ignore[arg-type]
    victory_item = OMFItem("Victory", ItemClassification.progression, None, player)  # type: ignore[arg-type]
    victory_loc.place_locked_item(victory_item)
    goal_region.locations.append(victory_loc)
