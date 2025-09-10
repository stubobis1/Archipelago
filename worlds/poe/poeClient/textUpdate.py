import asyncio
import base64
import logging
import random
import re
from NetUtils import ClientStatus
from worlds.poe import Items
from worlds.poe import Locations
from worlds.poe.poeClient import inputHelper
from worlds.poe.poeClient import fileHelper
from worlds.poe import Options
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from worlds.poe.Client import PathOfExileContext
    from worlds.poe import PathOfExileWorld

_debug = True
_random_string = ""
logger = logging.getLogger("poeClient.textUpdate")
SEND_MESSAGE_TIMEOUT = 4
def get_zone_from_line(ctx: "PathOfExileContext", line: str) -> str:
    # Implement the logic for handling self goals here
    match = re.search(r'] : You have entered (.+)\.$', line)
    zone = ""
    if match:
        zone = match.group(1)
    ctx.last_entered_zone = zone
    return zone
  

def get_char_name_and_message_from_line(line: str) -> tuple[str, str]:
    # Extract character name from the line
    match = re.search(r']\s?(<.*>)?\s?(@To|@From)?\s?(.+): (\\x00)?(.*)', line)
    if match:
        if match.group(2) == "@From":
            # We sent this message, so we can ignore it.
            return ("", "")
        return (match.group(3), match.group(5))
    return ("", "")

async def callback_if_valid_char(ctx: "PathOfExileContext", callback: callable):
    global _random_string
    def verify_character_callback(line: str):
        try:
            if _debug:
                logger.info(f"[DEBUG] verify_character_callback: {line}")
            char_name, message = get_char_name_and_message_from_line(line)
            if not f"{_random_string}" in message:
                return
            if not char_name == ctx.character_name:
                logger.info(f"[DEBUG] FALSE ALARM, Chars don't match: char_name={char_name}, ctx.character_name={ctx.character_name}")
                chat_command_external_callbacks.pop(_random_string, None)
                #callback(False)
                return False
            chat_command_external_callbacks.pop(_random_string, None)
            callback()
            return True
        except Exception as e:
            logger.error(f"[ERROR] verify_character_callback failed: {e}")
            return False
    global chat_command_external_callbacks
    chat_command_external_callbacks[_random_string] = verify_character_callback
    _random_string = random.randbytes(2).hex()
    await inputHelper.send_poe_text(f"@{ctx.character_name} {_random_string}")
chat_command_external_callbacks : dict[str, callable]  = dict()

async def chat_commands_callback(ctx: "PathOfExileContext", line: str):
    # Implement the logic for handling self whispers here
    # call each chat command callback with the line
    for callback in chat_command_external_callbacks.values():
        callback(line)
    
    global _random_string
    char_name, message = get_char_name_and_message_from_line(line)
    message = message.lower()

    if "!ap char" in message:
        _random_string = random.randbytes(8).hex()
        await inputHelper.send_poe_text(f"char_{_random_string}") # don't know the char name yet, so we can't whisper.
    if "char_" in message:
        parts = line.split("char_")
        if parts[1] == _random_string:
            if _debug:
                logger.info(f"[DEBUG] self_whisper_callback: {parts}")
            ctx.character_name = char_name
            await inputHelper.send_poe_text_ignore_debounce(f"@{ctx.character_name} Welcome to Archipelago, {ctx.character_name}!")
            await fileHelper.save_settings(ctx)
            return


    if not char_name == ctx.character_name:
        return
    item_ids = [item.item for item in ctx.items_received]
    
    if "!help" in message or "!commands" in message:
            help_message = """!ap char - Set your character | !deathlink | !goal | !passive or !p | !usable skill gems - by level | !usable support gems | !usable utility gems | !usable gems | !main gems | !support gems | !utility gems | !all gems or !gems | !gear | !weapons | !armor | !links | !flasks | !ascendancy | !help | Note: use @yourname followed a command."""
            await split_send_message(ctx, help_message)
            
    if "!main gems" in message:
        # Get all main skill gem items in item_ids
        gems = [item for item in Items.get_main_skill_gem_items() if item["id"] in item_ids] + [i for i in Items.get_by_category("GemModifier") if i["id"] in item_ids]
        # sort by required level
        gems.sort(key=lambda x: x.get("requiredLevel", 0))  # Sort by required level
        await split_send_message(ctx,', '.join(gem['name'] for gem in gems))

    if "!support gems" in message:
        # Get all support gem items in item_ids
        gems = [item for item in Items.get_support_gem_items() if item["id"] in item_ids]
        gems.sort(key=lambda x: x.get("requiredLevel", 0))  # Sort by required level
        await split_send_message(ctx,', '.join(gem['name'] for gem in gems))

    if "!utility gems" in message:
        # Get all utility gem items in item_ids
        gems = [item for item in Items.get_utility_skill_gem_items() if item["id"] in item_ids]
        gems.sort(key=lambda x: x.get("requiredLevel", 0))  # Sort by required level
        await split_send_message(ctx,', '.join(gem['name'] for gem in gems))
        
    if "!all gems" in message or "!gems" in message:
        # Get all gem items in item_ids
        gems = [item for item in Items.get_all_gems() if item["id"] in item_ids] + [i for i in Items.get_by_category("GemModifier") if i["id"] in item_ids]
        gems.sort(key=lambda x: x.get("requiredLevel", 0))  # Sort by required level
        await split_send_message(ctx,', '.join(gem['name'] for gem in gems))

    if "!usable skill gems" in message:
        # Get all usable skill gems in item_ids
        usable_gems = [item for item in Items.get_main_skill_gems_by_required_level(0, ctx.last_character_level) if item["id"] in item_ids]
        usable_gems.sort(key=lambda x: x.get("requiredLevel", 0), reverse=True)  # Sort by required level descending
        await split_send_message(ctx,', '.join(gem['name'] for gem in usable_gems))

    if "!usable support gems" in message:
        # Get all usable skill gems in item_ids
        usable_gems = [item for item in Items.get_support_gems_by_required_level(0, ctx.last_character_level) if item["id"] in item_ids]
        usable_gems.sort(key=lambda x: x.get("requiredLevel", 0), reverse=True)  # Sort by required level descending
        await split_send_message(ctx,', '.join(gem['name'] for gem in usable_gems))

    if "!usable utility gems" in message:
        # Get all usable utility gems in item_ids
        usable_gems = [item for item in Items.get_utility_skill_gems_by_required_level(0, ctx.last_character_level) if item["id"] in item_ids]
        usable_gems.sort(key=lambda x: x.get("requiredLevel", 0), reverse=True)  # Sort by required level descending
        await split_send_message(ctx,', '.join(gem['name'] for gem in usable_gems))

    if "!usable gems" in message:
        # Get all usable gems in item_ids
        usable_gems = [item for item in Items.get_all_gems_by_required_level(0, ctx.last_character_level) if item["id"] in item_ids]
        usable_gems.sort(key=lambda x: x.get("requiredLevel", 0), reverse=True)  # Sort by required level descending
        await split_send_message(ctx,', '.join(gem['name'] for gem in usable_gems))

    if "!gear" in message:
        # Get all gear items in item_ids
        gear = [item for item in Items.get_gear_items() if item["id"] in item_ids]
        progressive_message = build_progressive_message(gear)
        singles = ', '.join(gear['name'] for gear in gear if "Progressive" not in gear["category"])
        await split_send_message(ctx, progressive_message + (', and ' + singles if singles else '' ))

    if "!links" in message:
        # Get all linked items in item_ids
        links = [item for item in Items.get_max_links_items() if item["id"] in item_ids]
        link_counts: dict[str, int] = {}
        
        # Count each occurrence of each link item
        for item_id in item_ids:
            # Find the link item with this ID
            link_item = next((item for item in Items.get_max_links_items() if item["id"] == item_id), None)
            if link_item:
                link_counts[link_item["name"]] = link_counts.get(link_item["name"], 0) + 1
        
        if link_counts:
            link_message = ', '.join(f"{name}: {count}" for name, count in link_counts.items())
        else:
            link_message = "No links"
        
        await split_send_message(ctx, link_message)

    if "!flasks" in message or "!flask" in message:
        # Get all flask items in item_ids
        flask_counts: dict[str, int] = {}
        
        # Count each occurrence of each flask item
        for item_id in item_ids:
            # Find the flask item with this ID
            flask_item = next((item for item in Items.get_flask_items() if item["id"] == item_id), None)
            if flask_item:
                flask_counts[flask_item["name"]] = flask_counts.get(flask_item["name"], 0) + 1

        # Create a message with flask names and counts
        if flask_counts:
            flask_message = ', '.join(f"{name}: {count}" for name, count in flask_counts.items())
        else:
            flask_message = "No flasks"

        await split_send_message(ctx, flask_message)

    if "!ascendancy" in message:
        # Get all ascendancy items in item_ids
        ascendancy = [item for item in Items.get_ascendancy_items() if item["id"] in item_ids]
        await split_send_message(ctx,', '.join(ascendancy['name'] for ascendancy in ascendancy))

    if "!weapons" in message:
        # Get all weapon items in item_ids
        weapons = [item for item in Items.get_weapon_items() if item["id"] in item_ids]
        progressive_message = build_progressive_message(weapons)
        singles = ', '.join(weapons['name'] for weapons in weapons if "Progressive" not in weapons["category"])
        await split_send_message(ctx, progressive_message + (', and ' + singles if singles else '' ))

    if "!armor" in message:
        # Get all armor items in item_ids
        armor = [item for item in Items.get_armor_items() if item["id"] in item_ids]
        progressive_message = build_progressive_message(armor)
        singles = ', '.join(armor['name'] for armor in armor if "Progressive" not in armor["category"])
        await split_send_message(ctx, progressive_message + (', and ' + singles if singles else '' ))

    if "!passive" in message or "!p" in message:
        message = f"You have {ctx.passives_available - ctx.passives_used} passive skill points available. ( {ctx.passives_used} / {ctx.passives_available} total for character {ctx.character_name} )"
        await split_send_message(ctx, message)
    
    if "!deathlink" in message:
        # If the user has deathlink enabled, send a message to the server to enable deathlink
        deathlinked = ctx.get_is_death_linked()
        await ctx.update_death_link(not deathlinked)
        await split_send_message(ctx, f"Deathlink {"enabled" if not deathlinked else "disabled"}.")
        
    if "!goal" in message:
        await send_goal_message(ctx)

def build_progressive_message(items: list["ItemDict"]) -> str:
    progressive_count: dict[str, int] = {}
    progressive_message = ""
    for item in items:
        if "Progressive" in item["category"]:
            progressive_count[item["name"]] = progressive_count.get(item["name"], 0) + 1
    for name, count in progressive_count.items():
        progressive_message += f"{rarity_from_progressive_count(count)} {name.replace("Progressive ", "")}, "
    return progressive_message.rstrip(", ")

def rarity_from_progressive_count(count: int) -> str:
    if count == 1:
        return "Normal"
    elif count == 2:
        return "up to Magic"
    elif count == 3:
        return "up to Rare"
    elif count == 4:
        return "Any"
    else:
        return ""

async def send_goal_message(ctx):
    goal = ctx.game_options.get("goal", -1)
    goal_message = ""
    if goal == Options.Goal.option_complete_act_1:
        goal_message = "Goal: Complete Act 1 (reach The Southern Forest)"
    elif goal == Options.Goal.option_complete_act_2:
        goal_message = "Goal: Complete Act 2 (reach The City of Sarn)"
    elif goal == Options.Goal.option_complete_act_3:
        goal_message = "Goal: Complete Act 3 (reach The Aqueduct)"
    elif goal == Options.Goal.option_complete_act_4:
        goal_message = "Goal: Complete Act 4 (reach The Slave Pens)"
    elif goal == Options.Goal.option_kauri_fortress_act_6:
        goal_message = "Goal: Reach Karui Fortress in Act 6"
    elif goal == Options.Goal.option_complete_act_6:
        goal_message = "Goal: Complete Act 6 (reach The Bridge Encampment)"
    elif goal == Options.Goal.option_complete_act_7:
        goal_message = "Goal: Complete Act 7 (reach The Sarn Ramparts)"
    elif goal == Options.Goal.option_complete_act_8:
        goal_message = "Goal: Complete Act 8 (reach The Blood Aqueduct)"
    elif goal == Options.Goal.option_complete_act_9:
        goal_message = "Goal: Complete Act 9 (reach Oriath Docks)"
    elif goal == Options.Goal.option_complete_the_campaign:
        goal_message = "Goal: Complete the campaign (reach Karui Shores)"
    elif goal == Options.Goal.option_defeat_bosses:
        # Show boss defeat progress using the same logic as validationLogic
        bosses_for_goal = ctx.game_options.get("bosses_for_goal", [])
        if not bosses_for_goal:
            goal_message = "Goal: Defeat bosses (no bosses configured)"
        else:
            # Get completion items we've received
            received_item_names = set()
            for network_item in ctx.items_received:
                item_data = [i for i in Locations.bosses.values() if i.get("id") == network_item.item]
                if item_data:
                    received_item_names.add(item_data[0]["name"])

            # Find bosses we haven't completed yet
            incomplete_bosses = []
            complete_bosses = []
            for boss in bosses_for_goal:
                completion_item = f"defeat {boss}"
                if completion_item not in received_item_names:
                    incomplete_bosses.append(boss)
                else:
                    complete_bosses.append(boss)

            if incomplete_bosses:
                goal_message = f"Goal: Defeat bosses - ✗{', ✗'.join(incomplete_bosses)}" + (f"  ✓{', ✓'.join(complete_bosses)}" if complete_bosses else "")
            else:
                goal_message = "Goal: Defeat bosses - All bosses completed!"
    else:
        goal_message = "Goal: Unknown or not set"
    await split_send_message(ctx=ctx, message=goal_message)


async def split_send_message(ctx, message: str, max_length: int = 500):
    """
    Splits a message into chunks and sends each chunk separately.
    """
    if not message:
        message = "None"
    prefix = f"@{ctx.character_name} "
    max_length = max_length - len(prefix)  # Adjust for character name prefix
    if len(message) <= max_length:
        await asyncio.wait_for(inputHelper.send_poe_text(prefix + message), SEND_MESSAGE_TIMEOUT)
        return

    # Split the message into chunks, only at a comma
    chunks = [message[i:i + max_length] for i in range(0, len(message), max_length)]
    
    # Send each chunk
    for chunk in chunks:
        await asyncio.wait_for(inputHelper.send_poe_text(prefix + chunk, retry_times=len(chunks) + 1, retry_delay=0.5), SEND_MESSAGE_TIMEOUT * len(chunks))

async def deathlink_callback(ctx:"PathOfExileContext", line: str):
    if not ctx.character_name:
        return
    if f"{ctx.character_name.lower()} has been slain." in line.lower():
        await asyncio.wait_for(ctx.send_death(f"{ctx.character_name} level {ctx.last_character_level} has been slain in {ctx.last_entered_zone}."), SEND_MESSAGE_TIMEOUT)

# not really related to text updates, but this is the only place where it fits.
async def receive_deathlink(ctx: "PathOfExileContext"):
    await inputHelper.important_send_poe_text(f"/exit")