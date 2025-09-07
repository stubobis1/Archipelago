import os
from typing import Dict, Set
from worlds.LauncherComponents import components, Component, launch_subprocess, Type, icon_paths
from BaseClasses import Region, MultiWorld, Item, Location, LocationProgressType, ItemClassification
from worlds.AutoWorld import World, WebWorld
from Utils import visualize_regions
import yaml
import logging
import base64

from worlds.poe.data import ItemTable

from .Options import PathOfExileOptions
from . import Items
from . import Locations
from . import Regions as poeRegions
from . import Rules as poeRules
from . import Options
from .Version import POE_VERSION

logger = logging.getLogger("poe")
logger.setLevel(logging.DEBUG)

# ----- Configure the POE client ----- #


def launch_client():
    from . import Client
    launch_subprocess(Client.launch, name="poeClient", )

components.append(Component("Path of Exile Client",
                            func=launch_client,
                            component_type=Type.CLIENT,
                            icon="poe"))

icon_paths["poe"] = f"ap:{__name__}/icons/poeicon.png"

# ----- PathOfExile Web World ----- #
from BaseClasses import Tutorial
class PathOfExileWebWorld(WebWorld):
    """
    Web interface for the Path of Exile world.
    This class can be extended to include specific web functionalities.
    """
    theme = "stone"
    bug_report_page = "https://github.com/stubobis1/Archipelago/issues" # if anyone else wants to help maintain this, please do so
    setup_en = Tutorial(
        tutorial_name="Path of Exile Setup Guide",
        description="A guide to setting up Archipelago Path of Exile.",
        language="English",
        file_name="setup_en.md",
        link="setup/en",
        authors=["StuBob"]
    )
    tutorials = [setup_en]

    option_groups = Options.poe_options_groups
    options_presets = Options.poe_presets

# ----- PathOfExile World ----- #


class PathOfExileWorld(World):
    """
    Path of Exile is a free-to-play online action RPG set in a dark, gritty world where you explore, fight monsters,
    and collect powerful loot. The game is known for its deep character customization, with an enormous passive skill
    tree, thousands of items, and a huge endgame full of challenging bosses, and a wide variety of skill gems that define abilities.
    """
    _debug = True
    game = "Path of Exile"
    author: str = "StuBob"
    web = PathOfExileWebWorld()
    options_dataclass = PathOfExileOptions
    origin_region_name = "Menu"

# Instance variables, but made in __init__ so they are per-instance
#    items_to_place = {}
#    items_procollected = {}
#    locations_to_place = {}
#    total_items_to_place_count = 0
#
#    goal_act = 0

    location_name_to_id = ({ loc["name"]: id for id, loc in Locations.full_locations.items() } 
                        | { loc["name"]: loc["id"] for loc in Locations.bosses.values() })

    item_name_to_id = ({ item["name"]: item["id"] for item in Items.item_table.values() }
                       | { item["name"]: item["id"] for item in Locations.bosses.values() })



    item_name_groups: Dict[str, Set[str]] = Items.get_item_name_groups()

    def __init__(self, *args, **kwargs):

        self.items_to_place = {}
        self.items_procollected = {}
        self.locations_to_place = {}
        self.total_items_to_place_count = 0
        self.goal_act = 0
        self.bosses_for_goal: list[str] = []

        super().__init__(*args, **kwargs)

        # ``Items.item_table`` is a module level dictionary whose values are
        # mutable ``dict`` objects.  The original implementation only created a
        # shallow copy of this mapping which meant that any modification to the
        # nested dictionaries (for example changing an item's classification
        # from progression to filler) would also mutate the global item table.
        #
        # By performing a deep copy we ensure every world gets its own private
        # copy of the item table and mutations no longer leak between runs.
        # self.items_to_place = Items.item_table.copy()
        import copy
        self.items_to_place = copy.deepcopy(Items.item_table)


    def remove_and_create_items_by_itemdict(self, item: Items.ItemDict) -> list[Items.PathOfExileItem]:
        item_id = item["id"]
        item_to_place = self.items_to_place.pop(item_id)  # Remove from items to place
        item_objs = []
        count = item.get("count", 1)
        for i in range(count):
            item_obj = Items.PathOfExileItem(item_to_place["name"], item.get("classification", ItemClassification.filler), item_id, self.player)
            item_objs.append(item_obj)
        return item_objs

    def remove_and_create_item_by_name(self, item_name: str) -> Item:
        item_id = self.item_name_to_id[item_name]
        item_to_place = self.items_to_place.pop(item_id)  # Remove from items to place
        item_obj = Items.PathOfExileItem(item_to_place["name"], ItemClassification.progression, item_id, self.player)
        return item_obj

    def precollect(self, item_obj):
        self.items_procollected[item_obj.code] = item_obj
        self.multiworld.push_precollected(item_obj)
    
    def generate_early(self):
       # # Clear performance cache for fresh generation
       # from . import Rules as poeRules
       # poeRules.clear_item_cache()
        
        opt: PathOfExileOptions = self.options
        self.goal_act = get_goal_act(self, opt)

        if opt.goal.value == opt.goal.option_defeat_bosses:
            if opt.bosses_available.value is None or len(opt.bosses_available.value) == 0:
                opt.bosses_available.value = list(Locations.bosses.keys())

            bosses_to_kill = min(opt.number_of_bosses, len(Locations.bosses), len(opt.bosses_available.value))

            self.bosses_for_goal = self.random.sample(sorted(opt.bosses_available.value), bosses_to_kill)

        setup_early_items(self, opt)

        self.items_to_place = Items.deprioritize_non_logic_gems(self, self.items_to_place)
        self.items_to_place = Items.deprioritize_non_logic_gear(self, self.items_to_place)

        self.total_items_to_place_count = sum(item.get("count", 1) for item in self.items_to_place.values())
        self.locations_to_place = poeRules.SelectLocationsToAdd(world=self, target_amount=self.total_items_to_place_count)

        table_total_item_count = sum(item.get("count", 1) for item in Items.item_table.values())
        if len(self.locations_to_place) <  self.total_items_to_place_count:
            logger.debug(
                f"[Debug]: Not enough locations to place all items! locations: {len(self.locations_to_place)} < items: {table_total_item_count}\nCulling...")
            self.total_items_to_place_count = sum(item.get("count", 1) for item in self.items_to_place.values())
            logger.debug(
                f"[DEBUG]: total items to place before culling: {self.total_items_to_place_count} / {table_total_item_count} possible")
            self.items_to_place = Items.cull_items_to_place(self, self.items_to_place, self.locations_to_place)
            self.total_items_to_place_count = sum(item.get("count", 1) for item in self.items_to_place.values())
            logger.debug(
                f"[DEBUG]: total items to place after  culling: {self.total_items_to_place_count} / {table_total_item_count} possible")


        table_total_item_count = sum(item.get("count", 1) for item in Items.item_table.values())
        logger.debug(f"[DEBUG]: total items to place: {self.total_items_to_place_count} / {table_total_item_count} possible")
        logger.debug(f"[DEBUG]: total locs in world.: {len(self.locations_to_place)} / {len(Locations.full_locations)} possible")


    def create_regions(self):
        """Create the regions for the Path of Exile world.
        This method initializes the regions based on the acts defined in Regions.py.
        """
        options: PathOfExileOptions = self.options
        acts_to_play = [act for act in poeRegions.acts if act["act"] <= self.goal_act]
        poeRegions.create_and_populate_regions(world = self,
                                               multiworld=self.multiworld,
                                               player= self.player,
                                               locations=self.locations_to_place,
                                               act_regions=acts_to_play)
        #poeRegions.create_and_populate_regions(self, self.multiworld, self.player, locations_to_place, poeRegions.acts)

        self.multiworld.completion_condition[self.player] = lambda state: (poeRules.completion_condition(self, state))


        logger.debug(f"[CreateRegion]: total items to place: {self.total_items_to_place_count}")
        logger.debug(f"[CreateRegion]: total locs in world.: {len(self.locations_to_place)}")

        self.create_items_but_do_it_earlier()

    def create_items_but_do_it_earlier(self):
        """Create the items for the Path of Exile world.
        This method initializes the items based on the items defined in Items.py.
        """
        options: PathOfExileOptions = self.options
        # iterate over a copy to be safe while modifying the dictionary
        for item in list(self.items_to_place.values()):
            list_of_items = self.remove_and_create_items_by_itemdict(item)
            for item in list_of_items:
                self.multiworld.itempool.append(item)

        logger.debug(f"[DEBUG]: items left to place:{len(self.items_to_place)} /{self.total_items_to_place_count}.\n Created {len(self.locations_to_place)} locations.")

    def create_item(self, item_name: str) -> Items.PathOfExileItem:
        # this is called when AP wants to create an item by name (for plando, start inventory, item links) or when you call it from your own code

        # get the item from the item table, by name
        id = self.item_name_to_id.get(item_name)
        item = Items.item_table.get(id)
        if item is None:
            if "defeat" in item_name:
                #its a boss
                item = Locations.bosses.get(item_name.replace("defeat ", ""))
            else:
                raise Exception(f"I don't know how to create the item {item}")
        classification = item.get("classification", ItemClassification.progression)  # progression I guess?
        return Items.PathOfExileItem(item['name'], classification, item['id'], self.player)

    def create_items(self):
        #itempool = self.multiworld.itempool
        #logger.debug(f"[DEBUG]: in create_items {len(itempool)} ---- ")
        pass


    def fill_slot_data(self):
        options: PathOfExileOptions = self.options
        game_options = {
            "gucciHobo": options.gucci_hobo_mode.value,
            "passivePointsAsItems": options.add_passive_skill_points_to_item_pool.value,
            "LevelingUpAsLocations": options.add_leveling_up_to_location_pool.value,
            "ProgressiveGear": options.progressive_gear.value,
            "goal": options.goal.value,
            "starting_character": Options.option_starting_character_to_class_name(options.starting_character.value),
            "bosses_for_goal": self.bosses_for_goal,
            "deathlink": options.death_link.value,
        }
        client_options = {
            "lootFilterSounds": options.loot_filter_sounds.value,
            "lootFilterDisplay": options.loot_filter_display.value,
            "ttsSpeed" : options.tts_speed.value,
            "ttsEnabled": options.enable_tts.value,
        }
        return {
            "game_options": game_options,
            "client_options": client_options,
            "poe-uuid": base64.urlsafe_b64encode(self.random.randbytes(8)).strip(b'=').decode('utf-8'), # used for generation id
            "generated_version": POE_VERSION,
        }

        
    def generate_output(self, output_directory: str):
        if self._debug:
            logger.debug(f"Generating output for {self.game} in {output_directory}")
            visualize_regions(self.multiworld.get_region(self.origin_region_name, self.player), f"Player{self.player}.puml",
                            show_entrance_names=True,
                            regions_to_highlight=self.multiworld.get_all_state(self.player).reachable_regions[
                                self.player])

# ---------
def setup_early_items(world: PathOfExileWorld, options: PathOfExileOptions):
    setup_character_items(world, options)
    max_level = Locations.acts[world.goal_act]["maxMonsterLevel"]
    
    if options.progressive_gear.value == options.progressive_gear.option_enabled:
        for item in Items.get_by_category(category="Random Gear", table=world.items_to_place):
            world.items_to_place.pop(world.item_name_to_id[item["name"]], None)
    elif options.progressive_gear.value == options.progressive_gear.option_disabled:
        for item in Items.get_by_category(category="Progressive Gear", table=world.items_to_place):
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
    
    if options.gucci_hobo_mode.value != options.gucci_hobo_mode.option_disabled:
        uniques = [item for item in Items.item_table.values() if "Unique" in item["category"]]
        for unique in uniques:
            unique["classification"] = ItemClassification.progression
            
        gear_upgrades = Items.get_gear_items(table=world.items_to_place)
        if (options.gucci_hobo_mode.value == options.gucci_hobo_mode.option_allow_one_slot_of_normal_rarity
                or options.gucci_hobo_mode.value == options.gucci_hobo_mode.option_no_non_unique_items):
            for item in gear_upgrades:
                if "Magic" in item["category"] or "Rare" in item["category"]:
                    world.items_to_place.pop(item["id"])

        if (options.gucci_hobo_mode.value == options.gucci_hobo_mode.option_no_non_unique_items):
            for item in gear_upgrades:
                if "Normal" in item["category"]:
                    world.items_to_place.pop(item["id"])
    # remove passive skill points from item pool
    # we are using the slot_data to tell the client to chill out when it comes to passive skill points
    if options.add_passive_skill_points_to_item_pool.value == False:
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

def setup_character_items(world, options):
    def handle_starting_character(char):
        item_obj = world.remove_and_create_item_by_name(char)
        world.precollect(item_obj)

        if options.usable_starting_gear.value in \
                (options.usable_starting_gear.option_starting_weapon_flask_and_gems,
                 options.usable_starting_gear.option_starting_weapon_and_gems,
                 options.usable_starting_gear.option_starting_weapon):
            weapon_name = ItemTable.starting_items_table[char]["weapon"] if options.progressive_gear.value == options.progressive_gear.option_disabled else ItemTable.starting_items_table[char]["progressive weapon"]
            if weapon_name in [item["name"] for item in world.items_to_place.values()]:
                world.precollect(world.remove_and_create_item_by_name(weapon_name))

            count = world.multiworld.state.count("Progressive max links - Weapon", world.player)
            if count < 1:
                link = [i for i in Items.get_max_links_items(table=world.items_to_place) if i["name"] == "Progressive max links - Weapon"]
                if link and link[0] and link[0]["count"] :
                    if link[0]["count"] > 0:
                        world.items_to_place[link[0]["id"]]["count"] -= 1
                        world.precollect(world.create_item("Progressive max links - Weapon"))

        if options.usable_starting_gear.value in \
                (options.usable_starting_gear.option_starting_weapon_flask_and_gems,
                 options.usable_starting_gear.option_starting_weapon_and_gems):
            world.precollect(world.remove_and_create_item_by_name(ItemTable.starting_items_table[char]["gem"]))
            world.precollect(world.remove_and_create_item_by_name(ItemTable.starting_items_table[char]["support"]))

        STARTING_FLASK_SLOTS = 3
        if options.usable_starting_gear.value in \
                (options.usable_starting_gear.option_starting_weapon_flask_and_gems,
                 options.usable_starting_gear.option_starting_weapon_and_flask_slots):

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







# TODO handle multiple locations with the same name -- two stone rings and stone axe (IIRC)