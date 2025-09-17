from typing import Dict, List, TYPE_CHECKING
from BaseClasses import Region, CollectionState
from worlds.generic.Rules import set_rule
from ..Items import SohItem
from ..Locations import SohLocation, SohLocationData
from ..Enums import Items
from ..Rules import *

if TYPE_CHECKING:
    from .. import SohWorld

# Lost Woods region names
region_names: list[str] = [
    "LW Forest Exit",
    "The Lost Woods", 
    "LW Beyond Mido",
    "LW Near Shortcuts Grotto",
    "Deku Theater",
    "LW Scrubs Grotto",
    "LW Bridge From Forest",
    "LW Bridge"
]

def create_regions_and_rules(world: "SohWorld") -> None:
    """Set access rules for Lost Woods regions (regions already created)."""
    # Set region access rules
    set_region_rules(world)
    
    # Location access rules will be set later after locations are created

def set_region_rules(world: "SohWorld") -> None:
    """Set access rules for Lost Woods region entrances."""
    
    # The Lost Woods -> LW Beyond Mido requires child or Saria's Song or trick
    world.get_entrance("The Lost Woods -> LW Beyond Mido").access_rule = \
        lambda state: is_child(state, world) or \
                      can_use(Items.SARIAS_SONG.value, state, world) or \
                      can_do_trick("RT_LW_MIDO", state, world)

def set_location_rules(world: "SohWorld") -> None:
    """Set access rules for Lost Woods locations."""
    
    # Helper function to check if location exists before setting rules
    def set_location_rule_if_exists(location_name: str, rule_func):
        try:
            world.get_location(location_name).access_rule = rule_func
        except KeyError:
            # Location doesn't exist (probably due to options), skip it
            pass
    
    # LW Beyond Mido locations
    set_location_rule_if_exists("LW Gift From Saria",
        lambda state: (is_child(state, world) or 
                       can_use(Items.SARIAS_SONG.value, state, world)) and \
                       can_use(Items.OCARINA.value, state, world))
    
    set_location_rule_if_exists("LW Trade Cojiro",
        lambda state: is_adult(state, world) and \
                      can_use(Items.COJIRO.value, state, world))
    
    # LW Scrubs Grotto locations
    set_location_rule_if_exists("LW Deku Scrub Grotto Front",
        lambda state: can_use_wallet(state, world, 1))
    
    set_location_rule_if_exists("LW Deku Scrub Grotto Rear",
        lambda state: can_use_wallet(state, world, 1))
    
    set_location_rule_if_exists("LW Deku Scrub Grotto Beehive",
        lambda state: is_child(state, world) and \
                      can_use(Items.BOOMERANG.value, state, world))
    
    set_location_rule_if_exists("LW Scrub Grotto Sun's Song Fairy",
        lambda state: can_use(Items.SUNS_SONG.value, state, world))
    
    # LW Target in Woods (child with slingshot)
    set_rule(world.get_location("LW Target in Woods"),
             lambda state: not is_adult(state, world) and
                           can_use(Items.FAIRY_SLINGSHOT.value, state, world))
    
    # LW Near Shortcuts Grotto Chest (inside grotto, always accessible)
    set_rule(world.get_location("LW Near Shortcuts Grotto Chest"),
             lambda state: True)
    
    # LW Deku Scrub Near Bridge (child with nuts/slingshot)
    set_rule(world.get_location("LW Deku Scrub Near Bridge"),
             lambda state: not is_adult(state, world) and
                           (can_use(Items.NUTS.value, state, world) or
                            can_use(Items.FAIRY_SLINGSHOT.value, state, world)))
    
    # Fairy locations
    
    # Bean sprout fairies (child with magic bean and song of storms)
    for fairy_num in [1, 2, 3]:
        set_rule(world.get_location(f"LW Bean Sprout Near Bridge Fairy {fairy_num}"),
                 lambda state: not is_adult(state, world) and
                               can_use(Items.MAGIC_BEAN.value, state, world) and
                               can_use(Items.SONG_OF_STORMS.value, state, world))
        
        set_rule(world.get_location(f"LW Bean Sprout Near Theatre Fairy {fairy_num}"),
                 lambda state: not is_adult(state, world) and
                               can_use(Items.MAGIC_BEAN.value, state, world) and
                               can_use(Items.SONG_OF_STORMS.value, state, world))
    
    # Gossip stone fairies
    set_rule(world.get_location("LW Gossip Stone Fairy"),
             lambda state: True)  # CallGossipFairyExceptSuns - always accessible
    
    set_rule(world.get_location("LW Gossip Stone Big Fairy"),
             lambda state: can_use(Items.SONG_OF_STORMS.value, state, world))
    
    # Grotto specific locations
    
    # LW Tunnel Grotto fairies
    set_rule(world.get_location("LW Tunnel Grotto Gossip Stone Fairy"),
             lambda state: True)
    
    set_rule(world.get_location("LW Tunnel Grotto Big Fairy"),
             lambda state: can_use(Items.SONG_OF_STORMS.value, state, world))
    
    # LW Shortcuts Song of Storms Fairy
    set_rule(world.get_location("LW Shortcuts Song of Storms Fairy"),
             lambda state: can_use(Items.SONG_OF_STORMS.value, state, world))
    
    # LW Scrub Grotto locations
    set_rule(world.get_location("LW Scrub Grotto Sun's Song Fairy"),
             lambda state: can_use(Items.SUNS_SONG.value, state, world))
    
    # Beehive locations  
    set_rule(world.get_location("LW Deku Scrub Grotto Beehive"),
             lambda state: has_projectile(state, world) or can_attack(state, world))

def create_regions(multiworld, player: int, logic: "OOTLogic") -> Dict[str, Region]:
    """Create all Lost Woods regions and their access rules."""
    regions = {}

    # Lost Woods regions
    regions[OOTRegions.LW_FOREST_EXIT] = create_lw_forest_exit(multiworld, player, logic)
    regions[OOTRegions.THE_LOST_WOODS] = create_the_lost_woods(multiworld, player, logic)
    regions[OOTRegions.LW_BEYOND_MIDO] = create_lw_beyond_mido(multiworld, player, logic)
    regions[OOTRegions.LW_NEAR_SHORTCUTS_GROTTO] = create_lw_near_shortcuts_grotto(multiworld, player, logic)
    regions[OOTRegions.DEKU_THEATER] = create_deku_theater(multiworld, player, logic)
    regions[OOTRegions.LW_SCRUBS_GROTTO] = create_lw_scrubs_grotto(multiworld, player, logic)
    regions[OOTRegions.LW_BRIDGE_FROM_FOREST] = create_lw_bridge_from_forest(multiworld, player, logic)
    regions[OOTRegions.LW_BRIDGE] = create_lw_bridge(multiworld, player, logic)

    return regions

def create_lw_forest_exit(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create LW Forest Exit region."""
    region = Region("LW Forest Exit", player, multiworld)
    # This is just a connection point, no locations
    return region

def create_the_lost_woods(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create The Lost Woods main region."""
    region = Region("Lost Woods", player, multiworld)
    
    # Major trading/quest locations
    region.locations.append(OOTLocations.LW_SKULL_KID)
    region.locations.append(OOTLocations.LW_TRADE_COJIRO)
    region.locations.append(OOTLocations.LW_TRADE_ODD_POTION)
    region.locations.append(OOTLocations.LW_OCARINA_MEMORY_GAME)
    region.locations.append(OOTLocations.LW_TARGET_IN_WOODS)
    region.locations.append(OOTLocations.LW_DEKU_SCRUB_NEAR_BRIDGE)
    region.locations.append(OOTLocations.LW_GS_BEAN_PATCH_NEAR_BRIDGE)
    
    # Shortcut rupees (underwater)
    for i in range(1, 9):
        region.locations.append(getattr(OOTLocations, f"LW_SHORTCUT_RUPEE_{i}"))
    
    # Bean sprout fairies
    for i in range(1, 4):
        region.locations.append(getattr(OOTLocations, f"LW_BEAN_SPROUT_NEAR_BRIDGE_FAIRY_{i}"))
    
    # Gossip stone interactions
    region.locations.append(OOTLocations.LW_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.LW_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.LW_SHORTCUT_STORMS_FAIRY)
    region.locations.append(OOTLocations.LW_GOSSIP_STONE)
    
    # Grass cutting
    for i in range(1, 4):
        region.locations.append(getattr(OOTLocations, f"LW_GRASS_{i}"))
    
    return region

def create_lw_beyond_mido(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create LW Beyond Mido region."""
    region = Region("LW Beyond Mido", player, multiworld)
    
    # Deku scrubs near theater
    region.locations.append(OOTLocations.LW_DEKU_SCRUB_NEAR_DEKU_THEATER_RIGHT)
    region.locations.append(OOTLocations.LW_DEKU_SCRUB_NEAR_DEKU_THEATER_LEFT)
    
    # Gold Skulltulas
    region.locations.append(OOTLocations.LW_GS_ABOVE_THEATER)
    region.locations.append(OOTLocations.LW_GS_BEAN_PATCH_NEAR_THEATER)
    
    # Boulder rupee
    region.locations.append(OOTLocations.LW_BOULDER_RUPEE)
    
    # Bean sprout fairies near theater
    for i in range(1, 4):
        region.locations.append(getattr(OOTLocations, f"LW_BEAN_SPROUT_NEAR_THEATER_FAIRY_{i}"))
    
    # Grass cutting
    for i in range(4, 10):
        region.locations.append(getattr(OOTLocations, f"LW_GRASS_{i}"))
    
    return region

def create_lw_near_shortcuts_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create LW Near Shortcuts Grotto region."""
    region = Region("LW Near Shortcuts Grotto", player, multiworld)
    
    region.locations.append(OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_CHEST)
    region.locations.append(OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_FISH)
    region.locations.append(OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_GOSSIP_STONE)
    region.locations.append(OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_BEEHIVE_LEFT)
    region.locations.append(OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_BEEHIVE_RIGHT)
    
    # Grass cutting
    for i in range(1, 5):
        region.locations.append(getattr(OOTLocations, f"LW_NEAR_SHORTCUTS_GROTTO_GRASS_{i}"))
    
    return region

def create_deku_theater(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create Deku Theater region."""
    region = Region("Deku Theater", player, multiworld)
    
    region.locations.append(OOTLocations.DEKU_THEATER_SKULL_MASK)
    region.locations.append(OOTLocations.DEKU_THEATER_MASK_OF_TRUTH)
    
    return region

def create_lw_scrubs_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create LW Scrubs Grotto region."""
    region = Region("LW Scrubs Grotto", player, multiworld)
    
    region.locations.append(OOTLocations.LW_DEKU_SCRUB_GROTTO_REAR)
    region.locations.append(OOTLocations.LW_DEKU_SCRUB_GROTTO_FRONT)
    region.locations.append(OOTLocations.LW_DEKU_SCRUB_GROTTO_BEEHIVE)
    region.locations.append(OOTLocations.LW_DEKU_SCRUB_GROTTO_SUN_FAIRY)
    
    return region

def create_lw_bridge_from_forest(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create LW Bridge From Forest region."""
    region = Region("LW Bridge From Forest", player, multiworld)
    
    region.locations.append(OOTLocations.LW_GIFT_FROM_SARIA)
    
    return region

def create_lw_bridge(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create LW Bridge region."""
    region = Region("LW Bridge", player, multiworld)
    # This is primarily a connection point, no specific locations
    return region

def set_lost_woods_entrances(regions: Dict[str, Region], entrances_map: Dict[str, str]) -> None:
    """Set up entrances between Lost Woods regions."""
    
    # Main connections
    connect_entrance(regions[OOTRegions.LW_FOREST_EXIT], regions[OOTRegions.KOKIRI_FOREST], lambda state: True)
    connect_entrance(regions[OOTRegions.THE_LOST_WOODS], regions[OOTRegions.LW_FOREST_EXIT], lambda state: True)
    connect_entrance(regions[OOTRegions.THE_LOST_WOODS], regions[OOTRegions.GORON_CITY_WOODS_WARP], lambda state: True)
    
    # Access to bridge area
    connect_entrance(regions[OOTRegions.THE_LOST_WOODS], regions[OOTRegions.LW_BRIDGE], 
                    lambda state: (is_adult(state) and 
                                  (can_plant_bean(state, OOTRegions.THE_LOST_WOODS) or 
                                   logic.logic_tricks)) or 
                                 has_item(state, "Hover Boots") or 
                                 has_item(state, "Longshot"))
    
    # Zora River shortcut
    connect_entrance(regions[OOTRegions.THE_LOST_WOODS], regions[OOTRegions.ZR_FROM_SHORTCUT], 
                    lambda state: (has_item(state, "Silver Scale") or 
                                  has_item(state, "Iron Boots") or 
                                  (logic.logic_tricks and is_child(state) and 
                                   has_item(state, "Bronze Scale") and can_jumpslash(state))))
    
    # Beyond Mido access
    connect_entrance(regions[OOTRegions.THE_LOST_WOODS], regions[OOTRegions.LW_BEYOND_MIDO], 
                    lambda state: (is_child(state) or 
                                  has_item(state, "Saria's Song") or 
                                  logic.logic_tricks))
    
    # Grotto access from main Lost Woods
    connect_entrance(regions[OOTRegions.THE_LOST_WOODS], regions[OOTRegions.LW_NEAR_SHORTCUTS_GROTTO], 
                    lambda state: blast_or_smash(state))
    
    # From Beyond Mido
    connect_entrance(regions[OOTRegions.LW_BEYOND_MIDO], regions[OOTRegions.LW_FOREST_EXIT], lambda state: True)
    connect_entrance(regions[OOTRegions.LW_BEYOND_MIDO], regions[OOTRegions.THE_LOST_WOODS], 
                    lambda state: is_child(state) or has_item(state, "Saria's Song"))
    connect_entrance(regions[OOTRegions.LW_BEYOND_MIDO], regions[OOTRegions.SFM_ENTRYWAY], lambda state: True)
    connect_entrance(regions[OOTRegions.LW_BEYOND_MIDO], regions[OOTRegions.DEKU_THEATER], lambda state: True)
    connect_entrance(regions[OOTRegions.LW_BEYOND_MIDO], regions[OOTRegions.LW_SCRUBS_GROTTO], 
                    lambda state: blast_or_smash(state))
    
    # Bridge connections
    connect_entrance(regions[OOTRegions.LW_BRIDGE], regions[OOTRegions.KOKIRI_FOREST], lambda state: True)
    connect_entrance(regions[OOTRegions.LW_BRIDGE], regions[OOTRegions.HYRULE_FIELD], lambda state: True)
    connect_entrance(regions[OOTRegions.LW_BRIDGE], regions[OOTRegions.THE_LOST_WOODS], 
                    lambda state: has_item(state, "Longshot"))
    
    # Return connections from grottos
    connect_entrance(regions[OOTRegions.LW_NEAR_SHORTCUTS_GROTTO], regions[OOTRegions.THE_LOST_WOODS], lambda state: True)
    connect_entrance(regions[OOTRegions.DEKU_THEATER], regions[OOTRegions.LW_BEYOND_MIDO], lambda state: True)
    connect_entrance(regions[OOTRegions.LW_SCRUBS_GROTTO], regions[OOTRegions.LW_BEYOND_MIDO], lambda state: True)

def set_lost_woods_rules(regions: Dict[str, Region], logic: "OOTLogic") -> None:
    """Set access rules for all Lost Woods locations."""
    
    # The Lost Woods main region
    set_the_lost_woods_rules(regions[OOTRegions.THE_LOST_WOODS], logic)
    
    # LW Beyond Mido region
    set_lw_beyond_mido_rules(regions[OOTRegions.LW_BEYOND_MIDO], logic)
    
    # Grotto rules
    set_lw_grotto_rules(regions, logic)
    
    # Theater rules
    set_deku_theater_rules(regions[OOTRegions.DEKU_THEATER], logic)

def set_the_lost_woods_rules(region: Region, logic: "OOTLogic") -> None:
    """Set access rules for The Lost Woods main region."""
    
    # Skull Kid - child with Saria's Song
    set_rule(region.locations[OOTLocations.LW_SKULL_KID], 
             lambda state: is_child(state) and has_item(state, "Saria's Song"))
    
    # Trading sequence
    set_rule(region.locations[OOTLocations.LW_TRADE_COJIRO], 
             lambda state: is_adult(state) and has_item(state, "Cojiro"))
    set_rule(region.locations[OOTLocations.LW_TRADE_ODD_POTION], 
             lambda state: is_adult(state) and has_item(state, "Odd Potion"))
    
    # Ocarina memory game - child with ocarina and all 5 buttons
    set_rule(region.locations[OOTLocations.LW_OCARINA_MEMORY_GAME], 
             lambda state: (is_child(state) and 
                           has_item(state, "Fairy Ocarina") and 
                           ocarina_buttons(state) >= 5))
    
    # Target practice - child with slingshot
    set_rule(region.locations[OOTLocations.LW_TARGET_IN_WOODS], 
             lambda state: is_child(state) and has_item(state, "Fairy Slingshot"))
    
    # Deku scrub - child who can stun deku
    set_rule(region.locations[OOTLocations.LW_DEKU_SCRUB_NEAR_BRIDGE], 
             lambda state: is_child(state) and can_stun_deku(state))
    
    # Gold Skulltula bean patch
    set_rule(region.locations[OOTLocations.LW_GS_BEAN_PATCH_NEAR_BRIDGE], 
             lambda state: can_spawn_soil_skull(state) and can_attack(state))
    
    # Shortcut rupees - need to access underwater area
    shortcut_rule = lambda state: (is_child(state) and 
                                  (has_item(state, "Silver Scale") or 
                                   has_item(state, "Iron Boots")))
    for i in range(1, 9):
        set_rule(region.locations[getattr(OOTLocations, f"LW_SHORTCUT_RUPEE_{i}")], shortcut_rule)
    
    # Bean sprout fairies
    bean_sprout_rule = lambda state: (is_child(state) and 
                                     has_item(state, "Magic Bean") and 
                                     can_use_song_of_storms(state))
    for i in range(1, 4):
        set_rule(region.locations[getattr(OOTLocations, f"LW_BEAN_SPROUT_NEAR_BRIDGE_FAIRY_{i}")], 
                bean_sprout_rule)
    
    # Gossip stone interactions
    set_rule(region.locations[OOTLocations.LW_GOSSIP_STONE_FAIRY], 
             lambda state: can_call_gossip_fairy_except_suns(state, logic))
    set_rule(region.locations[OOTLocations.LW_GOSSIP_STONE_FAIRY_BIG], 
             lambda state: can_use_song_of_storms(state))
    set_rule(region.locations[OOTLocations.LW_SHORTCUT_STORMS_FAIRY], 
             lambda state: can_use_song_of_storms(state))
    
    # Grass cutting
    grass_rule = lambda state: can_cut_shrubs(state)
    for i in range(1, 4):
        set_rule(region.locations[getattr(OOTLocations, f"LW_GRASS_{i}")], grass_rule)

def set_lw_beyond_mido_rules(region: Region, logic: "OOTLogic") -> None:
    """Set access rules for LW Beyond Mido region."""
    
    # Deku scrubs near theater
    scrub_rule = lambda state: is_child(state) and can_stun_deku(state)
    set_rule(region.locations[OOTLocations.LW_DEKU_SCRUB_NEAR_DEKU_THEATER_RIGHT], scrub_rule)
    set_rule(region.locations[OOTLocations.LW_DEKU_SCRUB_NEAR_DEKU_THEATER_LEFT], scrub_rule)
    
    # Gold Skulltula above theater
    set_rule(region.locations[OOTLocations.LW_GS_ABOVE_THEATER], 
             lambda state: (is_adult(state) and 
                           ((can_plant_bean(state, OOTRegions.LW_BEYOND_MIDO) and can_attack(state)) or 
                            (logic.logic_tricks and has_item(state, "Hookshot") and 
                             (has_item(state, "Longshot") or 
                              has_item(state, "Fairy Bow") or 
                              has_item(state, "Fairy Slingshot") or 
                              has_item(state, "Bombchu") or 
                              has_item(state, "Din's Fire")))) and 
                           can_get_night_time_gs(state)))
    
    # Gold Skulltula bean patch near theater
    set_rule(region.locations[OOTLocations.LW_GS_BEAN_PATCH_NEAR_THEATER], 
             lambda state: can_spawn_soil_skull(state) and 
                          (can_attack(state) or 
                           (logic.scrub_shuffle == "off" and can_reflect_nuts(state))))
    
    # Boulder rupee
    set_rule(region.locations[OOTLocations.LW_BOULDER_RUPEE], 
             lambda state: blast_or_smash(state))
    
    # Bean sprout fairies near theater
    bean_sprout_rule = lambda state: (is_child(state) and 
                                     has_item(state, "Magic Bean") and 
                                     can_use_song_of_storms(state))
    for i in range(1, 4):
        set_rule(region.locations[getattr(OOTLocations, f"LW_BEAN_SPROUT_NEAR_THEATER_FAIRY_{i}")], 
                bean_sprout_rule)
    
    # Grass cutting
    grass_rule = lambda state: can_cut_shrubs(state)
    for i in range(4, 10):
        set_rule(region.locations[getattr(OOTLocations, f"LW_GRASS_{i}")], grass_rule)

def set_lw_grotto_rules(regions: Dict[str, Region], logic: "OOTLogic") -> None:
    """Set access rules for Lost Woods grotto locations."""
    
    # Near Shortcuts Grotto
    shortcuts_grotto = regions[OOTRegions.LW_NEAR_SHORTCUTS_GROTTO]
    
    # Chest is always accessible in grotto
    set_rule(shortcuts_grotto.locations[OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_CHEST], 
             lambda state: True)
    
    # Fish needs bottle
    set_rule(shortcuts_grotto.locations[OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_FISH], 
             lambda state: has_bottle(state))
    
    # Gossip stone fairies
    set_rule(shortcuts_grotto.locations[OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_GOSSIP_STONE_FAIRY], 
             lambda state: can_call_gossip_fairy(state))
    set_rule(shortcuts_grotto.locations[OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_GOSSIP_STONE_FAIRY_BIG], 
             lambda state: can_use_song_of_storms(state))
    
    # Beehives
    beehive_rule = lambda state: can_break_lower_beehives(state)
    set_rule(shortcuts_grotto.locations[OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_BEEHIVE_LEFT], beehive_rule)
    set_rule(shortcuts_grotto.locations[OOTLocations.LW_NEAR_SHORTCUTS_GROTTO_BEEHIVE_RIGHT], beehive_rule)
    
    # Grass cutting
    grass_rule = lambda state: can_cut_shrubs(state)
    for i in range(1, 5):
        set_rule(shortcuts_grotto.locations[getattr(OOTLocations, f"LW_NEAR_SHORTCUTS_GROTTO_GRASS_{i}")], 
                grass_rule)
    
    # Scrubs Grotto
    scrubs_grotto = regions[OOTRegions.LW_SCRUBS_GROTTO]
    
    # Deku scrubs
    scrub_rule = lambda state: can_stun_deku(state)
    set_rule(scrubs_grotto.locations[OOTLocations.LW_DEKU_SCRUB_GROTTO_REAR], scrub_rule)
    set_rule(scrubs_grotto.locations[OOTLocations.LW_DEKU_SCRUB_GROTTO_FRONT], scrub_rule)
    
    # Beehive
    set_rule(scrubs_grotto.locations[OOTLocations.LW_DEKU_SCRUB_GROTTO_BEEHIVE], 
             lambda state: can_break_upper_beehives(state))
    
    # Sun fairy
    set_rule(scrubs_grotto.locations[OOTLocations.LW_DEKU_SCRUB_GROTTO_SUN_FAIRY], 
             lambda state: has_item(state, "Sun's Song"))

def set_deku_theater_rules(region: Region, logic: "OOTLogic") -> None:
    """Set access rules for Deku Theater locations."""
    
    # Skull mask - child with borrowed skull mask
    set_rule(region.locations[OOTLocations.DEKU_THEATER_SKULL_MASK], 
             lambda state: is_child(state) and borrow_skull_mask(state))
    
    # Mask of Truth - child with all right masks borrowed
    set_rule(region.locations[OOTLocations.DEKU_THEATER_MASK_OF_TRUTH], 
             lambda state: is_child(state) and borrow_right_masks(state))

# Additional helper functions needed for Lost Woods logic
def ocarina_buttons(state: CollectionState) -> int:
    """Count available ocarina buttons."""
    # This would need to be implemented based on actual item progression
    # For now, assume 5 if has ocarina songs
    if (has_item(state, "Zelda's Lullaby") and 
        has_item(state, "Epona's Song") and 
        has_item(state, "Saria's Song") and 
        has_item(state, "Song of Time") and 
        has_item(state, "Song of Storms")):
        return 5
    return 0

def can_stun_deku(state: CollectionState) -> bool:
    """Check if player can stun Deku Scrubs."""
    return (has_item(state, "Deku Shield") or 
            has_item(state, "Hylian Shield") or 
            can_use_nuts(state))

def can_use_nuts(state: CollectionState) -> bool:
    """Check if player can use Deku Nuts."""
    return has_item(state, "Deku Nuts")

def can_reflect_nuts(state: CollectionState) -> bool:
    """Check if player can reflect Deku Nuts."""
    return (has_item(state, "Deku Shield") or 
            has_item(state, "Hylian Shield") or 
            has_item(state, "Mirror Shield"))

def can_break_upper_beehives(state: CollectionState) -> bool:
    """Check if player can break upper beehives."""
    return (has_item(state, "Fairy Bow") or 
            has_item(state, "Hookshot") or 
            has_item(state, "Longshot") or 
            has_item(state, "Boomerang"))

def can_plant_bean(state: CollectionState, region: str) -> bool:
    """Check if player can plant bean in specific region."""
    return (is_child(state) and 
            has_item(state, "Magic Bean") and 
            is_adult(state))  # Need to come back as adult

def borrow_skull_mask(state: CollectionState) -> bool:
    """Check if player can borrow skull mask."""
    # Simplified version - actual implementation would be more complex
    return has_item(state, "Skull Mask")

def borrow_right_masks(state: CollectionState) -> bool:
    """Check if player has borrowed all the right masks."""
    # Simplified version - actual implementation would be more complex
    return (has_item(state, "Skull Mask") and 
            has_item(state, "Spooky Mask") and 
            has_item(state, "Bunny Hood") and 
            has_item(state, "Goron Mask") and 
            has_item(state, "Zora Mask"))
