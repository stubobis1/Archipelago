from typing import Mapping, Any

from BaseClasses import Region, MultiWorld, Item, Location, ItemClassification
from worlds.AutoWorld import World, WebWorld
from Utils import visualize_regions
from .options import UnlockerOptions

import logging

logger = logging.getLogger("Unlocker")


def item_table(item_names):
    # Create a dictionary to ensure unique items
    unique_items = {}
    for i, name in enumerate(item_names):
        if name not in unique_items:
            unique_items[name] = {
                "id": len(unique_items) + 1,  # Use length of unique items for id
                "classification": ItemClassification.progression_skip_balancing
            }
    return unique_items

def location_table(item_names):
    return {f"Unlock Slot {i+1}": i+1 for i in range(len(item_names))}

class UnlockerLocation(Location):
    game = "Unlocker"

    def __init__(self, player: int, name: str, address: int, parent=None):
        super().__init__(player, name, address, parent)
        self.event = True

    def can_fill(self, state, item, check_access=True) -> bool:
        # logger.info(f"Location {self.name} checking if can fill {item.name} (player {item.player})")
        # logger.info(f"Location player: {self.player}, Item player: {item.player}")
        # logger.info(f"Item classification: {item.classification}")
        # logger.info(f"Location event status: {self.event}")
        # Accept any item - these are progression locations
        return True


class Unlocker(World):
    game = "Unlocker"
    options_dataclass = UnlockerOptions

    item_name_to_id = {}
    location_name_to_id = {}
    item_id_to_location_id = {}
    location_id_to_item_id = {}
    origin_region_name = "Menu"

    def generate_early(self) -> None:
        items = self.options.item_list.value
        self.item_name_to_id = {name: i+1 for i, name in enumerate(items)}
        self.location_name_to_id = {f"Unlock Slot {i+1}": i+1 for i in range(len(items))}
        #self.item_id_to_location_id = {i+1: f"Unlock Slot {i+1}" for i in range(len(items))}
        self.location_id_to_item_id = {i + 1: name for i, name in enumerate(items)}
        # Give the first item at game start


        a = 1 + 1  # Dummy operation to ensure this method is called


    def create_regions(self):
        # Make sure regions are properly connected
        menu = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu)

        region = Region("Unlocker Region", self.player, self.multiworld)
        menu.connect(region)
        self.multiworld.regions.append(region)

        items = self.options.item_list.value
        logger.info(f"Creating Unlocker locations for player {self.player}")
        for i, (loc_name, loc_id) in enumerate(location_table(items).items()):
            location = UnlockerLocation(self.player, loc_name, loc_id, region)
            # Fix: Use a function to avoid late binding in lambda
            if i == 0:
                location.access_rule = lambda state: True
            else:
                prev_item = items[i - 1]
                def make_rule(prev_item):
                    return lambda state: state.has(prev_item, self.player)
                location.access_rule = make_rule(prev_item)
            region.locations.append(location)

    def create_items(self):
        items = self.options.item_list.value
        logger.info(f"Creating Unlocker items: {items}")




        for i, (name, data) in enumerate(item_table(items).items()):
            item = Item(name, data["classification"], data["id"], self.player)
            #logger.info(f"Created item: {item.name} with classification {item.classification}")
            self.multiworld.itempool.append(item)
            if  i == 0:
                    # Give the first item at game start
                    self.multiworld.push_precollected(item)

    def set_rules(self):
        # Simplify completion condition - player wins when they collect all items
        def completion_rule(state):
            for item in self.options.item_list.value:
                if not state.has(item, self.player):
                    return False
            return True
        self.multiworld.completion_condition[self.player] = completion_rule


    def fill_slot_data(self):
        # make a mapping of items to the locations they unlock for this player
        items = self.options.item_list.value
        item_to_location_unlock = {
            item: f"Unlock Slot {i+1}" for i, item in enumerate(items)
        }
        return {
            "item_to_location_unlock": item_to_location_unlock,
        }

    def generate_output(self, output_directory: str):
        visualize_regions(self.multiworld.get_region("Menu", self.player), f"Player{self.player}.puml",
                          show_entrance_names=True,
                          regions_to_highlight=self.multiworld.get_all_state(self.player).reachable_regions[
                              self.player])