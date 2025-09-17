from typing import Dict, List, TYPE_CHECKING
from BaseClasses import Region, CollectionState
from worlds.generic.Rules import set_rule
from ..Items import SohItem
from ..Locations import SohLocation, SohLocationData
from ..Enums import Items
from ..Rules import *

if TYPE_CHECKING:
    from .. import SohWorld

# Sacred Forest Meadow region names
region_names: list[str] = [
    "SFM Entryway",
    "Sacred Forest Meadow",
    "SFM Fairy Grotto", 
    "SFM Wolfos Grotto",
    "SFM Storms Grotto"
]

def create_regions_and_rules(world: "SohWorld") -> None:
    """Set access rules for Sacred Forest Meadow regions (regions already created)."""
    # Set region access rules
    set_region_rules(world)
    
    # Location access rules will be set later after locations are created

def set_region_rules(world: "SohWorld") -> None:
    """Set access rules for Sacred Forest Meadow region entrances."""
    
    # SFM Entryway -> Sacred Forest Meadow requires adult or ability to defeat Wolfos
    world.get_entrance("SFM Entryway -> Sacred Forest Meadow").access_rule = \
        lambda state: is_adult(state, world) or can_attack(state, world)
    
    # SFM Entryway -> SFM Wolfos Grotto requires bomb/explosive access
    world.get_entrance("SFM Entryway -> SFM Wolfos Grotto").access_rule = \
        lambda state: blast_or_smash(state, world)
    
    # Sacred Forest Meadow -> SFM Storms Grotto requires Song of Storms  
    world.get_entrance("Sacred Forest Meadow -> SFM Storms Grotto").access_rule = \
        lambda state: can_use(Items.SONG_OF_STORMS.value, state, world)

def set_location_rules(world: "SohWorld") -> None:
    """Set access rules for Sacred Forest Meadow locations."""
    
    # Song from Saria (child with Zelda's Letter)
    set_rule(world.get_location("Song from Saria"),
             lambda state: not is_adult(state, world) and
                           has_item(Items.ZELDAS_LETTER.value, state, world))
    
    # Sheik in Forest (adult only)
    set_rule(world.get_location("Sheik in Forest"), 
             lambda state: is_adult(state, world))
    
    # SFM GS (adult with hookshot/boomerang and nighttime)
    set_rule(world.get_location("SFM GS"),
             lambda state: is_adult(state, world) and
                           (can_use(Items.HOOKSHOT.value, state, world) or
                            can_use(Items.BOOMERANG.value, state, world)))
    
    # SFM Wolfos Grotto Chest (can kill 2 wolfos)
    set_rule(world.get_location("SFM Wolfos Grotto Chest"),
             lambda state: can_attack(state, world))
    
    # Gossip stone fairies
    set_rule(world.get_location("SFM Gossip Stone Fairy"),
             lambda state: True)  # CallGossipFairyExceptSuns - always accessible
    
    set_rule(world.get_location("SFM Gossip Stone Big Fairy"), 
             lambda state: can_use(Items.SONG_OF_STORMS.value, state, world))

def create_regions(multiworld, player: int, logic: "OOTLogic") -> Dict[str, Region]:
    """Create all Sacred Forest Meadow regions and their access rules."""
    regions = {}

    # Sacred Forest Meadow regions
    regions[OOTRegions.SFM_ENTRYWAY] = create_sfm_entryway(multiworld, player, logic)
    regions[OOTRegions.SACRED_FOREST_MEADOW] = create_sacred_forest_meadow(multiworld, player, logic)
    regions[OOTRegions.SFM_FAIRY_GROTTO] = create_sfm_fairy_grotto(multiworld, player, logic)
    regions[OOTRegions.SFM_WOLFOS_GROTTO] = create_sfm_wolfos_grotto(multiworld, player, logic)
    regions[OOTRegions.SFM_STORMS_GROTTO] = create_sfm_storms_grotto(multiworld, player, logic)

    return regions

def create_sfm_entryway(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create SFM Entryway region."""
    region = Region("SFM Entryway", player, multiworld)
    # This is primarily a transitional area, no specific locations
    return region

def create_sacred_forest_meadow(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create Sacred Forest Meadow main region."""
    region = Region("Sacred Forest Meadow", player, multiworld)
    
    # Major quest locations
    region.locations.append(OOTLocations.SONG_FROM_SARIA)
    region.locations.append(OOTLocations.SHEIK_IN_FOREST)
    
    # Gold Skulltula
    region.locations.append(OOTLocations.SFM_GS)
    
    # Gossip stone interactions - maze lower
    region.locations.append(OOTLocations.SFM_MAZE_LOWER_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.SFM_MAZE_LOWER_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.SFM_MAZE_LOWER_GOSSIP_STONE)
    
    # Gossip stone interactions - maze upper
    region.locations.append(OOTLocations.SFM_MAZE_UPPER_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.SFM_MAZE_UPPER_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.SFM_MAZE_UPPER_GOSSIP_STONE)
    
    # Gossip stone interactions - Saria area
    region.locations.append(OOTLocations.SFM_SARIA_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.SFM_SARIA_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.SFM_SARIA_GOSSIP_STONE)
    
    return region

def create_sfm_fairy_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create SFM Fairy Grotto region."""
    region = Region("SFM Fairy Grotto", player, multiworld)
    
    # All 8 fairies in the grotto
    for i in range(1, 9):
        region.locations.append(getattr(OOTLocations, f"SFM_FAIRY_GROTTO_FAIRY_{i}"))
    
    return region

def create_sfm_wolfos_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create SFM Wolfos Grotto region."""
    region = Region("SFM Wolfos Grotto", player, multiworld)
    
    region.locations.append(OOTLocations.SFM_WOLFOS_GROTTO_CHEST)
    
    return region

def create_sfm_storms_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create SFM Storms Grotto region."""
    region = Region("SFM Storms Grotto", player, multiworld)
    
    region.locations.append(OOTLocations.SFM_DEKU_SCRUB_GROTTO_REAR)
    region.locations.append(OOTLocations.SFM_DEKU_SCRUB_GROTTO_FRONT)
    region.locations.append(OOTLocations.SFM_STORMS_GROTTO_BEEHIVE)
    
    return region

def set_sacred_forest_meadow_entrances(regions: Dict[str, Region], entrances_map: Dict[str, str]) -> None:
    """Set up entrances between Sacred Forest Meadow regions."""
    
    # Main connections
    connect_entrance(regions[OOTRegions.SFM_ENTRYWAY], regions[OOTRegions.LW_BEYOND_MIDO], lambda state: True)
    connect_entrance(regions[OOTRegions.SFM_ENTRYWAY], regions[OOTRegions.SACRED_FOREST_MEADOW], 
                    lambda state: is_adult(state) or can_kill_enemy(state, "Wolfos"))
    connect_entrance(regions[OOTRegions.SFM_ENTRYWAY], regions[OOTRegions.SFM_WOLFOS_GROTTO], 
                    lambda state: can_open_bomb_grotto(state))
    
    # From Sacred Forest Meadow
    connect_entrance(regions[OOTRegions.SACRED_FOREST_MEADOW], regions[OOTRegions.SFM_ENTRYWAY], lambda state: True)
    connect_entrance(regions[OOTRegions.SACRED_FOREST_MEADOW], regions[OOTRegions.FOREST_TEMPLE_ENTRYWAY], 
                    lambda state: has_item(state, "Hookshot"))
    connect_entrance(regions[OOTRegions.SACRED_FOREST_MEADOW], regions[OOTRegions.SFM_FAIRY_GROTTO], lambda state: True)
    connect_entrance(regions[OOTRegions.SACRED_FOREST_MEADOW], regions[OOTRegions.SFM_STORMS_GROTTO], 
                    lambda state: can_open_storms_grotto(state))
    
    # Return connections from grottos
    connect_entrance(regions[OOTRegions.SFM_FAIRY_GROTTO], regions[OOTRegions.SACRED_FOREST_MEADOW], lambda state: True)
    connect_entrance(regions[OOTRegions.SFM_WOLFOS_GROTTO], regions[OOTRegions.SFM_ENTRYWAY], lambda state: True)
    connect_entrance(regions[OOTRegions.SFM_STORMS_GROTTO], regions[OOTRegions.SACRED_FOREST_MEADOW], lambda state: True)

def set_sacred_forest_meadow_rules(regions: Dict[str, Region], logic: "OOTLogic") -> None:
    """Set access rules for all Sacred Forest Meadow locations."""
    
    # Main Sacred Forest Meadow rules
    set_sacred_forest_meadow_main_rules(regions[OOTRegions.SACRED_FOREST_MEADOW], logic)
    
    # Fairy Grotto rules
    set_sfm_fairy_grotto_rules(regions[OOTRegions.SFM_FAIRY_GROTTO], logic)
    
    # Wolfos Grotto rules
    set_sfm_wolfos_grotto_rules(regions[OOTRegions.SFM_WOLFOS_GROTTO], logic)
    
    # Storms Grotto rules
    set_sfm_storms_grotto_rules(regions[OOTRegions.SFM_STORMS_GROTTO], logic)

def set_sacred_forest_meadow_main_rules(region: Region, logic: "OOTLogic") -> None:
    """Set access rules for main Sacred Forest Meadow region."""
    
    # Song from Saria - child with Zelda's Letter
    set_rule(region.locations[OOTLocations.SONG_FROM_SARIA], 
             lambda state: is_child(state) and has_item(state, "Zelda's Letter"))
    
    # Sheik teaches song - adult only
    set_rule(region.locations[OOTLocations.SHEIK_IN_FOREST], 
             lambda state: is_adult(state))
    
    # Gold Skulltula - adult with hookshot/boomerang at night
    set_rule(region.locations[OOTLocations.SFM_GS], 
             lambda state: (is_adult(state) and 
                           hookshot_or_boomerang(state) and 
                           can_get_night_time_gs(state)))
    
    # Gossip stone fairies - maze lower
    set_rule(region.locations[OOTLocations.SFM_MAZE_LOWER_GOSSIP_STONE_FAIRY], 
             lambda state: can_call_gossip_fairy_except_suns(state, logic))
    set_rule(region.locations[OOTLocations.SFM_MAZE_LOWER_GOSSIP_STONE_FAIRY_BIG], 
             lambda state: can_use_song_of_storms(state))
    
    # Gossip stone fairies - maze upper
    set_rule(region.locations[OOTLocations.SFM_MAZE_UPPER_GOSSIP_STONE_FAIRY], 
             lambda state: can_call_gossip_fairy_except_suns(state, logic))
    set_rule(region.locations[OOTLocations.SFM_MAZE_UPPER_GOSSIP_STONE_FAIRY_BIG], 
             lambda state: can_use_song_of_storms(state))
    
    # Gossip stone fairies - Saria area
    set_rule(region.locations[OOTLocations.SFM_SARIA_GOSSIP_STONE_FAIRY], 
             lambda state: can_call_gossip_fairy_except_suns(state, logic))
    set_rule(region.locations[OOTLocations.SFM_SARIA_GOSSIP_STONE_FAIRY_BIG], 
             lambda state: can_use_song_of_storms(state))
    
    # Gossip stones themselves are always accessible
    set_rule(region.locations[OOTLocations.SFM_MAZE_LOWER_GOSSIP_STONE], lambda state: True)
    set_rule(region.locations[OOTLocations.SFM_MAZE_UPPER_GOSSIP_STONE], lambda state: True)
    set_rule(region.locations[OOTLocations.SFM_SARIA_GOSSIP_STONE], lambda state: True)

def set_sfm_fairy_grotto_rules(region: Region, logic: "OOTLogic") -> None:
    """Set access rules for SFM Fairy Grotto."""
    
    # All fairies are freely accessible in the grotto
    for i in range(1, 9):
        set_rule(region.locations[getattr(OOTLocations, f"SFM_FAIRY_GROTTO_FAIRY_{i}")], 
                lambda state: True)

def set_sfm_wolfos_grotto_rules(region: Region, logic: "OOTLogic") -> None:
    """Set access rules for SFM Wolfos Grotto."""
    
    # Chest requires killing 2 Wolfos at close range
    set_rule(region.locations[OOTLocations.SFM_WOLFOS_GROTTO_CHEST], 
             lambda state: can_kill_enemy(state, "Wolfos", close_range=True, count=2))

def set_sfm_storms_grotto_rules(region: Region, logic: "OOTLogic") -> None:
    """Set access rules for SFM Storms Grotto."""
    
    # Deku scrubs
    scrub_rule = lambda state: can_stun_deku(state)
    set_rule(region.locations[OOTLocations.SFM_DEKU_SCRUB_GROTTO_REAR], scrub_rule)
    set_rule(region.locations[OOTLocations.SFM_DEKU_SCRUB_GROTTO_FRONT], scrub_rule)
    
    # Beehive
    set_rule(region.locations[OOTLocations.SFM_STORMS_GROTTO_BEEHIVE], 
             lambda state: can_break_upper_beehives(state))

# Additional helper functions for Sacred Forest Meadow
def can_kill_enemy(state: CollectionState, enemy_type: str, close_range: bool = False, count: int = 1) -> bool:
    """Check if player can kill specific enemy type."""
    if enemy_type == "Wolfos":
        if close_range:
            # Close range weapons for Wolfos
            return (has_item(state, "Kokiri Sword") or 
                   has_item(state, "Master Sword") or 
                   has_item(state, "Biggoron Sword") or 
                   has_item(state, "Deku Stick"))
        else:
            # Any attack method works for Wolfos
            return can_attack(state)
    return can_attack(state)

def can_open_bomb_grotto(state: CollectionState) -> bool:
    """Check if player can open bomb grotto."""
    return blast_or_smash(state)

def can_open_storms_grotto(state: CollectionState) -> bool:
    """Check if player can open storms grotto."""
    return can_use_song_of_storms(state)
