
# red = 201 117 130 255
# yellow = 238 227 147 255
# green = 117 194 116 255
# blue = 118 126 189 255
# purp = 201 148 194 255
#orange = 216 160 125 255
from pathlib import Path
from worlds.poe.Locations import base_item_types_by_name
filter_file_dir = Path.home() / "Documents" / "My Games" / "Path of Exile"
filter_file_path = Path.home() / "Documents" / "My Games" / "Path of Exile" / "__ap.filter"
filter_sounds_dir_name = "apsound"
filter_sounds_path = filter_file_dir / filter_sounds_dir_name
start_item_filter_block = "# <Base Item Hunt item>"
end_item_filter_block = "# </Base Item Hunt item>"
base_item_filter_import = "normalLocal.filter"
default_style_string = f"""SetFontSize 45
SetFontSize 45
SetTextColor 201 117 130 255
SetBorderColor 117 194 116 255
SetBackgroundColor 238 227 147 255
MinimapIcon 0 Green UpsideDownHouse
PlayEffect Cyan
"""
invalid_style_string = f"""SetFontSize 45
SetTextColor 255 255 0 0
SetBorderColor 255 255 0 0
SetBackgroundColor 255 255 0 0
"""
_debug = True
base_item_to_relative_wav_path = {}
def generate_item_filter_block(base_type_name, alert_sound, style_string=default_style_string):
    if base_type_name not in base_item_types_by_name:
        print(f"[ERROR] Base type '{base_type_name}' not found in item table.")
        return ""
    if not Path.exists(filter_file_dir / alert_sound):
        print(f"[ERROR] Alert sound '{alert_sound}' does not exist in {filter_sounds_path}.")
        return generate_item_filter_block_without_sound(base_type_name)
    return f"""
{start_item_filter_block}
Show 
BaseType == "{base_type_name}"
{style_string}
CustomAlertSound "{alert_sound}" 300
{end_item_filter_block}"""

def generate_item_filter_block_without_sound(base_type_name, style_string=default_style_string):
    return f"""
{start_item_filter_block}
Show 
BaseType == "{base_type_name}"
{style_string}
{end_item_filter_block}"""


def generate_invalid_item_filter_block(alert_sound):
    if not Path.exists(filter_file_dir / alert_sound):
        print(f"[ERROR] Alert sound '{alert_sound}' does not exist in {filter_sounds_path}.")
        return generate_invalid_item_filter_block_without_sound()
    return f"""
Show 
{invalid_style_string}
CustomAlertSound "{alert_sound}" 300
"""

def generate_invalid_item_filter_block_without_sound():
    return f"""
    Show 
    {invalid_style_string}
    """

def write_item_filter(item_filter:str, item_filter_import=base_item_filter_import, file_path: Path = filter_file_path):
    if item_filter_import is not None:
        item_filter = f"""{item_filter}
    Import "{item_filter_import}"
    """
    with open(str(file_path), "w", encoding="utf-8") as f:
        f.write(item_filter)
    if _debug:
        print(f"[DEBUG] Item filter written to {file_path} with base filter {item_filter_import}")