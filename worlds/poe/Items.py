import random
import typing
from collections import defaultdict

if typing.TYPE_CHECKING:
    from worlds.poe import PathOfExileWorld
    from worlds.poe.Options import PathOfExileOptions

from BaseClasses import Item, ItemClassification
from typing import TypedDict, Dict, Set

from worlds.poe.data import ItemTable
from worlds.poe import Locations
from worlds.poe import Items

import logging
logger = logging.getLogger("poe.Items")
logger.setLevel(logging.DEBUG)
_verbose_debug = False  # Set to True to enable verbose debug logging

ACT_0_USABLE_GEMS = 4
ACT_0_FLASK_SLOTS = 3
ACT_0_WEAPON_TYPES = 2
ACT_0_ARMOUR_TYPES = 2
ACT_0_ADDITIONAL_LOCATIONS = 8

class ItemDict(TypedDict, total=False): 
    classification: ItemClassification 
    count: int | None
    id : int
    name: str 
    category: list[str]
    reqLevel: int | None
    reqToUse: list[str] | None

class PathOfExileItem(Item):
    """
    Represents an item in the Path of Exile world.
    This class can be extended to include specific item properties and methods.
    """
    game = "Path of Exile"
    itemInfo: ItemDict
    category = list[str]()


item_table: Dict[int, ItemDict] = ItemTable.item_table
alternate_gems: Dict[str, Dict] = ItemTable.alternate_gems
if _verbose_debug:
    logger.debug(f"Loaded {len(item_table)} items from ItemTable.")
memoize_cache: Dict[str, list[ItemDict]] = {}

def deprioritize_non_logic_gems(world: "PathOfExileWorld", table: Dict[int, ItemDict]) -> Dict[int, ItemDict]:
    opt: PathOfExileOptions = world.options
    
    # Early exit if no gems are in the table (e.g., when gems are disabled)
    all_gems = get_all_gems(table)
    if not all_gems:
        return table
    
    still_required_gem_ids = set()

    #act 0 starter gems
    selected_gems = [] # a list, we may have duplicates, but that's fine
    lvl_1_gems = [item for item in get_main_skill_gem_items(table) if item["reqLevel"] == 1]
    selected_gems.extend(world.random.sample(lvl_1_gems, k=min(ACT_0_USABLE_GEMS, len(lvl_1_gems)))) # 4 starting gems

    for act in range(1, world.goal_act + 1):
        main_gems_for_act = [item for item in get_main_skill_gem_items(table) if item["reqLevel"] <= Locations.acts[act]["maxMonsterLevel"] and item not in selected_gems]
        support_gems_for_act = [item for item in get_support_gem_items(table) if item["reqLevel"] <= Locations.acts[act]["maxMonsterLevel"] and item not in selected_gems]
        utility_gems_for_act = [item for item in get_utility_skill_gem_items(table) if item["reqLevel"] <= Locations.acts[act]["maxMonsterLevel"] and item not in selected_gems]

        if main_gems_for_act:
            selected_gems.extend(world.random.sample(main_gems_for_act, k=min(max(opt.skill_gems_per_act.value, 1), len(main_gems_for_act)))) #need at _least_ one main skill gem per act
        if support_gems_for_act:
            selected_gems.extend(world.random.sample(support_gems_for_act, k=min(opt.support_gems_per_act.value, len(support_gems_for_act))))
        if utility_gems_for_act:
            selected_gems.extend(world.random.sample(utility_gems_for_act, k=min(opt.skill_gems_per_act.value, len(utility_gems_for_act))))

    still_required_gem_ids.update(item["id"] for item in selected_gems)
    
    for item in table.values():
        if "MainSkillGem" in item["category"]\
            or "SupportGem" in item["category"] \
            or "UtilSkillGem" in item["category"] \
                :
            if item["id"] in still_required_gem_ids:
                item["classification"] = ItemClassification.progression
            else:
                if item["classification"] == ItemClassification.progression:
                    item["classification"] = ItemClassification.useful
#                elif item["classification"] == ItemClassification.useful:
#                    item["classification"] = ItemClassification.filler
    return table

def deprioritize_non_logic_gear(world: "PathOfExileWorld", table: Dict[int, ItemDict]) -> Dict[int, ItemDict]:
    opt: PathOfExileOptions = world.options

    # If gear upgrades are disabled, don't try to deprioritize any gear, flask are already progressive.
    if opt.gear_upgrades.value == opt.gear_upgrades.option_all_gear_unlocked_at_start:
        return table

    required_categories = list()
    progression_main_gems = [gem for gem in get_main_skill_gem_items(table) if gem["classification"] == ItemClassification.progression]
    for gem in progression_main_gems:
        if gem.get("reqToUse"):
            required_categories.append(random.choice(gem.get("reqToUse")))
    
    required_categories = world.random.sample(required_categories, k=min(ACT_0_WEAPON_TYPES, len(required_categories)))
    if "Unarmed" in required_categories: required_categories.remove("Unarmed")
    required_categories.extend(["Wand", "Bow", "Sword"])
    required_categories = required_categories[:ACT_0_WEAPON_TYPES]  # Ensure we only keep the guaranteed number of weapons

    required_armor_ids = [i['id'] for i in  world.random.sample(get_armor_items(table), k=min(ACT_0_ARMOUR_TYPES, len(get_armor_items(table))))]
    gear_ids = [item["id"] for item in get_gear_items(table)]
    progression_sample_size = min(opt.gear_upgrades_per_act.value * world.goal_act, len(gear_ids))
    progression_gear_ids = world.random.sample(gear_ids, progression_sample_size)

    required_categories.append("Flask") # Flasks are always progression
    for item in [ item for item in get_gear_items(table)]:
        if (any(cat in item["category"] for cat in required_categories)
            or item["id"] in required_armor_ids
            or item["id"] in progression_gear_ids):
            item["classification"] = ItemClassification.progression
        else:
            if item["classification"] == ItemClassification.progression:
                item["classification"] = ItemClassification.useful
 #           elif item["classification"] == ItemClassification.useful:
 #               item["classification"] = ItemClassification.filler
    
    return table

def cull_items_to_place(world: "PathOfExileWorld", items: Dict[int, ItemDict], locations: Dict[int, ItemDict]) -> Dict[int, ItemDict]:
    total_locations_count = len(locations)

    # Keep culling until we match the location count
    while True:
        total_items_count = sum(item.get("count", 1) for item in items.values())
        amount_to_cull = total_items_count - total_locations_count
        
        if amount_to_cull <= 0:
            break

        filler_items = [(item_id, item) for item_id, item in items.items() 
                       if item.get("classification") == ItemClassification.filler]

        useful_items = [(item_id, item) for item_id, item in items.items()
                       if item.get("classification") == ItemClassification.useful]
        
        
        if not filler_items and not useful_items:
            logger.error("[ERROR] No items available to remove. Cannot match location count.")
            break

        if len(filler_items + useful_items) < amount_to_cull:
            logger.error(f"\n[ERROR] Not enough non-progressive items to cull ({len(filler_items + useful_items)}) to meet location count need to cull({amount_to_cull}).")

        filler_items = world.random.sample(filler_items, k=min(len(filler_items), amount_to_cull))
        useful_items = world.random.sample(useful_items, k=min(len(useful_items), amount_to_cull))

        culled_count = 0
        def cull_item_func(cull_items, culled_count=0, amount_to_cull=amount_to_cull):
            starting_culled_count = culled_count
            items_to_remove = []

            for item_id, item in cull_items:
                if culled_count >= amount_to_cull:
                    break

                item_count = item.get("count", 1)

                if item_count <= (amount_to_cull - culled_count):
                    # Remove entire item
                    items_to_remove.append(item_id)
                    culled_count += item_count
                else:
                    # Reduce item count
                    reduction = amount_to_cull - culled_count
                    item["count"] = item_count - reduction
                    culled_count += reduction

            # Remove items marked for removal
            for item_id in items_to_remove:
                items.pop(item_id, None)
            return culled_count - starting_culled_count

        culled_count += cull_item_func(filler_items, culled_count, amount_to_cull)
        culled_count += cull_item_func(useful_items, culled_count, amount_to_cull)

        logger.info(f"[INFO] Culled {culled_count} items.")

    # Final verification
    final_count = sum(item.get("count", 1) for item in items.values())
    if final_count > total_locations_count:
        logger.error(f"\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                     f"\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                     f"\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                     f"\n"
                     f"\nGENERATION ERROR! with player ({world.player_name})"
                     f"\nFinal item count ({final_count}) is greater than location count ({total_locations_count})"
                     f"\nWill precollect random items to make up the difference."
                     f"\n"
                     f"\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                     f"\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                     f"\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")
        while final_count > total_locations_count:
            # Precollect random items to fill the gap
            random_item: ItemDict = world.random.choice(list(items.values()))
            logger.debug(f"Precollecting item: {random_item['name']}")
            random_item["count"] = random_item.get("count", 1) - 1
            if random_item["count"] <= 0:
                items.pop(random_item["id"])
            item_obj = Items.PathOfExileItem(random_item["name"], random_item["classification"], random_item["id"], world.player)
            world.precollect(item_obj)
            final_count -= 1
        
    return items


def get_item_name_groups() -> Dict[str, Set[str]]:
    categories: Dict[str, Set[str]] = defaultdict(set)
    for item in item_table.values():
        main_category = item.get("category", [None])[0]
        if main_category:
            categories[main_category].add(item["name"])
    return categories

def get_flask_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_by_category("Flask", table)

def get_character_class_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_by_category("Character Class", table)

def get_base_class_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_by_category("Base Class", table)

def get_ascendancy_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_by_category("Ascendancy", table)

def get_ascendancy_class_items(class_name: str, table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_by_has_every_category({"Ascendancy", f"{class_name} Class"}, table)

def get_main_skill_gem_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_by_category("MainSkillGem", table)

def get_main_skill_gem_items_table(table: Dict[int, ItemDict] = item_table) -> dict[int, ItemDict]:
    return {item["id"]: item for item in get_main_skill_gem_items(table)}

def get_support_gem_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_by_category("SupportGem", table)

def get_utility_skill_gem_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_by_category("UtilSkillGem", table)

def get_gear_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_by_category("Gear", table)

def get_armor_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_by_category("Armor", table)

def get_weapon_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_by_category("Weapon", table)

def get_max_links_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_by_category("max links", table)

def get_all_gems(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    if table is item_table and "AllGems" in memoize_cache:
        return memoize_cache["AllGems"]
    result = get_main_skill_gem_items(table) + get_support_gem_items(table) + get_utility_skill_gem_items(table)
    if table is item_table: memoize_cache["AllGems"] = result
    return result

def get_main_skill_gems_by_required_level(level_minimum:int=0, level_maximum:int=100, table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    key = f"MainSkillGems_{level_minimum}_{level_maximum}"
    if table is item_table and key in memoize_cache:
        return memoize_cache[key]
    result = [item for item in table.values() if "MainSkillGem" in item["category"] and (item["reqLevel"] is not None and (level_minimum <= item["reqLevel"] <= level_maximum))]
    if table is item_table: memoize_cache[key] = result
    return result

def get_main_skill_gems_by_required_level_and_useable_weapon(available_weapons: set[str], level_minimum:int=0, level_maximum:int=100, table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return [item for item in table.values() if "MainSkillGem" in item["category"] and (item["reqLevel"] is not None and (level_minimum <= item["reqLevel"] <= level_maximum))
            and (any(weapon in available_weapons for weapon in item.get("reqToUse", [])) or not item.get("reqToUse", []))] # we have the weapon, or there are no reqToUse

def get_support_gems_by_required_level(level_minimum:int=0, level_maximum:int=100, table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    key = f"SupportGems_{level_minimum}_{level_maximum}"
    if table is item_table and key in memoize_cache:
        return memoize_cache[key]
    result = [item for item in table.values() if "SupportGem" in item["category"] and (item["reqLevel"] is not None and (level_minimum <= item["reqLevel"] <= level_maximum))]
    if table is item_table: memoize_cache[key] = result
    return result

def get_utility_skill_gems_by_required_level(level_minimum:int=0, level_maximum:int=100, table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    key = f"UtilitySkillGems_{level_minimum}_{level_maximum}"
    if table is item_table and key in memoize_cache:
        return memoize_cache[key]
    result = [item for item in table.values() if "UtilSkillGem" in item["category"] and (item["reqLevel"] is not None and (level_minimum <= item["reqLevel"] <= level_maximum))]
    if table is item_table: memoize_cache[key] = result
    return result

def get_all_gems_by_required_level(level_minimum:int=0, level_maximum:int=100, table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    return get_main_skill_gems_by_required_level(level_minimum, level_maximum, table) + \
           get_support_gems_by_required_level(level_minimum, level_maximum, table) + \
           get_utility_skill_gems_by_required_level(level_minimum, level_maximum, table)

def get_by_category(category: str, table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    key = f"category_{category}"
    if table is item_table and key in memoize_cache:
        return memoize_cache[key]
    result = [item for item in table.values() if category in item["category"]]
    if table is item_table: memoize_cache[key] = result
    return result

def get_by_has_every_category(categories: Set[str], table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    key = f"has_every_category_{'_'.join(sorted(categories))}"
    if table is item_table and key in memoize_cache:
        return memoize_cache[key]
    result = [item for item in table.values() if all(cat in item["category"] for cat in categories)]
    if table is item_table: memoize_cache[key] = result
    return result

def get_by_has_any_category(categories: Set[str], table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    key = f"has_any_category_{'_'.join(sorted(categories))}"
    if table is item_table and key in memoize_cache:
        return memoize_cache[key]
    result = [item for item in table.values() if any(cat in item["category"] for cat in categories)]
    if table is item_table: memoize_cache[key] = result
    return result

def get_by_name(name: str, table: Dict[int, ItemDict] = item_table) -> ItemDict | None:
    return next((item for item in table.values() if item["name"] == name), None)

# used to check offhands

quiver_base_types = ItemTable.quiver_base_type_array.copy()  # Copy the list to avoid modifying the original data
shield_base_types = ItemTable.shield_base_type_array.copy() 


# used to check weapon base types
held_equipment_types = [
"Axe",
"Bow",
"Claw",
"Dagger",
"Mace",
"Sceptre",
"Staff",
"Sword",
"Wand",
"Shield",
"Quiver",
"Fishing Rod",
]