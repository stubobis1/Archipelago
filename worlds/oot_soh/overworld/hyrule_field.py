from typing import Dict, List
from BaseClasses import Region, CollectionState
from ..Enums import Items
from ..Rules import *

def create_regions(multiworld, player: int, logic: "OOTLogic") -> Dict[str, Region]:
    """Create all Hyrule Field regions and their access rules."""
    regions = {}

    # Main Hyrule Field region
    regions[OOTRegions.HYRULE_FIELD] = create_hyrule_field(multiworld, player, logic)
    
    # Hyrule Field Grottos
    regions[OOTRegions.HF_SOUTHEAST_GROTTO] = create_hf_southeast_grotto(multiworld, player, logic)
    regions[OOTRegions.HF_OPEN_GROTTO] = create_hf_open_grotto(multiworld, player, logic)
    regions[OOTRegions.HF_INSIDE_FENCE_GROTTO] = create_hf_inside_fence_grotto(multiworld, player, logic)
    regions[OOTRegions.HF_COW_GROTTO] = create_hf_cow_grotto(multiworld, player, logic)
    regions[OOTRegions.HF_COW_GROTTO_BEHIND_WEBS] = create_hf_cow_grotto_behind_webs(multiworld, player, logic)
    regions[OOTRegions.HF_NEAR_MARKET_GROTTO] = create_hf_near_market_grotto(multiworld, player, logic)
    regions[OOTRegions.HF_FAIRY_GROTTO] = create_hf_fairy_grotto(multiworld, player, logic)
    regions[OOTRegions.HF_NEAR_KAK_GROTTO] = create_hf_near_kak_grotto(multiworld, player, logic)
    regions[OOTRegions.HF_TEKTITE_GROTTO] = create_hf_tektite_grotto(multiworld, player, logic)

    return regions

def create_hyrule_field(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create main Hyrule Field region."""
    region = Region("Hyrule Field", player, multiworld)
    
    # Major quest items
    region.locations.append(OOTLocations.HF_OCARINA_OF_TIME_ITEM)
    region.locations.append(OOTLocations.SONG_FROM_OCARINA_OF_TIME)
    
    # Storms fairy
    region.locations.append(OOTLocations.HF_POND_STORMS_FAIRY)
    
    # Central grass locations
    for i in range(1, 13):
        region.locations.append(getattr(OOTLocations, f"HF_CENTRAL_GRASS_{i}"))
    
    # South grass locations
    for i in range(1, 13):
        region.locations.append(getattr(OOTLocations, f"HF_SOUTH_GRASS_{i}"))
    
    # Near Market grass locations
    for i in range(1, 13):
        region.locations.append(getattr(OOTLocations, f"HF_NEAR_MARKET_GRASS_{i}"))
    
    # Near KF grass locations
    for i in range(1, 13):
        region.locations.append(getattr(OOTLocations, f"HF_NEAR_KF_GRASS_{i}"))
    
    return region

def create_hf_southeast_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create HF Southeast Grotto region."""
    region = Region("HF Southeast Grotto", player, multiworld)
    
    region.locations.append(OOTLocations.HF_SOUTHEAST_GROTTO_CHEST)
    region.locations.append(OOTLocations.HF_SOUTHEAST_GROTTO_FISH)
    region.locations.append(OOTLocations.HF_SOUTHEAST_GROTTO_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.HF_SOUTHEAST_GROTTO_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.HF_SOUTHEAST_GROTTO_GOSSIP_STONE)
    region.locations.append(OOTLocations.HF_SOUTHEAST_GROTTO_BEEHIVE_LEFT)
    region.locations.append(OOTLocations.HF_SOUTHEAST_GROTTO_BEEHIVE_RIGHT)
    
    for i in range(1, 5):
        region.locations.append(getattr(OOTLocations, f"HF_SOUTHEAST_GROTTO_GRASS_{i}"))
    
    return region

def create_hf_open_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create HF Open Grotto region."""
    region = Region("HF Open Grotto", player, multiworld)
    
    region.locations.append(OOTLocations.HF_OPEN_GROTTO_CHEST)
    region.locations.append(OOTLocations.HF_OPEN_GROTTO_FISH)
    region.locations.append(OOTLocations.HF_OPEN_GROTTO_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.HF_OPEN_GROTTO_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.HF_OPEN_GROTTO_GOSSIP_STONE)
    region.locations.append(OOTLocations.HF_OPEN_GROTTO_BEEHIVE_LEFT)
    region.locations.append(OOTLocations.HF_OPEN_GROTTO_BEEHIVE_RIGHT)
    
    for i in range(1, 5):
        region.locations.append(getattr(OOTLocations, f"HF_OPEN_GROTTO_GRASS_{i}"))
    
    return region

def create_hf_inside_fence_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create HF Inside Fence Grotto region."""
    region = Region("HF Inside Fence Grotto", player, multiworld)
    
    region.locations.append(OOTLocations.HF_DEKU_SCRUB_GROTTO)
    region.locations.append(OOTLocations.HF_INSIDE_FENCE_GROTTO_BEEHIVE)
    region.locations.append(OOTLocations.HF_FENCE_GROTTO_STORMS_FAIRY)
    
    return region

def create_hf_cow_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create HF Cow Grotto region."""
    region = Region("HF Cow Grotto", player, multiworld)
    # This is just the entrance area, main content is behind webs
    return region

def create_hf_cow_grotto_behind_webs(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create HF Cow Grotto Behind Webs region."""
    region = Region("HF Cow Grotto Behind Webs", player, multiworld)
    
    region.locations.append(OOTLocations.HF_GS_COW_GROTTO)
    region.locations.append(OOTLocations.HF_COW_GROTTO_COW)
    region.locations.append(OOTLocations.HF_COW_GROTTO_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.HF_COW_GROTTO_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.HF_COW_GROTTO_GOSSIP_STONE)
    region.locations.append(OOTLocations.HF_COW_GROTTO_POT_1)
    region.locations.append(OOTLocations.HF_COW_GROTTO_POT_2)
    region.locations.append(OOTLocations.HF_COW_GROTTO_GRASS_1)
    region.locations.append(OOTLocations.HF_COW_GROTTO_GRASS_2)
    
    return region

def create_hf_near_market_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create HF Near Market Grotto region."""
    region = Region("HF Near Market Grotto", player, multiworld)
    
    region.locations.append(OOTLocations.HF_NEAR_MARKET_GROTTO_CHEST)
    region.locations.append(OOTLocations.HF_NEAR_MARKET_GROTTO_FISH)
    region.locations.append(OOTLocations.HF_NEAR_MARKET_GROTTO_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.HF_NEAR_MARKET_GROTTO_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.HF_NEAR_MARKET_GROTTO_GOSSIP_STONE)
    region.locations.append(OOTLocations.HF_NEAR_MARKET_GROTTO_BEEHIVE_LEFT)
    region.locations.append(OOTLocations.HF_NEAR_MARKET_GROTTO_BEEHIVE_RIGHT)
    
    for i in range(1, 5):
        region.locations.append(getattr(OOTLocations, f"HF_NEAR_MARKET_GROTTO_GRASS_{i}"))
    
    return region

def create_hf_fairy_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create HF Fairy Grotto region."""
    region = Region("HF Fairy Grotto", player, multiworld)
    
    for i in range(1, 9):
        region.locations.append(getattr(OOTLocations, f"HF_FAIRY_GROTTO_FAIRY_{i}"))
    
    return region

def create_hf_near_kak_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create HF Near Kak Grotto region."""
    region = Region("HF Near Kak Grotto", player, multiworld)
    
    region.locations.append(OOTLocations.HF_GS_NEAR_KAK_GROTTO)
    
    return region

def create_hf_tektite_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create HF Tektite Grotto region."""
    region = Region("HF Tektite Grotto", player, multiworld)
    
    region.locations.append(OOTLocations.HF_TEKTITE_GROTTO_FREESTANDING_POH)
    
    return region

def set_hyrule_field_entrances(regions: Dict[str, Region], entrances_map: Dict[str, str]) -> None:
    """Set up entrances between Hyrule Field regions."""
    
    # Main Hyrule Field connections to other overworld areas
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.LW_BRIDGE], lambda state: True)
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.LAKE_HYLIA], lambda state: True)
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.GERUDO_VALLEY], lambda state: True)
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.MARKET_ENTRANCE], lambda state: True)
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.KAKARIKO_VILLAGE], lambda state: True)
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.ZR_FRONT], lambda state: True)
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.LON_LON_RANCH], lambda state: True)
    
    # Grotto connections from main field
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.HF_SOUTHEAST_GROTTO], 
                    lambda state: blast_or_smash(state))
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.HF_OPEN_GROTTO], lambda state: True)
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.HF_INSIDE_FENCE_GROTTO], 
                    lambda state: can_open_bomb_grotto(state))
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.HF_COW_GROTTO], 
                    lambda state: (has_item(state, "Megaton Hammer") or is_child(state)) and 
                                 can_open_bomb_grotto(state))
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.HF_NEAR_MARKET_GROTTO], 
                    lambda state: blast_or_smash(state))
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.HF_FAIRY_GROTTO], 
                    lambda state: blast_or_smash(state))
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.HF_NEAR_KAK_GROTTO], 
                    lambda state: can_open_bomb_grotto(state))
    connect_entrance(regions[OOTRegions.HYRULE_FIELD], regions[OOTRegions.HF_TEKTITE_GROTTO], 
                    lambda state: can_open_bomb_grotto(state))
    
    # Cow grotto internal connection
    connect_entrance(regions[OOTRegions.HF_COW_GROTTO], regions[OOTRegions.HF_COW_GROTTO_BEHIND_WEBS], 
                    lambda state: has_fire_source(state))
    
    # Return connections from all grottos
    grotto_regions = [
        OOTRegions.HF_SOUTHEAST_GROTTO, OOTRegions.HF_OPEN_GROTTO, OOTRegions.HF_INSIDE_FENCE_GROTTO,
        OOTRegions.HF_COW_GROTTO, OOTRegions.HF_NEAR_MARKET_GROTTO, OOTRegions.HF_FAIRY_GROTTO,
        OOTRegions.HF_NEAR_KAK_GROTTO, OOTRegions.HF_TEKTITE_GROTTO
    ]
    
    for grotto in grotto_regions:
        connect_entrance(regions[grotto], regions[OOTRegions.HYRULE_FIELD], lambda state: True)
    
    # Special return for cow grotto behind webs
    connect_entrance(regions[OOTRegions.HF_COW_GROTTO_BEHIND_WEBS], regions[OOTRegions.HF_COW_GROTTO], lambda state: True)

def set_hyrule_field_rules(regions: Dict[str, Region], logic: "OOTLogic") -> None:
    """Set access rules for all Hyrule Field locations."""
    
    # Main Hyrule Field rules
    set_hyrule_field_main_rules(regions[OOTRegions.HYRULE_FIELD], logic)
    
    # Grotto rules
    set_hyrule_field_grotto_rules(regions, logic)

def set_hyrule_field_main_rules(region: Region, logic: "OOTLogic") -> None:
    """Set access rules for main Hyrule Field region."""
    
    # Ocarina of Time item - child with all 3 stones and bronze scale
    set_rule(region.locations[OOTLocations.HF_OCARINA_OF_TIME_ITEM], 
             lambda state: (is_child(state) and 
                           stone_count(state) == 3 and 
                           has_item(state, "Bronze Scale")))
    
    # Song from Ocarina of Time - same requirements
    set_rule(region.locations[OOTLocations.SONG_FROM_OCARINA_OF_TIME], 
             lambda state: (is_child(state) and 
                           stone_count(state) == 3 and 
                           has_item(state, "Bronze Scale")))
    
    # Pond storms fairy
    set_rule(region.locations[OOTLocations.HF_POND_STORMS_FAIRY], 
             lambda state: can_use_song_of_storms(state))
    
    # All grass cutting locations
    grass_rule = lambda state: can_cut_shrubs(state)
    
    grass_locations = []
    for prefix in ["HF_CENTRAL_GRASS", "HF_SOUTH_GRASS", "HF_NEAR_MARKET_GRASS", "HF_NEAR_KF_GRASS"]:
        for i in range(1, 13):
            grass_locations.append(f"{prefix}_{i}")
    
    for grass_location in grass_locations:
        set_rule(region.locations[getattr(OOTLocations, grass_location)], grass_rule)

def set_hyrule_field_grotto_rules(regions: Dict[str, Region], logic: "OOTLogic") -> None:
    """Set access rules for all Hyrule Field grotto locations."""
    
    # Standard grotto rules (similar pattern for southeast, open, near market)
    standard_grottos = [
        (OOTRegions.HF_SOUTHEAST_GROTTO, "HF_SOUTHEAST_GROTTO"),
        (OOTRegions.HF_OPEN_GROTTO, "HF_OPEN_GROTTO"),
        (OOTRegions.HF_NEAR_MARKET_GROTTO, "HF_NEAR_MARKET_GROTTO")
    ]
    
    for region_name, location_prefix in standard_grottos:
        grotto_region = regions[region_name]
        
        # Chest is always accessible
        set_rule(grotto_region.locations[getattr(OOTLocations, f"{location_prefix}_CHEST")], 
                lambda state: True)
        
        # Fish needs bottle
        set_rule(grotto_region.locations[getattr(OOTLocations, f"{location_prefix}_FISH")], 
                lambda state: has_bottle(state))
        
        # Gossip stone fairies
        set_rule(grotto_region.locations[getattr(OOTLocations, f"{location_prefix}_GOSSIP_STONE_FAIRY")], 
                lambda state: can_call_gossip_fairy(state))
        set_rule(grotto_region.locations[getattr(OOTLocations, f"{location_prefix}_GOSSIP_STONE_FAIRY_BIG")], 
                lambda state: can_use_song_of_storms(state))
        
        # Gossip stone always accessible
        set_rule(grotto_region.locations[getattr(OOTLocations, f"{location_prefix}_GOSSIP_STONE")], 
                lambda state: True)
        
        # Beehives
        beehive_rule = lambda state: can_break_lower_beehives(state)
        set_rule(grotto_region.locations[getattr(OOTLocations, f"{location_prefix}_BEEHIVE_LEFT")], beehive_rule)
        set_rule(grotto_region.locations[getattr(OOTLocations, f"{location_prefix}_BEEHIVE_RIGHT")], beehive_rule)
        
        # Grass cutting
        grass_rule = lambda state: can_cut_shrubs(state)
        for i in range(1, 5):
            set_rule(grotto_region.locations[getattr(OOTLocations, f"{location_prefix}_GRASS_{i}")], grass_rule)
    
    # Inside Fence Grotto
    fence_grotto = regions[OOTRegions.HF_INSIDE_FENCE_GROTTO]
    set_rule(fence_grotto.locations[OOTLocations.HF_DEKU_SCRUB_GROTTO], 
             lambda state: can_stun_deku(state))
    set_rule(fence_grotto.locations[OOTLocations.HF_INSIDE_FENCE_GROTTO_BEEHIVE], 
             lambda state: can_break_lower_beehives(state))
    set_rule(fence_grotto.locations[OOTLocations.HF_FENCE_GROTTO_STORMS_FAIRY], 
             lambda state: can_use_song_of_storms(state))
    
    # Cow Grotto Behind Webs
    cow_grotto = regions[OOTRegions.HF_COW_GROTTO_BEHIND_WEBS]
    set_rule(cow_grotto.locations[OOTLocations.HF_GS_COW_GROTTO], 
             lambda state: can_get_enemy_drop(state, "Gold Skulltula", "Boomerang"))
    set_rule(cow_grotto.locations[OOTLocations.HF_COW_GROTTO_COW], 
             lambda state: can_use_eponas_song(state))
    set_rule(cow_grotto.locations[OOTLocations.HF_COW_GROTTO_GOSSIP_STONE_FAIRY], 
             lambda state: can_call_gossip_fairy(state))
    set_rule(cow_grotto.locations[OOTLocations.HF_COW_GROTTO_GOSSIP_STONE_FAIRY_BIG], 
             lambda state: can_use_song_of_storms(state))
    set_rule(cow_grotto.locations[OOTLocations.HF_COW_GROTTO_GOSSIP_STONE], 
             lambda state: True)
    
    pot_rule = lambda state: can_break_pots(state)
    set_rule(cow_grotto.locations[OOTLocations.HF_COW_GROTTO_POT_1], pot_rule)
    set_rule(cow_grotto.locations[OOTLocations.HF_COW_GROTTO_POT_2], pot_rule)
    
    grass_rule = lambda state: can_cut_shrubs(state)
    set_rule(cow_grotto.locations[OOTLocations.HF_COW_GROTTO_GRASS_1], grass_rule)
    set_rule(cow_grotto.locations[OOTLocations.HF_COW_GROTTO_GRASS_2], grass_rule)
    
    # Fairy Grotto - all fairies are free
    fairy_grotto = regions[OOTRegions.HF_FAIRY_GROTTO]
    for i in range(1, 9):
        set_rule(fairy_grotto.locations[getattr(OOTLocations, f"HF_FAIRY_GROTTO_FAIRY_{i}")], 
                lambda state: True)
    
    # Near Kak Grotto
    kak_grotto = regions[OOTRegions.HF_NEAR_KAK_GROTTO]
    set_rule(kak_grotto.locations[OOTLocations.HF_GS_NEAR_KAK_GROTTO], 
             lambda state: hookshot_or_boomerang(state))
    
    # Tektite Grotto
    tektite_grotto = regions[OOTRegions.HF_TEKTITE_GROTTO]
    set_rule(tektite_grotto.locations[OOTLocations.HF_TEKTITE_GROTTO_FREESTANDING_POH], 
             lambda state: (has_item(state, "Golden Scale") or 
                           has_item(state, "Iron Boots")))

# Additional helper functions for Hyrule Field
def stone_count(state: CollectionState) -> int:
    """Count spiritual stones."""
    count = 0
    if has_item(state, "Kokiri Emerald"): count += 1
    if has_item(state, "Goron Ruby"): count += 1
    if has_item(state, "Zora Sapphire"): count += 1
    return count

def has_fire_source(state: CollectionState) -> bool:
    """Check if player has fire source."""
    return (has_item(state, "Din's Fire") or 
            has_item(state, "Fire Arrows") or 
            (has_item(state, "Deku Stick") and has_item(state, "Torch")))

def can_get_enemy_drop(state: CollectionState, enemy: str, drop_method: str) -> bool:
    """Check if player can get specific enemy drop."""
    if drop_method == "Boomerang":
        return has_item(state, "Boomerang")
    return can_attack(state)
