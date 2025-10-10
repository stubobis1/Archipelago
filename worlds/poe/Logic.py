from typing import Dict, Set
from worlds.LauncherComponents import components, Component, launch_subprocess, Type, icon_paths
from BaseClasses import Region, MultiWorld, Item, Location, LocationProgressType, ItemClassification
from worlds.AutoWorld import World, WebWorld
from Utils import visualize_regions
import logging

from .Options import PathOfExileOptions
from . import Items
from .data import ItemTable
from . import Locations
from . import Regions as poeRegions
from . import Rules as poeRules
from . import Options
from .Version import POE_VERSION

import typing

if typing.TYPE_CHECKING:
    from worlds.poe import PathOfExileWorld
    from worlds.poe.Options import PathOfExileOptions

logger = logging.getLogger("poe.logic")
logger.setLevel(logging.INFO)

def generate_items_logic(world: "PathOfExileWorld"):

       # # Clear performance cache for fresh generation
       # from . import Rules as poeRules
       # poeRules.clear_item_cache()
        
        opt: PathOfExileOptions = world.options
        world.goal_act = get_goal_act(world, opt)

        if opt.goal.value == opt.goal.option_defeat_bosses:
            if opt.bosses_available.value is None or len(opt.bosses_available.value) == 0:
                opt.bosses_available.value = list(Locations.bosses.keys())

            bosses_to_kill = min(opt.number_of_bosses, len(Locations.bosses), len(opt.bosses_available.value))

            world.bosses_for_goal = world.random.sample(sorted(opt.bosses_available.value), bosses_to_kill)

        setup_early_items(world)

        world.items_to_place = Items.deprioritize_non_logic_gems(world, world.items_to_place)
        # world.items_to_place = Items.deprioritize_non_logic_gear(world, world.items_to_place) # this can lead to some generation issues, so not doing it for now.

        world.total_items_to_place_count = sum(item.get("count", 1) for item in world.items_to_place.values())
        world.locations_to_place = poeRules.SelectLocationsToAdd(world=world, target_amount=world.total_items_to_place_count)

        fake_generation = hasattr(world.multiworld, "generation_is_fake")
        if fake_generation:  # This is to add support for Universal Tracker
            logger.debug(f"Generating with all locations, seeing generation_is_fake")
            world.locations_to_place: list[Locations.LocationDict] = list(Locations.full_locations.values())
            world.bosses_for_goal = list(Locations.bosses.keys())

        table_total_item_count = sum(item.get("count", 1) for item in Items.item_table.values())
        if len(world.locations_to_place) <  world.total_items_to_place_count:
            logger.debug(
                f"[POE]: Not enough locations to place all items! locations: {len(world.locations_to_place)} < items: {table_total_item_count}\nCulling...")
            world.total_items_to_place_count = sum(item.get("count", 1) for item in world.items_to_place.values())
            logger.debug(
                f"[POE]: total items to place before culling: {world.total_items_to_place_count} / {table_total_item_count} possible")
            world.items_to_place = Items.cull_items_to_place(world, world.items_to_place, world.locations_to_place)
            world.total_items_to_place_count = sum(item.get("count", 1) for item in world.items_to_place.values())
            logger.debug(
                f"[POE]: total items to place after  culling: {world.total_items_to_place_count} / {table_total_item_count} possible")


        table_total_item_count = sum(item.get("count", 1) for item in Items.item_table.values())
        logger.debug(f"[POE]: total items to place: {world.total_items_to_place_count} / {table_total_item_count} possible")
        logger.debug(f"[POE]: total locs in world.: {len(world.locations_to_place)} / {len(Locations.full_locations)} possible")




def setup_early_items(world: "PathOfExileWorld"):
    options: PathOfExileOptions = world.options
    setup_character_items(world)
    max_level = Locations.acts[world.goal_act]["maxMonsterLevel"]

    if options.gucci_hobo_mode.value != options.gucci_hobo_mode.option_disabled:
        uniques = [item for item in world.items_to_place.values() if
                   "Unique" in item["category"] and "Fishing Rod" not in item["category"]]
        for unique in uniques:
            unique["classification"] = ItemClassification.progression

        gear_upgrades = Items.get_gear_items(table=world.items_to_place)
        if (options.gucci_hobo_mode.value == options.gucci_hobo_mode.option_allow_one_slot_of_normal_rarity
                or options.gucci_hobo_mode.value == options.gucci_hobo_mode.option_no_non_unique_items):
            for item in gear_upgrades:
                if "Magic" in item["category"] or "Rare" in item["category"]:
                    world.items_to_place.pop(item["id"])

        if options.gucci_hobo_mode.value == options.gucci_hobo_mode.option_no_non_unique_items:
            for item in gear_upgrades:
                if "Normal" in item["category"]:
                    world.items_to_place.pop(item["id"])
    # remove passive skill points from item pool
    # we are using the slot_data to tell the client to chill out when it comes to passive skill points
    if options.add_passive_skill_points_to_item_pool.value == False:  # remove passive points from item pool
        item = Items.get_by_name("Progressive passive point", world.items_to_place)
        if item:
            # there is only one itemDict for passive points, but has a count of how many items to add. This removal should work
            world.items_to_place.pop(item["id"], None)
    else:
        item = Items.get_by_name("Progressive passive point", world.items_to_place)
        if item:
            item["count"] = poeRules.passives_required_for_act[world.goal_act + 1]
    items_to_remove = {}
    gem_categories = {"MainSkillGem", "SupportGem", "UtilSkillGem"}
    # remove gems that are too high level from item pool
    for item in world.items_to_place.values():
        if set(item["category"]).intersection(gem_categories) and item["reqLevel"] > max_level:
            items_to_remove[item["id"]] = item

    for item_id in items_to_remove:
        world.items_to_place.pop(item_id)
    # TODO: handle progressive gear unlocked.
    if options.gear_upgrades != options.gear_upgrades.option_no_gear_unlocked:
        categories = set()
        if options.gear_upgrades in {options.gear_upgrades.option_all_gear_unlocked_at_start,
                                     options.gear_upgrades.option_all_normal_and_unique_gear_unlocked,
                                     options.gear_upgrades.option_all_normal_gear_unlocked}:
            categories.add("Normal")
        if options.gear_upgrades in {options.gear_upgrades.option_all_gear_unlocked_at_start,
                                     options.gear_upgrades.option_all_normal_and_unique_gear_unlocked,
                                     options.gear_upgrades.option_all_uniques_unlocked}:
            categories.add("Unique")
        if options.gear_upgrades == options.gear_upgrades.option_all_gear_unlocked_at_start:
            categories.add("Magic")
            categories.add("Rare")
        all_gear_items = Items.get_gear_items(table=world.items_to_place)
        gear_upgrades = [item for item in all_gear_items if set(item["category"]).intersection(categories)]
        for item in gear_upgrades:
            item_objs = world.remove_and_create_items_by_itemdict(item)
            for item_obj in item_objs:
                world.precollect(item_obj)
    if options.add_flasks_to_item_pool.value == False:
        flask_slots = Items.get_flask_items(table=world.items_to_place)
        for item in flask_slots:
            item_objs = world.remove_and_create_items_by_itemdict(item)
            for item_obj in item_objs:
                world.precollect(item_obj)
    if options.add_max_links_to_item_pool.value == False:
        support_gem_slots = Items.get_max_links_items(table=world.items_to_place)
        for item in support_gem_slots:
            item_objs = world.remove_and_create_items_by_itemdict(item)
            for item_obj in item_objs:
                world.precollect(item_obj)

    if options.add_skill_gems_to_item_pool == False:
        skill_gems = Items.get_by_has_any_category({"MainSkillGem", "UtilSkillGem"}, table=world.items_to_place)
        for item in skill_gems:
            item_objs = world.remove_and_create_items_by_itemdict(item)
            for item_obj in item_objs:
                world.precollect(item_obj)

    if options.add_support_gems_to_item_pool == False:
        support_gems = Items.get_support_gem_items(table=world.items_to_place)
        for item in support_gems:
            item_objs = world.remove_and_create_items_by_itemdict(item)
            for item_obj in item_objs:
                world.precollect(item_obj)
    cleanup_gear_based_on_progressive_option(options, world)

    world.placed_total_gear_upgrades = min(len(Items.get_gear_items(table=world.items_to_place)),
                                           world.MAX_GUCCI_GEAR_UPGRADES)
    world.placed_total_flask_slots = min(len(Items.get_flask_items(table=world.items_to_place)),
                                         world.MAX_GEAR_UPGRADES)
    world.placed_total_link_upgrades = min(len(Items.get_max_links_items(table=world.items_to_place)),
                                           world.MAX_FLASK_SLOTS)
    world.placed_total_skill_gems = min(len(Items.get_main_skill_gem_items(table=world.items_to_place)),
                                        world.MAX_LINK_UPGRADES)
    world.placed_total_support_gems = min(len(Items.get_support_gem_items(table=world.items_to_place)),
                                          world.MAX_SKILL_GEMS)


def cleanup_gear_based_on_progressive_option(options, world):
    gucci_mode = not (options.gucci_hobo_mode.value == options.gucci_hobo_mode.option_disabled)

    if options.progressive_gear.value == options.progressive_gear.option_enabled and not gucci_mode:
        for item in Items.get_by_category(category="Random Gear", table=world.items_to_place):
            world.items_to_place.pop(world.item_name_to_id[item["name"]], None)

    elif options.progressive_gear.value == options.progressive_gear.option_progressive_except_for_unique:
        for item in Items.get_by_category(category="Progressive Gear", table=world.items_to_place):
            if "Flask" not in item["category"]:
                item["count"] -= 1
            elif "Flask" in item["category"]:
                item["count"] -= 5
        for item in Items.get_by_category(category="Random Gear", table=world.items_to_place):
            if "Unique" not in item["category"]:
                world.items_to_place.pop(world.item_name_to_id[item["name"]], None)

    # elif options.progressive_gear.value == options.progressive_gear.option_disabled:
    else:  # also if Guci Hobo is enabled, we are going to disable progressive gear, and use random gear upgrades
        for item in Items.get_by_category(category="Progressive Gear", table=world.items_to_place):
            world.items_to_place.pop(world.item_name_to_id[item["name"]], None)
    return None


def setup_character_items(world: "PathOfExileWorld"):
    options: PathOfExileOptions = world.options

    def handle_starting_character(char):
        item_obj = world.remove_and_create_item_by_name(char)
        world.precollect(item_obj)

        if options.usable_starting_gear.value in \
                (options.usable_starting_gear.option_starting_weapon_flask_and_gems,
                 options.usable_starting_gear.option_starting_weapon_and_gems,
                 options.usable_starting_gear.option_starting_weapon):
            weapon_name = ItemTable.starting_items_table[char]["weapon"]
            if not options.progressive_gear.value == options.progressive_gear.option_disabled:
                weapon_name = f"Progressive {weapon_name}"
            else:
                weapon_name = f"Normal {weapon_name}"
            if weapon_name in [item["name"] for item in world.items_to_place.values()]:
                world.precollect(world.remove_and_create_item_by_name(weapon_name))

            count = world.multiworld.state.count("Progressive max links - Weapon", world.player)
            if count < 1:
                link = [i for i in Items.get_max_links_items(table=world.items_to_place) if
                        i["name"] == "Progressive max links - Weapon"]
                if link and link[0] and link[0]["count"]:
                    if link[0]["count"] > 0:
                        world.items_to_place[link[0]["id"]]["count"] -= 1
                        world.precollect(world.create_item("Progressive max links - Weapon"))

        if options.usable_starting_gear.value in \
                (options.usable_starting_gear.option_starting_weapon_flask_and_gems,
                 options.usable_starting_gear.option_starting_weapon_and_gems):
            world.precollect(world.remove_and_create_item_by_name(Items.ItemTable.starting_items_table[char]["gem"]))
            world.precollect(world.remove_and_create_item_by_name(Items.ItemTable.starting_items_table[char]["support"]))

        STARTING_FLASK_SLOTS = 3
        if options.usable_starting_gear.value in \
                (options.usable_starting_gear.option_starting_weapon_flask_and_gems,
                 options.usable_starting_gear.option_starting_weapon_and_flask_slots):
            if options.progressive_gear.value == options.progressive_gear.option_disabled:
                # Get all normal flask items from the main table, this will probably just be 1, with a count
                normal_flasks = Items.get_by_has_every_category({"Flask", "Normal"})
                normal_flask_ids = {flask["id"] for flask in normal_flasks}
                total_normal_flask_count = sum(
                    item.get("count", 1) for item in world.items_to_place.values() if item["id"] in normal_flask_ids)
                # Count how many normal flasks are already collected
                collected_normal_flask_count = sum(
                    1 for item_obj in world.items_procollected.values() if item_obj.code in normal_flask_ids)

                # add flasks
                flasks_needed = STARTING_FLASK_SLOTS - collected_normal_flask_count
                if flasks_needed > 0:
                    normal_progressive_flask = Items.get_by_has_every_category({"Flask", "Normal"},
                                                                               table=world.items_to_place)  # should only be 1 item
                    total_normal_flask_count = normal_progressive_flask[0].get("count", 1)
                    for i in range(min(flasks_needed, total_normal_flask_count)):
                        item_obj = Items.PathOfExileItem(
                            name=normal_progressive_flask[0]["name"],
                            classification=ItemClassification.progression,
                            code=normal_progressive_flask[0]["id"],
                            player=world.player)
                        world.precollect(item_obj)

                    normal_progressive_flask[0]["count"] -= flasks_needed
                    if normal_progressive_flask[0]["count"] <= 0:
                        world.items_to_place.pop(normal_progressive_flask[0]["id"], None)
            else:
                for i in range(STARTING_FLASK_SLOTS):
                    world.precollect(world.create_item("Progressive Flask Unlock"))
        return char

    starting_character = ""
    if options.starting_character.value == options.starting_character.option_scion:
        starting_character = handle_starting_character("Scion")
    if options.starting_character.value == options.starting_character.option_marauder:
        starting_character = handle_starting_character("Marauder")
    if options.starting_character.value == options.starting_character.option_duelist:
        starting_character = handle_starting_character("Duelist")
    if options.starting_character.value == options.starting_character.option_ranger:
        starting_character = handle_starting_character("Ranger")
    if options.starting_character.value == options.starting_character.option_shadow:
        starting_character = handle_starting_character("Shadow")
    if options.starting_character.value == options.starting_character.option_witch:
        starting_character = handle_starting_character("Witch")
    if options.starting_character.value == options.starting_character.option_templar:
        starting_character = handle_starting_character("Templar")
    # remove other character class items, if not allowed
    if not options.allow_unlock_of_other_characters.value:
        character_items = Items.get_base_class_items(world.items_to_place)
        for character_item in character_items:
            if character_item['name'] != starting_character:
                world.items_to_place.pop(character_item['id'], None)
    temp_items_to_place = {}

    # add ascendancy items.
    char_classes = ["Marauder", "Ranger", "Witch", "Duelist", "Templar", "Shadow",
                    "Scion"] if options.allow_unlock_of_other_characters.value else [starting_character]
    if world.goal_act >= 3:
        for char_class in char_classes:
            sample_size = max(min(1 if char_class == "Scion" else 3, options.ascendancies_available_per_class.value), 0)
            logger.debug(
                f"{sample_size} Adding ascendancy items for {char_class}. "
                f"There are {len(Items.get_ascendancy_class_items(char_class, table=world.items_to_place))} items available.")
            items: list[Items.ItemDict] = world.random.sample(
                population=Items.get_ascendancy_class_items(char_class, table=world.items_to_place),
                k=sample_size
            )
            for item in items:
                temp_items_to_place[item["id"]] = item

    # remove all the other ascendancy items
    for item in Items.get_ascendancy_items(table=world.items_to_place):
        item_id = world.item_name_to_id[item["name"]]
        world.items_to_place.pop(item_id, None)
    # add the temp items to place back to the items to place
    for item_id, item_obj in temp_items_to_place.items():
        world.items_to_place[item_id] = item_obj

def get_goal_act(world, opt) -> int:
    if opt.goal.value == opt.goal.option_complete_act_1: return 1
    elif opt.goal.value == opt.goal.option_complete_act_2: return 2
    elif opt.goal.value == opt.goal.option_complete_act_3: return 3
    elif opt.goal.value == opt.goal.option_complete_act_4: return 4
    elif opt.goal.value == opt.goal.option_kauri_fortress_act_6: return 5
    elif opt.goal.value == opt.goal.option_complete_act_6: return 6
    elif opt.goal.value == opt.goal.option_complete_act_7: return 7
    elif opt.goal.value == opt.goal.option_complete_act_8: return 8
    elif opt.goal.value == opt.goal.option_complete_act_9: return 9
    elif opt.goal.value == opt.goal.option_complete_the_campaign: return 10
    else: return 11