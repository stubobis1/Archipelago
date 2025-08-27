import logging

from worlds.poe.Options import PathOfExileOptions
from .Locations import PathOfExileLocation, base_item_type_locations, level_locations, acts, LocationDict
from BaseClasses import CollectionState, Region
from . import Items
import typing
if typing.TYPE_CHECKING:
    from . import PathOfExileWorld

logger = logging.getLogger("poe.Rules")
logger.setLevel(logging.DEBUG)

MAX_GUCCI_GEAR_UPGRADES = 20
MAX_GEAR_UPGRADES       = 50
MAX_FLASK_SLOTS         = 10
MAX_LINK_UPGRADES       = 22
MAX_SKILL_GEMS          = 50 # you will get more, but this is the max required for "logic"
MAX_SUPPORT_GEMS        = 50 # you will get more, but this is the max required for "logic"

ACT_0_USABLE_GEMS = 4
ACT_0_FLASK_SLOTS = 3
ACT_0_WEAPON_TYPES = 2
ACT_0_ARMOUR_TYPES = 2
ACT_0_ADDITIONAL_LOCATIONS = 8
_debug = False
_very_debug = False


armor_categories = ["BodyArmour", "Boots", "Gloves", "Helmet", "Amulet", "Belt", "Ring (left)", "Ring (right)", "Quiver", "Shield"]
weapon_categories = ["Axe","Bow","Claw","Dagger","Mace","Sceptre","Staff","Sword","Wand",
                            #"Fishing Rod", # yeahhhh no, not required for logic
                            #"Unarmed" # every character can use unarmed, so no need to check this
                            ]

passives_required_for_act = {
    1: 6,
    2: 18,
    3: 34,
    4: 46,
    5: 56,
    6: 68,
    7: 80,
    8: 90,
    9: 100,
    10: 109,
    11: 120,
    12: 136,  # max amount of passives in the game (including ascendancy points)
}

def get_ascendancy_amount_for_act(act, opt):
    return (
        min(
            opt.ascendancies_available_per_class.value,
            3 if opt.starting_character.value != opt.starting_character.option_scion else 1
        )
    ) if act >= 3 else 0

def get_gear_amount_for_act(act, opt): return min(opt.gear_upgrades_per_act.value * (act - 1), MAX_GEAR_UPGRADES if opt.gucci_hobo_mode.value == opt.gucci_hobo_mode.option_disabled else MAX_GUCCI_GEAR_UPGRADES)
def get_flask_amount_for_act(act, opt): return 0 if not opt.add_flask_slots_to_item_pool else min(opt.flask_slots_per_act.value * (act - 1), MAX_FLASK_SLOTS)
def get_gem_amount_for_act(act, opt): return 0 if not opt.add_max_links_to_item_pool else min(opt.max_links_per_act.value * (act - 1), MAX_LINK_UPGRADES)
def get_skill_gem_amount_for_act(act, opt): return min(opt.skill_gems_per_act.value * (act - 1), MAX_SKILL_GEMS)
def get_support_gem_amount_for_act(act, opt): return min(opt.support_gems_per_act.value * (act - 1), MAX_SUPPORT_GEMS)
def get_passives_amount_for_act(act, opt): return passives_required_for_act.get(act, 0) if opt.add_passive_skill_points_to_item_pool.value else 0

def completion_condition(world: "PathOfExileWorld",  state: CollectionState) -> bool:
    if len(world.bosses_for_goal) > 0:
        # if we can reach act 11, we can assume we have completed the goal
        return can_reach(11, world, state)
    #    # if there are bosses for the goal, we need to check if they are all completed
    #    for boss in world.bosses_for_goal:
    #        if not state.has(f"complete {boss}", world.player):
    #            return False
    #    return True

    else: # reach act for goal
        return can_reach(world.goal_act, world, state)

# Cache for expensive item lookups to avoid repeated computation
_item_cache = {}

def _get_cached_items(cache_key, item_func, *args):
    """Cache expensive item list generation."""
    if cache_key not in _item_cache:
        _item_cache[cache_key] = item_func(*args)
    return _item_cache[cache_key]

def can_reach(act: int, world, state: CollectionState) -> bool:
    opt: PathOfExileOptions = world.options

    if opt.disable_generation_logic.value:
        return True

    if act < 1:
        return True

    # Early exit optimization - calculate required amounts first
    ascedancy_amount = get_ascendancy_amount_for_act(act, opt)
    gear_amount = get_gear_amount_for_act(act, opt)
    flask_amount = get_flask_amount_for_act(act, opt)
    gem_slot_amount = get_gem_amount_for_act(act, opt)
    skill_gem_amount = get_skill_gem_amount_for_act(act, opt)
    support_gem_amount = get_support_gem_amount_for_act(act, opt)
    passive_amount = get_passives_amount_for_act(act, opt)

    # Quick passive check first (cheapest operation)
    passive_count = state.count("Progressive passive point", world.player)
    if passive_count < passive_amount:
        return False

    # Cache item lists by character class to avoid repeated lookups
    char_class = opt.starting_character.current_option_name
    ascendancy_items = _get_cached_items(f"ascendancy_{char_class}", Items.get_ascendancy_class_items, char_class)
    gear_items = _get_cached_items("gear_items", Items.get_gear_items)
    flask_items = _get_cached_items("flask_items", Items.get_flask_items)
    support_gem_items = _get_cached_items("support_gem_items", Items.get_support_gem_items)
    max_links_items = _get_cached_items("max_links_items", Items.get_max_links_items)

    # Pre-filter flask items to exclude unique ones (done once and cached)
    non_unique_flask_key = "non_unique_flasks"
    if non_unique_flask_key not in _item_cache:
        _item_cache[non_unique_flask_key] = [item for item in flask_items if 'Unique' not in item['category']]
    non_unique_flask_items = _item_cache[non_unique_flask_key]

    # Extract names once and reuse
    ascendancy_names = [item['name'] for item in ascendancy_items]
    gear_names = [item['name'] for item in gear_items]
    non_unique_flask_names = [item['name'] for item in non_unique_flask_items]
    support_gem_names = [item['name'] for item in support_gem_items]
    max_links_names = [item['name'] for item in max_links_items]

    # Batch count operations to reduce state traversals
    ascendancy_count = state.count_from_list(ascendancy_names, world.player)
    gear_count = state.count_from_list(gear_names, world.player)
    flask_count = state.count_from_list(non_unique_flask_names, world.player)
    support_gem_count = state.count_from_list(support_gem_names, world.player)
    gem_slot_count = state.count_from_list(max_links_names, world.player)

    # Early exit checks for most expensive requirements
    if (ascendancy_count < ascedancy_amount or 
        gear_count < gear_amount or 
        flask_count < flask_amount or
        gem_slot_count < gem_slot_amount or
        support_gem_count < support_gem_amount):
        return False

    # Cache weapon category items
    weapon_category_items = {}
    for weapon_type in weapon_categories:
        cache_key = f"weapon_category_{weapon_type}"
        if cache_key not in _item_cache:
            _item_cache[cache_key] = [i["name"] for i in Items.get_by_category(weapon_type)]
        weapon_category_items[weapon_type] = _item_cache[cache_key]

    # Efficiently determine valid weapon types
    valid_weapon_types = {
        weapon_type for weapon_type in weapon_categories
        if weapon_category_items[weapon_type] and state.has_from_list(weapon_category_items[weapon_type], world.player, 1)
    }
    valid_weapon_types.add("Unarmed")  # every character can use unarmed

    # Cache gems for weapons to avoid repeated computation
    max_level = acts[act].get("maxMonsterLevel", 0)
    gems_cache_key = f"gems_{frozenset(valid_weapon_types)}_{max_level}"
    if gems_cache_key not in _item_cache:
        gems_for_weapons = Items.get_main_skill_gems_by_required_level_and_useable_weapon(
            available_weapons=valid_weapon_types, level_minimum=1, level_maximum=max_level
        )
        _item_cache[gems_cache_key] = [item['name'] for item in gems_for_weapons]
    
    gems_for_our_weapons = _item_cache[gems_cache_key]
    usable_skill_gem_count = state.count_from_list(gems_for_our_weapons, world.player)

    # Check skill gem requirement
    if usable_skill_gem_count < skill_gem_amount:
        return False

    valid_weapon_types.discard("Unarmed")  # remove for weapon type count

    # Act 1 specific checks
    if act == 1:
        # Cache armor category items
        distinct_armor_count = 0
        for category in armor_categories:
            cache_key = f"armor_category_{category}"
            if cache_key not in _item_cache:
                _item_cache[cache_key] = [item['name'] for item in Items.get_by_category(category)]
            category_items = _item_cache[cache_key]
            
            if category_items and state.has_from_list(category_items, world.player, 1):
                distinct_armor_count += 1

        # Final Act 1 checks
        if (usable_skill_gem_count < ACT_0_USABLE_GEMS or
            len(valid_weapon_types) < ACT_0_WEAPON_TYPES or
            distinct_armor_count < ACT_0_ARMOUR_TYPES or
            flask_count < ACT_0_FLASK_SLOTS):
            return False

    return True


def clear_item_cache():
    """Clear the item cache. Should be called when starting a new generation."""
    global _item_cache
    _item_cache.clear()


def SelectLocationsToAdd (world: "PathOfExileWorld", target_amount):
    opt:PathOfExileOptions = world.options

    total_available_locations: list[LocationDict] = list()
    selected_locations_result: list[LocationDict] = list()
    goal_act = world.goal_act

    max_level = acts[goal_act]["maxMonsterLevel"]

    # Add base item locations
    base_item_locs = [loc for loc in base_item_type_locations.values() if loc["act"] <= goal_act]
    total_available_locations.extend(base_item_locs)
    
    if opt.add_leveling_up_to_location_pool:
        #    {"name": "Reach Level 100", "level": 100, "act": 11},
        lvl_locs = [loc for loc in level_locations.values() if loc["level"] is not None and loc["level"] <= max_level]
        total_available_locations.extend(lvl_locs)

    def total_needed_by_act(act: int, opt: PathOfExileOptions) -> int:
        if act < 1:
            return 0
        needed_locations = 0
        needed_locations += ACT_0_USABLE_GEMS + ACT_0_WEAPON_TYPES + ACT_0_ARMOUR_TYPES + ACT_0_FLASK_SLOTS + ACT_0_ADDITIONAL_LOCATIONS
        needed_locations += get_ascendancy_amount_for_act(act, opt)
        needed_locations += get_gear_amount_for_act(act, opt)
        needed_locations += get_flask_amount_for_act(act, opt)
        needed_locations += get_gem_amount_for_act(act, opt)
        needed_locations += get_skill_gem_amount_for_act(act, opt)
        needed_locations += get_passives_amount_for_act(act, opt)
        return needed_locations


    for act in range(1, goal_act + 1):
        needed_locations_for_act = total_needed_by_act(act, opt) - total_needed_by_act(act - 1, opt)
        locations_in_act = [loc for loc in total_available_locations if loc["act"] == act]
    
        if not locations_in_act:
            break

        if needed_locations_for_act > len(locations_in_act):
            logger.error(f"[ERROR] Not enough locations for Act {act}. Needed: {needed_locations_for_act}, Available: {len(locations_in_act)}, going to try to generate anyway...")

        selected_locations = world.random.sample(locations_in_act, k=min(needed_locations_for_act, len(locations_in_act)))
        for loc in selected_locations:
            total_available_locations.remove(loc)
        selected_locations_result.extend(selected_locations)

    world.random.shuffle(total_available_locations)
    selected_locations_result.extend(total_available_locations)
    return selected_locations_result[:target_amount]




