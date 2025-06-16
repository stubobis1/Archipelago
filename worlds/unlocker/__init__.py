from BaseClasses import Region, MultiWorld, Item, Location, LocationProgressType, ItemClassification
from worlds.AutoWorld import World, WebWorld
from Utils import visualize_regions
from .options import UnlockerOptions, Accessibility
import os
import yaml
import logging

# ----- SETUP CLIENT ----- #
from worlds.LauncherComponents import components, Component, launch_subprocess, Type, icon_paths

logger = logging.getLogger("Unlocker")

def launch_client():
    from . import client
    launch_subprocess(client.launch, name="unlockerClient", )

components.append(Component("Unlocker Client",
                            func=launch_client,
                            component_type=Type.CLIENT,
                            icon="unlocker"))

icon_paths["unlocker"] = f"ap:{__name__}/icons/unlocker.png"

# ----- ITEMS ----- #

# an enum of item classifications
class ClassificationStrings:
    progression = "progression"
    key = "key"
    other = "other"

class UnlockerItem(Item):
    game = "Unlocker"
    def __init__(self, name: str, classification: ItemClassification, id: int, player: int):
        super().__init__(name, classification, id, player)

# player specific item table
def generate_player_item_table(item_names, location_name_to_id, classification=ClassificationStrings.progression):
    # Create a dictionary to ensure unique items
    player_items = {}
    for name in item_names:
        if name not in player_items:
            player_items[name] = {
                "name": name,
                "id": location_name_to_id.get(name),
                "classification": classification
            }
    return player_items

# ----- LOCATIONS ----- #

# player specific location table
def generate_player_location_table(player_items, location_name_to_id, item_name_to_unlocker_location):
    player_locations = {}
    for name in player_items:
        location_name = item_name_to_unlocker_location[name]
        player_locations[location_name] = {
            "id": location_name_to_id.get(location_name),
            "loc_id": location_name_to_id.get(location_name),
            "name": location_name,
            "game": "Unlocker",
        }
    return player_locations

class UnlockerLocation(Location):
    game = "Unlocker"
    OnlyOtherGamesCanFill = True

    def __init__(self, player: int, name: str, address: int, parent=None, only_other_games_can_fill: bool = False):
        super().__init__(player, name, address, parent)
        self.OnlyOtherGamesCanFill = only_other_games_can_fill

    def can_fill(self, state, item, check_access=True) -> bool:
        # we can always allow items from other players to fill locations
        if not super().can_fill(state, item, check_access):
            return False
        if item.player != self.player and item.game != self.game:
            return True # we can always allow items from other players in other games.
        if self.OnlyOtherGamesCanFill:
            return item.game != self.game
        else:
            # we do this so that there are no circular dependencies in the game.
            return item.code < self.address

# ----- WORLD CLASS ----- #

def get_all_unlocker_items(players_dir="Players"):
    unique_items = {}
    # Ensure the players directory exists
    if not os.path.exists(players_dir):
        players_dir = "../" + players_dir  # Adjust path if needed
    if not os.path.exists(players_dir):
        players_dir = "../" + players_dir  # twice if we are running from the client in unlocker.
    yaml_files = os.listdir(players_dir)
    for filename in os.listdir(players_dir):
        if filename.endswith(".yaml"):
            with open(os.path.join(players_dir, filename), "r", encoding="utf-8") as f:
                try:
                    data = yaml.safe_load(f)
                    if data.get("game", "").lower() == "unlocker":
                        full_item_list = data.get("Unlocker", {}).get("required_item_list", []) + data.get("Unlocker", {}).get("optional_item_list", [])

                        # Handle both list and string (comma-separated) formats
                      # if isinstance(full_item_list, str):
                      #     full_item_list = [item.strip() for item in full_item_list.split(",")]
                        for item in full_item_list:
                            if item not in unique_items:
                                unique_items[item] = len(unique_items) + 1
                except Exception as e:
                    logger.error(f"Error reading {filename}: {e}")
                    continue
    return unique_items

def generate_all_unlocker_locations_from_items(full_item_list, item_name_to_unlocked_location):
    locations = {}
    for i, name in enumerate(full_item_list):
        key = f"Unlock #{full_item_list[name]} - {name} "
        locations[key] = full_item_list[name]
        item_name_to_unlocked_location[name] = key
    return locations
__mydebug__ = True  # This is used for debugging purposes, can be set to False to disable debug prints
class Unlocker(World):
    game = "Unlocker"
    options_dataclass = UnlockerOptions



    item_name_to_unlocker_location = {}

    # needed by parent, TODO make this static
    item_name_to_id = get_all_unlocker_items()
    location_name_to_id = generate_all_unlocker_locations_from_items(item_name_to_id, item_name_to_unlocker_location)


    player_required_location_table = {}
    player_optional_location_table = {}
    player_required_item_table = {}
    player_optional_item_table = {}
    origin_region_name = "Menu"


    def generate_early(self) -> None:
        required_items = self.options.required_item_list.value
        optional_items = self.options.optional_item_list.value
        optional_access = ClassificationStrings.other if self.options.accessibility == Accessibility.option_minimal \
            else ClassificationStrings.progression


        self.player_required_item_table = generate_player_item_table(required_items, self.item_name_to_id, ClassificationStrings.progression)
        self.player_optional_item_table = generate_player_item_table(optional_items, self.item_name_to_id, optional_access)
        self.player_required_location_table = generate_player_location_table(required_items, self.location_name_to_id,
                                                                             self.item_name_to_unlocker_location)
        self.player_optional_location_table = generate_player_location_table(optional_items, self.location_name_to_id,
                                                                             self.item_name_to_unlocker_location)

    # Every region in Unlocker is unlocked by an item, the item and the location are tightly coupled.
    def create_regions(self):
        menu = Region(self.origin_region_name, self.player, self.multiworld)
        self.multiworld.regions.append(menu)
        required_region = Region("Unlocker Required  Region", self.player, self.multiworld)
        optional_region = Region("Unlocker Optional  Region", self.player, self.multiworld)
        menu.connect(required_region)
        menu.connect(optional_region)
        self.multiworld.regions.append(required_region)
        self.multiworld.regions.append(optional_region)
        logger.info(f"Creating Unlocker locations for player {self.player}")

        for loc_name, loc_obj in self.player_required_location_table.items():
            location = UnlockerLocation(self.player, loc_name, loc_obj["id"], required_region,
                                        self.options.only_allow_other_games_items.value == 1)
            location.access_rule = lambda state, location_id=loc_obj["id"]: state.has(self.item_id_to_name[location_id], self.player)
            required_region.locations.append(location)

        for loc_name, loc_obj in self.player_optional_location_table.items():
            location = UnlockerLocation(self.player, loc_name, loc_obj["id"], optional_region,
                                        self.options.only_allow_other_games_items.value == 1)
            if (self.options.accessibility == Accessibility.option_minimal):
                location.progress_type = LocationProgressType.EXCLUDED

            location.access_rule = lambda state, location_id=loc_obj["id"]: state.has(self.item_id_to_name[location_id], self.player)
            optional_region.locations.append(location)

    def create_items(self):
        items = self.options.required_item_list.value
        logger.info(f"Creating required Unlocker items: {items}")
        for i, (name, data) in enumerate(self.player_required_item_table.items()):
            new_item = UnlockerItem(name, ItemClassification.progression, data["id"], self.player)
            self.multiworld.itempool.append(new_item)

        items = self.options.optional_item_list.value
        logger.info(f"Creating optional Unlocker items: {items}")
        optional_access \
            = ItemClassification.filler if self.options.accessibility == Accessibility.option_minimal \
            else ItemClassification.useful
        for i, (name, data) in enumerate(self.player_optional_item_table.items()):
            new_item = UnlockerItem(name, optional_access, data["id"], self.player)
            self.multiworld.itempool.append(new_item)

    def set_rules(self):
        # completion condition - player wins when they collect all items
        def completion_rule(state):
            for item in self.player_required_item_table.keys():
                if not state.has(item, self.player):
                    return False
            return True

        self.multiworld.completion_condition[self.player] = completion_rule

    def fill_slot_data(self):
        location_table = self.player_required_location_table
        # make a table of item id to location name
        item_id_to_location_name = {data["id"]: name for name, data in list(self.player_required_location_table.items()) + list(self.player_optional_location_table.items())}
        return {
            "item_name_to_unlocker_location": self.item_name_to_unlocker_location,
            "player_location_table": self.player_required_location_table,
            "item_id_to_location_name": item_id_to_location_name,
        }

    def generate_output(self, output_directory: str):
        visualize_regions(self.multiworld.get_region(self.origin_region_name, self.player), f"Player{self.player}.puml",
                          show_entrance_names=True,
                          regions_to_highlight=self.multiworld.get_all_state(self.player).reachable_regions[
                              self.player])