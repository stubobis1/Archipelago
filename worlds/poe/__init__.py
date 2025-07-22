from ast import Set
import os
from typing import Dict
from worlds.LauncherComponents import components, Component, launch_subprocess, Type, icon_paths
from BaseClasses import Region, MultiWorld, Item, Location, LocationProgressType, ItemClassification
from worlds.AutoWorld import World, WebWorld
from Utils import visualize_regions
import yaml
import logging

from .Options import PathOfExileOptions
from . import Items
from . import Locations
from . import Regions as poeRegions


# ----- Configure the POE client ----- #
logger = logging.getLogger("poe")

def launch_client():
    from . import Client
    launch_subprocess(Client.launch, name="poeClient", )

components.append(Component("Path of Exile Client",
                            func=launch_client,
                            component_type=Type.CLIENT,
                            icon="poe"))

icon_paths["poe"] = f"ap:{__name__}/icons/poeicon.png"

# ----- PathOfExile Web World ----- #

class PathOfExileWebWorld(WebWorld):
    """
    Web interface for the Path of Exile world.
    This class can be extended to include specific web functionalities.
    """
    theme = "stone"
    bug_report_page = "https://github.com/stubobis1/Archipelago/issues" # if anyone else wants to maintain this, please do so

# ----- PathOfExile World ----- #


class PathOfExileWorld(World):
    """
    Represents the Path of Exile world in Archipelago.
    This class can be extended to include specific world properties and methods.
    """
    _debug = True
    game = "Path of Exile"
    web_world_class = PathOfExileWebWorld
    options_dataclass = PathOfExileOptions
    origin_region_name = "Menu"

    items_to_place = {}
    locations_to_place = {}
    total_items_count = 0
    #generate the location and item tables from Locations.py and Items.py
    # location_name_to_id = { loc.name: loc.id for loc in Locations.base_item_types }
    location_name_to_id = { loc["baseItem"]: id for id, loc in Locations.base_item_types.items() }
    item_name_to_id = { item["name"]: item["id"] for item in Items.item_table.values() }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items_to_place = Items.item_table.copy()
        self.locations_to_place = Locations.base_item_types.copy()

    def remove_and_create_item_by_dict(self, item: Items.ItemDict) -> list[Items.PathOfExileItem]:
        item_id = item["id"]
        item_to_place = self.items_to_place.pop(item_id)  # Remove from items to place
        item_objs = []
        count = item.get("count", 1)
        for i in range(count):
            item_obj = Items.PathOfExileItem(item_to_place["name"], ItemClassification.progression, item_id, self.player)
            item_objs.append(item_obj)
        return item_objs

    def remove_and_create_item_by_name(self, item_name: str) -> Item:
        item_id = self.item_name_to_id[item_name]
        item_to_place = self.items_to_place.pop(item_id)  # Remove from items to place
        item_obj = Items.PathOfExileItem(item_to_place["name"], ItemClassification.progression, item_id, self.player)
        return item_obj
    
    def generate_early(self):

        
        options: PathOfExileOptions = self.options
        # if options.starting_character.value == options.starting_character.option_random:
        #     options.starting_character.value = self.random.choice(
        #         [options.starting_character.option_marauder,
        #          options.starting_character.option_ranger,
        #          options.starting_character.option_witch,
        #          options.starting_character.option_duelist,
        #          options.starting_character.option_templar,
        #          options.starting_character.option_shadow,
        #          options.starting_character.option_scion])
        
        if (options.gucci_hobo_mode.value == options.gucci_hobo_mode.option_allow_one_slot_of_normal_rarity
                or options.gucci_hobo_mode.value == options.gucci_hobo_mode.option_no_non_unique_items):
            gear_upgrades = Items.get_gear_items(table=self.items_to_place)
            for item in gear_upgrades:
                if "Magic" in item["category"] or "Rare" in item["category"]:
                    self.items_to_place.pop(item["id"])

        if (options.gucci_hobo_mode.value == options.gucci_hobo_mode.option_no_non_unique_items):
            for item in gear_upgrades:
                if "Normal" in item["category"]:
                    self.items_to_place.pop(item["id"])

        
        if options.gear_unlocks.value == False:
            gear_upgrades = Items.get_gear_items(table=self.items_to_place)
            for item in gear_upgrades:
                item_objs = self.remove_and_create_item_by_dict(item)
                for item_obj in item_objs:
                    self.multiworld.push_precollected(item_obj)

        if options.flask_slot_upgrades.value == False:
            flask_slots = Items.get_flask_items(table=self.items_to_place)
            for item in flask_slots:
                item_objs = self.remove_and_create_item_by_dict(item)
                for item_obj in item_objs:
                    self.multiworld.push_precollected(item_obj)

        if options.support_gem_slot_upgrades.value == False:
            support_gem_slots = Items.get_max_links_items(table=self.items_to_place)
            for item in support_gem_slots:
                item_obj = self.remove_and_create_item_by_dict(item)        
                self.multiworld.push_precollected(item_obj)
                
        starting_character = ""
        if options.starting_character.value == options.starting_character.option_scion:
            item_obj = self.remove_and_create_item_by_name("Scion")
            self.multiworld.push_precollected(item_obj)
            starting_character = "Scion"

        if options.starting_character.value == options.starting_character.option_marauder:
            item_obj = self.remove_and_create_item_by_name("Marauder")
            self.multiworld.push_precollected(item_obj)
            starting_character = "Marauder"

        if options.starting_character.value == options.starting_character.option_duelist:
            item_obj = self.remove_and_create_item_by_name("Duelist")
            self.multiworld.push_precollected(item_obj)
            starting_character = "Duelist"

        if options.starting_character.value == options.starting_character.option_ranger:
            item_obj = self.remove_and_create_item_by_name("Ranger")
            self.multiworld.push_precollected(item_obj)
            starting_character = "Ranger"

        if options.starting_character.value == options.starting_character.option_shadow:
            item_obj = self.remove_and_create_item_by_name("Shadow")
            self.multiworld.push_precollected(item_obj)
            starting_character = "Shadow"

        if options.starting_character.value == options.starting_character.option_witch:
            item_obj = self.remove_and_create_item_by_name("Witch")
            self.multiworld.push_precollected(item_obj)
            starting_character = "Witch"

        if options.starting_character.value == options.starting_character.option_templar:
            item_obj = self.remove_and_create_item_by_name("Templar")
            self.multiworld.push_precollected(item_obj)
            starting_character = "Templar"

        temp_items_to_place = {}
        # add ascendancy items.
        char_classes = ["Marauder", "Ranger", "Witch", "Duelist", "Templar", "Shadow", "Scion"] if options.allow_unlock_of_other_characters.value else [starting_character]
        for item in range(0, options.ascendancies_available_per_class.value):
            for char_class in char_classes:
                item: Items.ItemDict = self.random.choice(Items.get_ascendancy_class_items(char_class, table=self.items_to_place))
                temp_items_to_place[item["id"]] = item
        
        # remove all the other ascendancy items
        for item in Items.get_ascendancy_items(table=self.items_to_place):
            item_id = self.item_name_to_id[item["name"]]
            self.items_to_place.pop(item_id, None)
        
        # add the temp items to place back to the items to place
        for item_id, item_obj in temp_items_to_place.items():
            self.items_to_place[item_id] = item_obj


    def create_regions(self):
        """Create the regions for the Path of Exile world.
        This method initializes the regions based on the acts defined in Regions.py.
        """
        options: PathOfExileOptions = self.options

        self.total_items_count = sum(item.get("count", 1) for item in self.items_to_place.values())
        
        # and only use the first `total_items_count` items of the Locations.base_item_types, we should have enough locations to place all items
        locations_to_place = list(Locations.base_item_types.values())[:self.total_items_count]
        if self._debug:
            logger.info(f"[DEBUG]: total locations to add: {len(locations_to_place)} / {len(Locations.base_item_types)} possible")
        poeRegions.create_and_populate_regions(world = self,
                                               multiworld=self.multiworld,
                                               player= self.player,
                                               locations=locations_to_place,
                                               act_regions=poeRegions.acts)
        #poeRegions.create_and_populate_regions(self, self.multiworld, self.player, locations_to_place, poeRegions.acts)

    def create_items(self):
        """Create the items for the Path of Exile world.
        This method initializes the items based on the items defined in Items.py.
        """
        options: PathOfExileOptions = self.options
        # iterate over a copy to be safe while modifying the dictionary
        for item in list(self.items_to_place.values()):
            list_of_items = self.remove_and_create_item_by_dict(item)
            for item in list_of_items:
                self.multiworld.itempool.append(item)
        
        if self._debug:
            logger.info(f"[DEBUG]: items left to place:{len(self.items_to_place)} /{self.total_items_count}.\n Created {len(self.locations_to_place)} locations.")



    def fill_slot_data(self):
        options: PathOfExileOptions = self.options
        client_options = {
            "gucciHobo" : options.gucci_hobo_mode.value,
            "ttsSpeed" : options.tts_speed.value,
            "ttsEnabled": options.enable_tts.value,
        }
        return {
            "client_options": client_options,
        }
        
        
    def generate_output(self, output_directory: str):
        if self._debug:
            logger.debug(f"Generating output for {self.game} in {output_directory}")
            visualize_regions(self.multiworld.get_region(self.origin_region_name, self.player), f"Player{self.player}.puml",
                            show_entrance_names=True,
                            regions_to_highlight=self.multiworld.get_all_state(self.player).reachable_regions[
                                self.player])



# TODO handle multiple locations with the same name -- two stone rings and stone axe (IIRC)
# TODO handle multiple items with the same name -- for flasks and such