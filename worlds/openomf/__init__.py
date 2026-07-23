from typing import Any, Mapping

from BaseClasses import Tutorial
from worlds.AutoWorld import WebWorld, World
from Utils import visualize_regions

from .data.tournaments import TOURNAMENTS, HAR_NAMES, HAR_STAT_NAMES, PILOT_STAT_NAMES, HAR_ENHANCEMENT_COUNTS
from .Items import (
    OMFItem, ITEM_NAME_TO_ID, ITEM_GROUPS,
    create_item, get_filler_item_name,
    har_unlock_id,
)
from .Locations import LOCATION_NAME_TO_ID, LOCATION_GROUPS
from .Options import OMFOptions
from . import Regions, Rules


class OMFWebWorld(WebWorld):
    theme = "dirt"
    tutorials = [Tutorial(
        tutorial_name="Setup Guide",
        description="A guide to setting up One Must Fall: 2097 for Archipelago.",
        language="English",
        file_name="setup_en.md",
        link="setup_en/en",
        authors=["stubob"],
    )]
    bug_report_page = "https://github.com/stubobis1/archipelago-openomf/issues"


class OMFWorld(World):
    """One Must Fall: 2097 — a classic robot fighting tournament game.
    Enter the arena, unlock HARs, and upgrade your robot through Archipelago item randomization."""

    game = "One Must Fall: 2097"
    web  = OMFWebWorld()

    options_dataclass = OMFOptions
    options: OMFOptions

    item_name_to_id     = ITEM_NAME_TO_ID
    location_name_to_id = LOCATION_NAME_TO_ID
    item_name_groups    = ITEM_GROUPS
    location_name_groups = LOCATION_GROUPS

    _starting_har_idx: int  # set in generate_early; use this everywhere, never call _resolve again

    def generate_early(self) -> None:
        idx = self.options.starting_har.value
        self._starting_har_idx = self.random.randint(0, 10) if idx == 11 else idx
        # Starting HAR is handed to the player at connect — no location needed.
        # Precollect the unlock so HAR-gated buy locations are accessible from the start.
        self.multiworld.push_precollected(create_item(self, f"{HAR_NAMES[self._starting_har_idx]} Unlock"))

    def create_regions(self) -> None:
        Regions.create_regions(self)

    def set_rules(self) -> None:
        Rules.set_rules(self)

    def create_items(self) -> None:
        har_stat_max   = self.options.har_stat_max.value
        pilot_stat_max = self.options.pilot_stat_max.value
        include_buy    = bool(self.options.include_buy_locations.value)

        pool: list[OMFItem] = []

        # HAR unlocks — 10 items (starting HAR is precollected in generate_early, not pooled)
        for i, har in enumerate(HAR_NAMES):
            if i != self._starting_har_idx:
                pool.append(create_item(self, f"{har} Unlock"))

        if include_buy:
            # HAR stat progressives: one item per level per stat per HAR
            for har in HAR_NAMES:
                for stat in HAR_STAT_NAMES:
                    for _ in range(har_stat_max):
                        pool.append(create_item(self, f"Progressive {har} {stat}"))
            # Pilot stat progressives: one item per level per stat
            for stat in PILOT_STAT_NAMES:
                for _ in range(pilot_stat_max):
                    pool.append(create_item(self, f"Progressive {stat}"))
            # HAR enhancement progressives: one item per enhancement level per HAR
            for har, count in zip(HAR_NAMES, HAR_ENHANCEMENT_COUNTS):
                for _ in range(count):
                    pool.append(create_item(self, f"Progressive {har} Enhancement"))

        # Filler to fill remaining locations
        total_locations = len(self.multiworld.get_unfilled_locations(self.player))
        while len(pool) < total_locations:
            pool.append(create_item(self, get_filler_item_name(self)))

        self.multiworld.itempool += pool

    def create_item(self, name: str) -> OMFItem:
        return create_item(self, name)

    def get_filler_item_name(self) -> str:
        return get_filler_item_name(self)

    # TODO: set _debug = False before committing / submitting to AP repo
    _debug = True

    def generate_output(self, output_directory: str) -> None:
        if self._debug:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Generating output for {self.game} in {output_directory}")
            from BaseClasses import CollectionState
            local_state = CollectionState(self.multiworld)
            for item in self.multiworld.itempool:
                if item.player == self.player:
                    local_state.collect(item, prevent_sweep=True)
            local_state.sweep_for_advancements(locations=self.multiworld.get_locations(self.player))
            visualize_regions(
                self.multiworld.get_region(self.origin_region_name, self.player),
                f"OMF-Player{self.player}.puml",
                show_entrance_names=True,
                regions_to_highlight=local_state.reachable_regions[self.player],
            )

    def fill_slot_data(self) -> Mapping[str, Any]:
        return {
            "goal_tournament":   self.options.goal_tournament.value,
            "starting_har":      self._starting_har_idx,
            "har_stat_max":      self.options.har_stat_max.value,
            "pilot_stat_max":    self.options.pilot_stat_max.value,
            "include_buy":       bool(self.options.include_buy_locations.value),
            "buy_cost_factor":   self.options.buy_cost_factor.value,
        }
