import logging
import typing
import random

from BaseClasses import ItemClassification

if typing.TYPE_CHECKING:
    from worlds.poe.Client import PathOfExileContext
from pathlib import Path
from worlds.poe.Locations import base_item_locations_by_base_item_name, LocationDict
from worlds.poe import Locations
from worlds.poe.Options import PathOfExileOptions, LootFilterDisplay, LootFilterSounds
import Utils

logger = logging.getLogger("poeClient.itemFilter")

AP_FILTER_NAME = "__ap"
INVALID_FILTER_NAME = "__invalid"
TTS_FILTER_SOUNDS_DIR_NAME = "_ap_tts"
JINGLE_FILTER_SOUNDS_DIR_NAME = "_ap_jingle"
start_item_filter_block = "# <Base Item Hunt item>"
end_item_filter_block = "# </Base Item Hunt item>"

DEFAULT_POE_DOC_PATH = Path.home() / "Documents" / "My Games" / "Path of Exile"

if Utils.is_windows:
    from win32com.shell import shell, shellcon
    # Use modern SHGetKnownFolderPath for better compatibility
    docs_path = Path(shell.SHGetKnownFolderPath(shellcon.FOLDERID_Documents, 0, None))
    if docs_path.exists():
        DEFAULT_POE_DOC_PATH = docs_path / "My Games" / "Path of Exile"
    else:
        logging.error("Windows Documents path not found, using hardcoded fallback.")

poe_doc_path = DEFAULT_POE_DOC_PATH

def set_poe_doc_path(new_path: Path | str) -> None:
    global poe_doc_path
    if isinstance(new_path, str):
        new_path = Path(new_path)

    if not new_path.exists() or not new_path.is_dir():
        logger.error(f"[ERROR] {new_path} is not a directory, using the old path: {poe_doc_path}")
        return

    poe_doc_path = new_path



#Archipelago Colors
# red = 201 117 130 255
# yellow = 238 227 147 255
# green = 117 194 116 255
# blue = 118 126 189 255
# purp = 201 148 194 255
# orange = 216 160 125 255
progressive_style_string = f"""
SetFontSize 45
SetTextColor 201 117 130 255
SetBorderColor 117 194 116 255
SetBackgroundColor 238 227 147 255
MinimapIcon 0 Green UpsideDownHouse
PlayEffect Cyan
"""
default_style_string = f"""
SetFontSize 38
SetTextColor 201 117 130 255
SetBorderColor 117 194 116 255
SetBackgroundColor 238 227 147 225
MinimapIcon 1 Green UpsideDownHouse
PlayEffect Cyan Temp
"""
filler_style_string = f"""
SetFontSize 31
SetTextColor 201 117 130 255
SetBorderColor 117 194 116 255
SetBackgroundColor 238 227 147 200
MinimapIcon 2 Green UpsideDownHouse
"""
trap_style_string = f"""
SetFontSize 45
SetBackgroundColor 201 117 130 255
SetBorderColor 117 194 116 255
SetTextColor 238 227 147 255
MinimapIcon 2 Red Cross
PlayEffect Red Temp
"""
invalid_style_string = f"""
SetTextColor 255 0 0 0
SetBorderColor 255 0 0 255
SetBackgroundColor 255 0 0 255
"""

minimap_icon_shapes = ["Circle", "Diamond", "Hexagon", "Square", "Star", "Triangle", "Cross", "Moon", "Raindrop", "Kite", "Pentagon", "UpsideDownHouse"]
minimap_icon_colors = ["Red", "Green", "Blue", "Brown", "White", "Yellow", "Cyan", "Grey", "Orange", "Pink", "Purple"]
minimap_play_effect = ["Red", "Green", "Blue", "Brown", "White", "Yellow", "Cyan", "Grey", "Orange", "Pink", "Purple"]
def get_random_style_string() -> str:
    style = ""
    style += f"SetFontSize {random.randint(28, 45)}\n"
    style += f"SetTextColor {random.randint(0, 255)} {random.randint(0, 255)} {random.randint(0, 255)} {random.randint(180, 255)}\n"
    style += f"SetBorderColor {random.randint(0, 255)} {random.randint(0, 255)} {random.randint(0, 255)} {random.randint(0, 255)}\n"
    style += f"SetBackgroundColor {random.randint(0, 255)} {random.randint(0, 255)} {random.randint(0, 255)} {random.randint(100, 255)}\n"
    style += f"MinimapIcon {random.randint(0,2)} {random.choice(minimap_icon_colors)} {random.choice(minimap_icon_shapes)}\n"
    style += f"PlayEffect {random.choice(minimap_play_effect)}\n"
    return style


def get_style_string_for_classification(classification: int) -> str:
    if classification == ItemClassification.progression:
        return progressive_style_string
    elif classification == ItemClassification.filler:
        return filler_style_string
    elif classification == ItemClassification.useful:
        return default_style_string
    elif classification == ItemClassification.trap:
        return trap_style_string
    else:
        return default_style_string


def get_progression_by_flag(flags: int):
    if flags & 0b001:  # progression
        return ItemClassification.progression
    elif flags & 0b010:  # useful
        return ItemClassification.useful
    elif flags & 0b100:  # trap
        return ItemClassification.trap
    else:
        return ItemClassification.filler

_debug = True
base_item_id_to_relative_tts_wav_path = {}

_valid_base_item_filter_paths = set() # just to speed up the check

def update_item_filter_from_context(ctx : "PathOfExileContext", exclude_locations: set[int]|None = None) -> None:
    """
    Generates an item filter based on the current context.
    This function will create a filter that shows items based on their base type and alert sound.
    """
    global base_item_id_to_relative_tts_wav_path
    item_filter_str = ""
    for base_item_location_id in ctx.locations_info:
        # Check if the location has been checked already, if so, skip it
        if base_item_location_id in ctx.checked_locations or \
           (exclude_locations and base_item_location_id in exclude_locations):
            continue
        
        base_type: LocationDict = Locations.base_item_type_locations.get(base_item_location_id, {})
        base_type_name: str = base_type.get("baseItem", None)
        if not base_type_name or base_type_name not in Locations.base_item_names_set: 
            continue # other locations that aren't item filter items 

        # get progression and style
        progression: ItemClassification
        style_string = ""
        if ctx.filter_options.loot_filter_display == LootFilterDisplay.option_show_classification:
            progression = get_progression_by_flag(ctx.locations_info[base_item_location_id].flags)
            style_string = get_style_string_for_classification(progression)
        elif ctx.filter_options.loot_filter_display == LootFilterDisplay.option_hide_classification:
            progression = ItemClassification.progression  # always use progression style
            style_string = get_style_string_for_classification(progression)
        else: #ctx.filter_options.loot_filter_display == LootFilterDisplay.option_randomize_lootfilter_style:
            progression = random.choice([ItemClassification.progression, ItemClassification.skip_balancing , ItemClassification.useful, ItemClassification.filler, ItemClassification.trap])
            style_string = get_random_style_string()

        relative_wav_path = None
        write_wav = False  # Initialize to default value
        if ctx.filter_options.tts_enabled or ctx.filter_options.loot_filter_sounds != LootFilterSounds.option_no_sound:
            write_wav = True

            if ctx.filter_options.loot_filter_sounds == LootFilterSounds.option_TTS:
                relative_wav_path = base_item_id_to_relative_tts_wav_path.get(base_item_location_id, None)
            elif ctx.filter_options.loot_filter_sounds == LootFilterSounds.option_jingles:
                if progression == ItemClassification.progression:
                    relative_wav_path = poe_doc_path / JINGLE_FILTER_SOUNDS_DIR_NAME / "Progression.wav"
                elif progression == ItemClassification.useful:
                    relative_wav_path = poe_doc_path / JINGLE_FILTER_SOUNDS_DIR_NAME / "Useful.wav"
                elif progression == ItemClassification.trap:
                    relative_wav_path = poe_doc_path / JINGLE_FILTER_SOUNDS_DIR_NAME / "Trap.wav"
                elif progression == ItemClassification.filler:
                    relative_wav_path = poe_doc_path / JINGLE_FILTER_SOUNDS_DIR_NAME / "Filler.wav"
                elif progression == ItemClassification.skip_balancing: # this should actually be 0b00011 intead (prog | useful), but this is easy and its only used here
                    relative_wav_path = poe_doc_path / JINGLE_FILTER_SOUNDS_DIR_NAME / "ProgUseful.wav" 

            if relative_wav_path is None:
                logger.error(f"[ERROR] No wav path found! base item location ID: {base_item_location_id}. progression: {progression}.")
                write_wav = False


        if write_wav:
            item_filter_str += generate_item_filter_block(base_type_name, alert_sound=relative_wav_path, style_string=style_string) + "\n\n"
        else:
            item_filter_str += generate_item_filter_block_without_sound(base_type_name, style_string=style_string) + "\n\n"
    write_item_filter(item_filter_str, item_filter_import=ctx.base_item_filter)

def generate_item_filter_block(base_type_name, alert_sound, style_string=default_style_string) -> str:
    if base_type_name not in base_item_locations_by_base_item_name:
        logger.error(f"[ERROR] Base type '{base_type_name}' not found in item table.")
        return ""
    if not Path.exists(poe_doc_path / alert_sound):
        logger.error(f"[ERROR] baseitem Alert sound '{alert_sound}' does not exist.")
        return generate_item_filter_block_without_sound(base_type_name=base_type_name, style_string=style_string)
    return f"""
{start_item_filter_block}
Show 
BaseType == "{base_type_name}"
{style_string}
CustomAlertSoundOptional "{alert_sound}" 300
{end_item_filter_block}"""

def generate_item_filter_block_without_sound(base_type_name, style_string=default_style_string) -> str:
    return f"""
{start_item_filter_block}
Show 
BaseType == "{base_type_name}"
{style_string}
{end_item_filter_block}"""


def generate_invalid_item_filter_block(alert_sound) -> str:
    if not Path.exists(poe_doc_path / alert_sound):
        logger.error(f"[ERROR] 'Invalid state' Alert sound '{alert_sound}' does not exist.")
        return generate_invalid_item_filter_block_without_sound()
    return f"""
Show 
{invalid_style_string}
CustomAlertSoundOptional "{alert_sound}" 300
"""

def generate_invalid_item_filter_block_without_sound() -> str:
    return f"""
    Show 
    {invalid_style_string}
    """

def write_item_filter(item_filter:str, item_filter_import:str|None=None, file_path: Path = (poe_doc_path / f"{AP_FILTER_NAME}.filter")) -> None:
    if item_filter_import == INVALID_FILTER_NAME or item_filter_import == AP_FILTER_NAME:
        logger.error(f"\n\n-------- THIS SHOULD NEVER HAPPEN -----------\n Not writing base item filter because import path '{item_filter_import}' is reserved.")
        item_filter_import = None
    write_filter = False
    if item_filter_import is None:
        item_filter_import = ""

    if item_filter_import and item_filter_import in _valid_base_item_filter_paths:
        write_filter = True

    if not write_filter and item_filter_import and Path.exists(poe_doc_path / item_filter_import):
        # If the import path exists, we can use it
        _valid_base_item_filter_paths.add(item_filter_import)
        write_filter = True

    if not write_filter:
            logger.debug(f"Not writing base item filter because import path '{item_filter_import}' is not valid or does not exist (this is fine, there just isn't a backup item filter).")

    if write_filter:
        item_filter = f"""{item_filter}
    Import "{item_filter_import}"
    """

    with open(str(file_path), "w", encoding="utf-8") as f:
        f.write(item_filter)
    logger.debug(f"Item filter written to {file_path} with base filter {item_filter_import}")