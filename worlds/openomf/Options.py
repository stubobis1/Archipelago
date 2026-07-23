from dataclasses import dataclass
from Options import Choice, Toggle, Range, PerGameCommonOptions


class GoalTournament(Choice):
    """Which tournament must be won to complete the seed."""
    display_name = "Goal Tournament"
    option_north_american_open  = 0
    option_katushai_challenge   = 1
    option_war_invitational     = 2
    option_world_championship   = 3
    option_all_tournaments      = 4
    default = 3


class StartingHAR(Choice):
    """Which HAR the player begins with. Random picks one of the 11 at generation time."""
    display_name = "Starting HAR"
    option_jaguar   = 0
    option_shadow   = 1
    option_thorn    = 2
    option_pyros    = 3
    option_electra  = 4
    option_katana   = 5
    option_shredder = 6
    option_flail    = 7
    option_gargoyle = 8
    option_chronos  = 9
    option_nova            = 10
    option_random_selection = 11
    default = 11


class HARStatMax(Range):
    """Maximum upgrade level for each HAR stat. Vanilla = 9."""
    display_name = "HAR Stat Max"
    range_start = 1
    range_end   = 20
    default     = 9


class PilotStatMax(Range):
    """Maximum upgrade level for each pilot stat. Vanilla = 25."""
    display_name = "Pilot Stat Max"
    range_start = 1
    range_end   = 50
    default     = 25


class IncludeBuyLocations(Toggle):
    """Include Mechlab purchase slots and Training slots as location checks.
    When off, only match and tournament checks are generated and HAR/pilot stat
    upgrades are removed from the item pool."""
    display_name = "Include Buy Locations"
    default = 1


class BuyCostFactor(Range):
    """Per-level cost multiplier on top of vanilla Mechlab prices (stored as integer,
    divide by 100 for float). 100 = vanilla prices. 200 = each successive upgrade
    costs 2× vanilla for that tier. Range 10–1000 (0.1×–10×)."""
    display_name = "Buy Cost Factor"
    range_start = 10
    range_end   = 1000
    default     = 100


@dataclass
class OMFOptions(PerGameCommonOptions):
    goal_tournament:       GoalTournament
    starting_har:          StartingHAR
    har_stat_max:          HARStatMax
    pilot_stat_max:        PilotStatMax
    include_buy_locations: IncludeBuyLocations
    buy_cost_factor:       BuyCostFactor
