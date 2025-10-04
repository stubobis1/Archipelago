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

MAX_GUCCI_GEAR_UPGRADES = 19 # fishing rods don't count.
MAX_GEAR_UPGRADES       = 50
MAX_FLASK_SLOTS         = 10
MAX_LINK_UPGRADES       = 22
MAX_SKILL_GEMS          = 50 # you will get more, but this is the max required for "logic"
MAX_SUPPORT_GEMS        = 50 # you will get more, but this is the max required for "logic"

_debug = True
_very_debug = True
if Items.ACT_0_USABLE_GEMS + Items.ACT_0_WEAPON_TYPES + Items.ACT_0_ARMOUR_TYPES + Items.ACT_0_FLASK_SLOTS > 19:
    raise Exception("Act 0 requirements are too high, there are not enough locations in early act 1 to satisfy them")

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

def get_gear_amount_for_act(act, opt):
    max_gear = 0
    if opt.gucci_hobo_mode.value == opt.gucci_hobo_mode.option_disabled:
        max_gear = MAX_GEAR_UPGRADES
    elif opt.gucci_hobo_mode.value == opt.gucci_hobo_mode.option_no_non_unique_items:
        max_gear = MAX_GUCCI_GEAR_UPGRADES
    else:
        max_gear = MAX_GUCCI_GEAR_UPGRADES + 1 # allow one non-unique item
    return min(opt.gear_upgrades_per_act.value * (act - 1), max_gear)

def get_flask_amount_for_act(act, opt):
    return 0 if not opt.add_flasks_to_item_pool else min(opt.flasks_per_act.value * (act - 1), MAX_FLASK_SLOTS if opt.add_flasks_to_item_pool.value else 0)

def get_gem_amount_for_act(act, opt):
    return 0 if not opt.add_max_links_to_item_pool else min(opt.max_links_per_act.value * (act - 1), MAX_LINK_UPGRADES if opt.add_max_links_to_item_pool.value else 0)

def get_skill_gem_amount_for_act(act, opt):
    return min(opt.skill_gems_per_act.value * (act - 1), MAX_SKILL_GEMS if opt.add_skill_gems_to_item_pool.value else 0)

def get_support_gem_amount_for_act(act, opt):
    return min(opt.support_gems_per_act.value * (act - 1), MAX_SUPPORT_GEMS if opt.add_support_gems_to_item_pool.value else 0)

def get_passives_amount_for_act(act, opt):
    return passives_required_for_act.get(act, 0) if opt.add_passive_skill_points_to_item_pool.value else 0

def completion_condition(world: "PathOfExileWorld",  state: CollectionState) -> bool:
    if len(world.bosses_for_goal) > 0:
        # if we can reach act 11, we can assume the world is completable.
        return can_reach(11, world, state)

    else: # reach act for goal
        return can_reach(world.goal_act, world, state)

def can_reach(act: int, world: "PathOfExileWorld", state: CollectionState) -> bool:
    opt : PathOfExileOptions = world.options

    if opt.disable_generation_logic.value:
        return True

    reachable = True
    if act < 1:
        return True

    ascendancy_amount = get_ascendancy_amount_for_act(act, opt)
    gear_amount = get_gear_amount_for_act(act, opt)
    flask_amount = get_flask_amount_for_act(act, opt)
    gem_slot_amount = get_gem_amount_for_act(act, opt)
    skill_gem_amount = get_skill_gem_amount_for_act(act, opt)
    support_gem_amount = get_support_gem_amount_for_act(act, opt)
    passive_amount = get_passives_amount_for_act(act,opt)

    # make a list of valid weapon types, based on the state

    valid_weapon_types = {
        item for item in weapon_categories
        if state.has_from_list([i["name"] for i in Items.get_by_category(item)], world.player, 1)
    }
    valid_weapon_types.add("Unarmed")  # every character can use unarmed, so we add it as a valid type, for gems
    
    ascedancy_count = state.count_from_list([item['name'] for item in Items.get_ascendancy_class_items(opt.starting_character.current_option_name)], world.player)
    gear_count = state.count_from_list([item['name'] for item in Items.get_gear_items()], world.player)
    flask_count = state.count_from_list([item['name'] for item in Items.get_flask_items() if 'Unique' not in item.get('category', '')], world.player) # unique flasks are not logically required
    support_gem_count = state.count_from_list([item['name'] for item in Items.get_support_gem_items()], world.player)
    gem_slot_count = state.count_from_list([item['name'] for item in Items.get_max_links_items()], world.player)
    passive_count = state.count("Progressive passive point", world.player)

    gems_for_our_weapons = [item['name'] for item in Items.get_main_skill_gems_by_required_level_and_useable_weapon(
            available_weapons= valid_weapon_types, level_minimum=1, level_maximum=acts[act].get("maxMonsterLevel", 0) )]
    usable_skill_gem_count = (state.count_from_list(gems_for_our_weapons, world.player))


    valid_weapon_types.remove("Unarmed") # we don't care about this for the rest of the logic
    if act == 1:
            # Check distinct armor categories

        distinct_armor_count = 0

        for category in armor_categories:
            category_items = [item['name'] for item in Items.get_by_category(category)]
            if category_items and state.has_from_list(category_items, world.player, 1):
                distinct_armor_count += 1

        reachable &= usable_skill_gem_count >= Items.ACT_0_USABLE_GEMS
        reachable &= len(valid_weapon_types) >= Items.ACT_0_WEAPON_TYPES
        reachable &= distinct_armor_count >= Items.ACT_0_ARMOUR_TYPES
        reachable &= flask_count >= Items.ACT_0_FLASK_SLOTS

        if not reachable:
            if _debug:
                log = f"Act 0 not reachable with gear:"
                if len(valid_weapon_types) < Items.ACT_0_WEAPON_TYPES:
                    log += f" weapon types: {len(valid_weapon_types)}/{Items.ACT_0_WEAPON_TYPES},"
                if distinct_armor_count < Items.ACT_0_ARMOUR_TYPES:
                    log += f" armor types: {distinct_armor_count}/{Items.ACT_0_ARMOUR_TYPES},"
                if flask_count < Items.ACT_0_FLASK_SLOTS:
                    log += f" flask: {flask_count}/{Items.ACT_0_FLASK_SLOTS},"
                if usable_skill_gem_count < Items.ACT_0_USABLE_GEMS:
                    log += f" skill gems: {usable_skill_gem_count}/{Items.ACT_0_USABLE_GEMS},"
                log += f" for {opt.starting_character.current_option_name}"
                #logger.debug(log)

            return False

        else:
            if _debug and _very_debug:
                #logger.debug(f"Act 0 is reachable with gear for {opt.starting_character.current_option_name}")
                pass


    reachable &= ascedancy_count >= ascendancy_amount and \
            gear_count >= gear_amount and \
            flask_count >= flask_amount and \
            gem_slot_count >= gem_slot_amount and \
            support_gem_count >= support_gem_amount and \
            usable_skill_gem_count >= skill_gem_amount and \
            passive_count >= passive_amount

    if not reachable:
        if _debug:
            log = f"Act {act} not reachable with:"
            if gear_count < gear_amount:
                log += f"gear: {gear_count}/{gear_amount} (total: {len(Items.get_gear_items(world.items_to_place))}),"
            if flask_count < flask_amount:
                log += f" flask: {flask_count}/{flask_amount},"
            if gem_slot_count < gem_slot_amount:
                amount = Items.get_max_links_items(world.items_to_place)
                log += f" gem slots: {gem_slot_count}/{gem_slot_amount}, full_amount: {amount}"
            if support_gem_count < support_gem_amount:
                log += f" support gems: {support_gem_count}/{support_gem_amount},"
            if usable_skill_gem_count < skill_gem_amount:
                log += f" skill gems: {usable_skill_gem_count}/{skill_gem_amount},"
            if ascedancy_count < ascendancy_amount:
                log += f" ascendancies: {ascedancy_count}/{ascendancy_amount},"
            if passive_count < passive_amount:
                log += f" levels:{passive_count}/{passive_amount}"
            log += f" for {opt.starting_character.current_option_name}"

            #print (log)

            logger.debug(log)
        if _very_debug:
            #logger.debug(f"[DEBUG] expecting Act {act} - Gear: {gear_amount}, Flask: {flask_amount}, Gem Slots: {gem_slot_amount}, Skill Gems: {skill_gem_amount}, Ascendancies: {ascedancy_amount}")
            #logger.debug(f"[DEBUG] we have   Act {act} - Gear: {gear_count}, Flask: {flask_count}, Gem Slots: {gem_slot_count}, Skill Gems: {usable_skill_gem_count}, Ascendancies: {ascedancy_count}")
            #add up all the prog items


            total_items = state.count_from_list([item["name"] for item in Items.get_gear_items()], world.player) + \
                          state.count_from_list([item["name"] for item in Items.get_flask_items()], world.player) + \
                          state.count_from_list([item["name"] for item in Items.get_max_links_items()], world.player) + \
                          state.count_from_list([item["name"] for item in Items.get_main_skill_gem_items()], world.player) + \
                          state.count_from_list([item["name"] for item in Items.get_ascendancy_class_items(opt.starting_character.current_option_name)], world.player)
            #logger.debug(f"[DEBUG] total items {total_items}, ")
            #logger.debug(f"[DEBUG] expecting   {gear_amount + flask_amount + gem_slot_amount + skill_gem_amount} items")
    
    
    return reachable





def SelectLocationsToAdd (world: "PathOfExileWorld", target_amount) -> list[LocationDict]:
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
        needed_locations += Items.ACT_0_USABLE_GEMS + Items.ACT_0_WEAPON_TYPES + Items.ACT_0_ARMOUR_TYPES + Items.ACT_0_FLASK_SLOTS + Items.ACT_0_ADDITIONAL_LOCATIONS
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
            logger.error(f"\n@@@@@@@@@@\n[ERROR] Not enough locations for Act {act}. Needed: {needed_locations_for_act}, Available: {len(locations_in_act)}, going to try to generate anyway...")

        selected_locations = world.random.sample(locations_in_act, k=min(needed_locations_for_act, len(locations_in_act)))
        for loc in selected_locations:
            total_available_locations.remove(loc)
        selected_locations_result.extend(selected_locations)

    world.random.shuffle(total_available_locations)
    selected_locations_result.extend(total_available_locations)
    return selected_locations_result[:target_amount]




