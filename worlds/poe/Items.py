from BaseClasses import Item, ItemClassification
from typing import TypedDict, Dict, Set

from worlds.poe.data import ItemTable

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
    
    def create_item(self, item: str):
        # this is called when AP wants to create an item by name (for plando, start inventory, item links) or when you call it from your own code
        
        # get the item from the item table, by name
        id = self.item_name_to_id.get(item)
        item = ItemTable.item_table.get(id)
        classification = item.get("classification", None) # default to progression, but none for developing
        return PathOfExileItem(item, classification, self.item_name_to_id[item], self.player)



#def get_items():
#    """
#    Returns a list of all items available in the Path of Exile world.
#    This function can be extended to include specific item definitions.
#    """
#    return items



item_table: Dict[int, ItemDict] = ItemTable.item_table

def get_flask_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a set of all flask items available in the Path of Exile world.
    """
    return [item for item in table.values() if "Flask" in item["category"]]

def get_character_class_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a set of all character class items available in the Path of Exile world.
    """
    return [item for item in table.values() if "Character Class" in item["category"]] 

def get_ascendancy_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a set of all ascendancy items available in the Path of Exile world.
    """
    return [item for item in table.values() if "Ascendancy" in item["category"]]

def get_ascendancy_class_items(class_name: str, table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a set of all ascendancy items available for a specific class in the Path of Exile world.
    """
    return [item for item in table.values() if "Ascendancy" in item["category"] and f"{class_name} Class" in item["category"]]

def get_main_skill_gem_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a set of all main skill gem items available in the Path of Exile world.
    """
    return [item for item in table.values() if "MainSkillGem" in item["category"]]

def get_support_gem_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a set of all support gem items available in the Path of Exile world.
    """
    return [item for item in table.values() if "SupportGem" in item["category"]]

def get_utility_skill_gem_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a set of all utility skill gem items available in the Path of Exile world.
    """
    return [item for item in table.values() if "UtilSkillGem" in item["category"]]

def get_all_gems(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a set of all gem items available in the Path of Exile world.
    This includes main skill gems, support gems, and utility skill gems.
    """
    return get_main_skill_gem_items(table) + get_support_gem_items(table) + get_utility_skill_gem_items(table)

def get_main_skill_gems_by_required_level(level_minimum:int=0, level_maximum:int=100, table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a list of all Main skill gem items available within a specific level range in the Path of Exile world.

    Args:
        level_minimum (int): The minimum required level for the skill gems.
        level_maximum (int): The maximum required level for the skill gems.
    """
    return [item for item in table.values() if "MainSkillGem" in item["category"] and (item["reqLevel"] is not None and (level_minimum <= item["reqLevel"] <= level_maximum))]

def get_main_skill_gems_by_required_level_and_useable_weapon(available_weapons: set[str], level_minimum:int=0, level_maximum:int=100, table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a list of all Main skill gem items available within a specific level range and usable with the provided weapons in the Path of Exile world.

    Args:
        available_weapons (set[str]): A set of weapon items that can be used with the skill gems.
        level_minimum (int): The minimum required level for the skill gems.
        level_maximum (int): The maximum required level for the skill gems.
    """
    return [item for item in table.values() if "MainSkillGem" in item["category"] and (item["reqLevel"] is not None and (level_minimum <= item["reqLevel"] <= level_maximum))
            and (any(weapon in available_weapons for weapon in item.get("reqToUse", [])) or not item.get("reqToUse", []))] # we have the weapon, or there are no reqToUse

def get_gear_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a list of all gear items available in the Path of Exile world.
    """
    return [item for item in table.values() if "Gear" in item["category"]]

def get_armor_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a list of all armor items available in the Path of Exile world.
    """
    return [item for item in table.values() if "Armor" in item["category"]]

def get_weapon_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a list of all weapon items available in the Path of Exile world.
    """
    return [item for item in table.values() if "Weapon" in item["category"]]

def get_max_links_items(table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a list of all max links items available in the Path of Exile world.
    """
    return [item for item in table.values() if "max links" in item["category"]]

def get_by_category(category: str, table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a list of all items in the Path of Exile world that belong to a specific category.

    Args:
        category (str): The category to filter items by.
    """
    return [item for item in table.values() if category in item["category"]]

def get_by_has_every_category(categories: Set[str], table: Dict[int, ItemDict] = item_table) -> list[ItemDict]:
    """
    Returns a list of all items in the Path of Exile world that have every category in the provided set.

    Args:
        categories (Set[str]): A set of categories to filter items by.
    """
    return [item for item in table.values() if all(cat in item["category"] for cat in categories)]

# used to check offhands

quiver_base_types = ItemTable.quiver_base_type_array.copy()  # Copy the list to avoid modifying the original data
shield_base_types = ItemTable.shield_base_type_array.copy() 

# used to check weapon base types
weapon_base_types = [
"Axe",
"Bow",
"Claw",
"Dagger",
"Mace",
"Sceptre",
"Staff",
"Sword",
"Wand",
"Fishing Rod",
]