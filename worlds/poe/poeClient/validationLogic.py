import asyncio

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from worlds.poe.Client import PathOfExileContext
    from worlds.poe import PathOfExileWorld
from . import itemFilter
from . import baseItemTypes
from . import gggAPI
from . import fileHelper
from . import inputHelper
from . import tts

import worlds.poe.Items as Items
import worlds.poe.Locations as Locations

found_items_dict = {}
found_items_set = set()
save_path = "found_items.txt"
total_items = set()
is_char_in_logic = True

_debug = True
_verbose_debug = False
total_items.update(baseItemTypes.get_base_item_types())

async def when_enter_new_zone(line: str, context: "PathOfExileContext" = None):
    """
    Callback function that is called when a new zone is entered.
    It validates the character and updates the item filter accordingly.

    Args:
        line (str): The line from the log file indicating the new zone entry.
    """
    if not "] : You have entered" in line:
        return
    global is_char_in_logic
    await validate_and_update(ctx=context)
    await asyncio.sleep(0.5)  # Allow some time for the filter to update
    await inputHelper.send_poe_text("/itemfilter __ap")

async def validate_and_update(ctx: "PathOfExileContext" = None) -> bool:
    if ctx is None:
        # something is wrong, are we not connected?
        print("Context is None, cannot validate character.")
        return False
    character_name = ctx.character_name
    char = {}
    try: 
        char = (await gggAPI.get_character(character_name)).character
        ctx.last_response_from_api.setdefault("character",{})[ctx.character_name] = char
    except Exception as e:
        print(f"Error fetching character {character_name}: {e}")
        raise e
    
    global is_char_in_logic
    validate_errors = await validate_char(char, ctx)

    is_char_in_logic = True if len(validate_errors) == 0 else False


    if is_char_in_logic:
        locations_to_check = set()
        found_items_set = get_found_items(char)
        for item in found_items_set:
            if _debug and _verbose_debug:
                print(f"[DEBUG] Found item: {item}")
            location_id = Locations.get_location_id_from_item_name(item)
            if location_id is not None:
                locations_to_check.add(location_id)
        await update_filter(ctx)
        if len(locations_to_check) > 0:
            if _debug:
                print(f"[DEBUG] Locations to check: {locations_to_check}")
            await ctx.check_locations(locations_to_check)
#           await ctx.send_msgs([{"cmd": 'LocationChecks', "locations": tuple(locations_to_check)}])
        else:
            if _debug:
                print("[DEBUG] No locations to check, skipping check_locations.")
        await update_filter(ctx)
        return True

    else:
        await update_filter_to_invalid_char_filter(validate_errors)
        return False



async def validate_char(character: gggAPI.Character, ctx: "PathOfExileContext") -> list[str]:
    # Perform validation logic here

    if character is None:
        print("Character is None, cannot validate.")
        return False

    errors = list()

    total_recieved_items = list()
    for network_item in ctx.items_received:
        total_recieved_items.append(Items.item_table.get(network_item.item))

    simple_equipment_slots = ["BodyArmour","Amulet","Belt","Boots","Gloves","Helmet"]

    normal_flask_count = 0
    magic_flask_count = 0
    unique_flask_count = 0

    if character.class_ not in [i["name"] for i in total_recieved_items]:
        errors.append(f"Class {character.class_}")

    gucci_rarity_check = {}
    for equipped_item in character.equipment:
        rarity = equipped_item.rarity
        gucci_rarity_check.setdefault(rarity, 0)
        gucci_rarity_check[rarity] += 1
        # simple checks.
        for slot in simple_equipment_slots:
            if equipped_item.inventoryId == slot:
                errors.append(rarity_check(total_recieved_items, rarity, slot))
                
        if equipped_item.inventoryId == "Ring":
            errors.append(rarity_check(total_recieved_items, rarity, "Ring (left)"))
        if equipped_item.inventoryId == "Ring2":
            errors.append(rarity_check(total_recieved_items, rarity, "Ring (right)"))
        if equipped_item.inventoryId == "Offhand":
            if equipped_item.baseType in Items.quiver_base_types:
                errors.append(rarity_check(total_recieved_items, rarity, "Quiver"))
            else:
                errors.append(rarity_check(total_recieved_items, rarity, "Shield"))
        if equipped_item.inventoryId == "Weapon":
            for prop in equipped_item.properties:
                prop_name = prop.name
                for weapon_base_type in Items.weapon_base_types:
                    if prop_name.lower().endswith(weapon_base_type.lower()):
                        errors.append(rarity_check(total_recieved_items, rarity, weapon_base_type))

        equipped_sockets = 0
        if equipped_item.socketedItems is not None:
            for socketed_item in equipped_item.socketedItems:
                if socketed_item.support:
                    equipped_sockets += 1
                if socketed_item.baseType not in [i["name"] for i in total_recieved_items]:
                    errors.append(f"Socketed {socketed_item.baseType} in {equipped_item.inventoryId}")

        links = [i["name"] for i in total_recieved_items if i["name"] == f"Progressive max links - {equipped_item.baseType}"]
        if len(links) < equipped_sockets - 1: # -1 for the skill gem
            errors.append(f"Too many links for {equipped_item.baseType}")

        if equipped_item.inventoryId == "Flask":
            flask_rarity = equipped_item.rarity
            if flask_rarity == "Normal":
                normal_flask_count += 1
            elif flask_rarity == "Magic":
                magic_flask_count += 1
            elif flask_rarity == "Unique":
                unique_flask_count += 1
                
    # get count of items.name that match the progressive unlocks
    if normal_flask_count > len([i["name"] for i in total_recieved_items if i["name"] == 'Progressive Flask Unlock Slot']):
        errors.append("Normal Flasks")
    if magic_flask_count > len([i["name"] for i in total_recieved_items if i["name"] == 'Progressive Magic Flask Unlock']):
        errors.append("Magic Flasks")
    if unique_flask_count > len([i["name"] for i in total_recieved_items if i["name"] == 'Progressive Unique Flask Unlock']):
        errors.append("Unique Flasks")

    gucci_hobo_mode = ctx.slot_info.get("gucci_hobo_mode", False)
    if gucci_hobo_mode == 1 or gucci_hobo_mode == 2 or gucci_hobo_mode ==3:
        normal_gear = gucci_rarity_check.setdefault("Normal", 0)
        magic_gear = gucci_rarity_check.setdefault("Magic", 0)
        rare_gear = gucci_rarity_check.setdefault("Rare", 0)
        if gucci_hobo_mode == 1 and  normal_gear + magic_gear + rare_gear > 1: #options_allow_one_slot_of_any_rarity
            errors.append("Gucci Hobo Mode - Only one item allowed of any rarity")
        if gucci_hobo_mode == 2 and (normal_gear > 1 or magic_gear + rare_gear > 0):  # options_allow_one_slot_of_normal_rarity
            errors.append("Gucci Hobo Mode - Only one normal item allowed")
        if gucci_hobo_mode == 3 and (normal_gear + magic_gear + rare_gear > 0): # option_no_non_unique_items
            errors.append("Gucci Hobo Mode - No non-unique items allowed")

    errors = [x for x in errors if x]  # filter out empty strings
    if _debug and errors:
        print("YOU ARE OUT OF LOGIC: " + ", ".join(errors))
        print("YOU ARE OUT OF LOGIC: " + ", ".join(errors))
        print("YOU ARE OUT OF LOGIC: " + ", ".join(errors))
        print("YOU ARE OUT OF LOGIC: " + ", ".join(errors))
        print("YOU ARE OUT OF LOGIC: " + ", ".join(errors))
    return errors
    

def rarity_check(total_recieved_items, rarity: str, equipmentId: str) -> str | None:
    valid = True
    if rarity == "Unique":
        valid = True if f"Unique {equipmentId}" in [i["name"] for i in total_recieved_items] else False
    elif rarity == "Rare":
        valid = True if f"Rare {equipmentId}" in [i["name"] for i in total_recieved_items] else False
    elif rarity == "Magic":
        valid = True if f"Magic {equipmentId}" in [i["name"] for i in total_recieved_items] else False
    else:
        valid = True if f"Normal {equipmentId}" in [i["name"] for i in total_recieved_items] else False
    
    if not valid:
        return equipmentId
    else: 
        return None


async def update_filter(ctx: "PathOfExileContext") -> bool:
    item_filter_string = ""
    missing_location_ids = ctx.missing_locations
    for base_item_location_id in missing_location_ids:

#        item_text = Items.get(base_item_location_id, "Unknown Item") # this needs to be the scouted item name, unless the options specify otherwise
        network_item = ctx.locations_info[base_item_location_id]
        item_text = tts.get_item_name_tts_text(ctx, network_item)
        filename =  f"{item_text.lower()}_{tts.WPM}.wav"
        base_item_location_name = ctx.location_names.lookup_in_game(base_item_location_id)
        item_filter_string += itemFilter.generate_item_filter_block(base_item_location_name, f"{itemFilter.filter_sounds_dir_name}/{fileHelper.safe_filename(filename)}")+ "\n\n"

    if item_filter_string:
        itemFilter.write_item_filter(item_filter_string)
        print(f"Item filter updated with {len(missing_location_ids)} items.")
    return True

async def update_filter_to_invalid_char_filter(errors: list[str]):
    if len(errors) > 1:
        error_text = " ... and ".join(errors)
    else:
        error_text = errors[0]
    filename = f"{fileHelper.short_hash(error_text)}_{tts.WPM}.wav" # this could be a long text, so we use a hash
    await tts.safe_tts_async(
        text=f"YOU ARE OUT OF LOGIC: {error_text}",
        filename=itemFilter.filter_sounds_path / f"{filename}",
        rate=tts.WPM
    )
    invalid_item_filter_string = itemFilter.generate_invalid_item_filter_block(f"{itemFilter.filter_sounds_dir_name}/{filename}")
    itemFilter.write_item_filter(invalid_item_filter_string, item_filter_import=None)


def get_found_items(char: gggAPI.Character) -> set:
    """
    Fetches the found items for a given character from the GGG API.

    Args:
        char (gggAPI.Character): The character to fetch items for.

    Returns:
        dict: A dictionary containing the found items.
    """
    try:
        for item in char.inventory:
            found_items_set.add(item.baseType)
            if _debug and _verbose_debug:
                print(f"[DEBUG] Item in inventory: {item.baseType}")
    except Exception as e:
        print(f"Error fetching found items: {e}")
        raise e
    return found_items_set

async def load_found_items_from_file(file_path: str = save_path ) -> set:
    """
    Loads the found items from a file.
    Returns:
        set: A set containing the found items.
    """
    global found_items_set
    found_set = set()
    try:
        found_set = await fileHelper.read_set_from_file(file_path)
    except Exception as e:
        print(f"Error loading found items: {e}")

    found_items_set.update(found_set)
    return found_items_set