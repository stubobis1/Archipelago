from typing import Dict, List
from BaseClasses import Region, CollectionState
from ..Enums import Items
from ..Rules import *

def create_regions(multiworld, player: int, logic: "OOTLogic") -> Dict[str, Region]:
    """Create all Kokiri Forest regions and their access rules."""
    regions = {}

    # Main Kokiri Forest region
    regions[OOTRegions.KOKIRI_FOREST] = create_kf_main(multiworld, player, logic)
    
    # KF Houses region
    regions[OOTRegions.KF_LINKS_HOUSE] = create_kf_links_house(multiworld, player, logic)
    regions[OOTRegions.KF_SARIAS_HOUSE] = create_kf_sarias_house(multiworld, player, logic)
    regions[OOTRegions.KF_HOUSE_OF_TWINS] = create_kf_twins_house(multiworld, player, logic)
    regions[OOTRegions.KF_BROTHERS_HOUSE] = create_kf_brothers_house(multiworld, player, logic)
    
    # KF Know It All Brothers House region
    regions[OOTRegions.KF_KNOW_IT_ALL_HOUSE] = create_kf_know_it_all_brothers_house(multiworld, player, logic)
    
    # KF Shop region
    regions[OOTRegions.KF_KOKIRI_SHOP] = create_kf_shop(multiworld, player, logic)
    
    # KF Storms Grotto region
    regions[OOTRegions.KF_STORMS_GROTTO] = create_kf_storms_grotto(multiworld, player, logic)

    return regions

def create_kf_main(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create the main Kokiri Forest region."""
    region = Region("Kokiri Forest", player, multiworld)
    
    # Add the known existing locations first
    region.locations.append(OOTLocations.KF_DEKU_TREE_LEFT_GOSSIP_STONE)
    region.locations.append(OOTLocations.KF_DEKU_TREE_RIGHT_GOSSIP_STONE)
    region.locations.append(OOTLocations.KF_GOSSIP_STONE)
    region.locations.append(OOTLocations.KF_GS_BEAN_PATCH)
    region.locations.append(OOTLocations.KF_GS_KNOW_IT_ALL_HOUSE)
    region.locations.append(OOTLocations.KF_GS_HOUSE_OF_TWINS)
    region.locations.append(OOTLocations.KF_DEKU_SCRUB_GROTTO_LEFT)
    region.locations.append(OOTLocations.KF_DEKU_SCRUB_GROTTO_RIGHT)
    region.locations.append(OOTLocations.KF_DEKU_SCRUB_GROTTO_CENTER)
    
    # Add missing locations that we added to Enums
    region.locations.append(OOTLocations.KF_BEAN_SPROUT_FAIRY_1)
    region.locations.append(OOTLocations.KF_BEAN_SPROUT_FAIRY_2)
    region.locations.append(OOTLocations.KF_BEAN_SPROUT_FAIRY_3)
    region.locations.append(OOTLocations.KFDEKU_TREE_LEFT_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.KFDEKU_TREE_LEFT_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.KFDEKU_TREE_RIGHT_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.KFDEKU_TREE_RIGHT_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.KF_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.KF_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.KF_BRIDGE_RUPEE)
    region.locations.append(OOTLocations.KF_BEHIND_MIDOS_RUPEE)
    region.locations.append(OOTLocations.KF_SOUTH_GRASS_WEST_RUPEE)
    region.locations.append(OOTLocations.KF_SOUTH_GRASS_EAST_RUPEE)
    region.locations.append(OOTLocations.KF_NORTH_GRASS_WEST_RUPEE)
    region.locations.append(OOTLocations.KF_NORTH_GRASS_EAST_RUPEE)
    region.locations.append(OOTLocations.KF_BOULDER_RUPEE_1)
    region.locations.append(OOTLocations.KF_BOULDER_RUPEE_2)
    region.locations.append(OOTLocations.KF_BEAN_RUPEE_1)
    region.locations.append(OOTLocations.KF_BEAN_RUPEE_2)
    region.locations.append(OOTLocations.KF_BEAN_RUPEE_3)
    region.locations.append(OOTLocations.KF_BEAN_RUPEE_4)
    region.locations.append(OOTLocations.KF_BEAN_RUPEE_5)
    region.locations.append(OOTLocations.KF_BEAN_RUPEE_6)
    region.locations.append(OOTLocations.KF_BEAN_RED_RUPEE)
    region.locations.append(OOTLocations.KF_SARIAS_ROOF_WEST_HEART)
    region.locations.append(OOTLocations.KF_SARIAS_ROOF_EAST_HEART)
    region.locations.append(OOTLocations.KF_SARIAS_ROOF_NORTH_HEART)
    
    # Add grass cutting locations
    for i in range(1, 13):
        region.locations.append(getattr(OOTLocations, f"KF_CHILD_GRASS_{i}"))
    for i in range(1, 4):
        region.locations.append(getattr(OOTLocations, f"KF_CHILD_GRASS_MAZE_{i}"))
    for i in range(1, 21):
        region.locations.append(getattr(OOTLocations, f"KF_ADULT_GRASS_{i}"))

    return region

def create_kf_links_house(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create Link's House region."""
    region = Region("KF Links House", player, multiworld)
    
    region.locations.append(OOTLocations.KF_LINKS_HOUSE_COW)
    region.locations.append(OOTLocations.KF_LINKS_HOUSE_POT)
    
    return region

def create_kf_sarias_house(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create Saria's House region."""
    region = Region("KF Sarias House", player, multiworld)
    
    region.locations.append(OOTLocations.KF_SARIAS_TOP_LEFT_HEART)
    region.locations.append(OOTLocations.KF_SARIAS_TOP_RIGHT_HEART)
    region.locations.append(OOTLocations.KF_SARIAS_BOTTOM_LEFT_HEART)
    region.locations.append(OOTLocations.KF_SARIAS_BOTTOM_RIGHT_HEART)
    
    return region

def create_kf_twins_house(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create Twins House region."""
    region = Region("KF Twins House", player, multiworld)
    
    region.locations.append(OOTLocations.KF_TWINS_HOUSE_POT_1)
    region.locations.append(OOTLocations.KF_TWINS_HOUSE_POT_2)
    
    return region

def create_kf_brothers_house(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create Brothers House region."""
    region = Region("KF Brothers House", player, multiworld)
    
    region.locations.append(OOTLocations.KF_BROTHERS_HOUSE_POT_1)
    region.locations.append(OOTLocations.KF_BROTHERS_HOUSE_POT_2)
    
    return region

def create_kf_know_it_all_brothers_house(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create Know It All Brothers House region."""
    region = Region("KF Know It All Brothers House", player, multiworld)
    
    # No specific items in this house based on the C++ code, but it exists as a region
    
    return region

def create_kf_shop(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create KF Shop region."""
    region = Region("KF Shop", player, multiworld)
    
    # Shop items
    for i in range(1, 9):
        region.locations.append(getattr(OOTLocations, f"KF_SHOP_ITEM_{i}"))
    
    return region

def create_kf_storms_grotto(multiworld, player: int, logic: "OOTLogic") -> Region:
    """Create KF Storms Grotto region."""
    region = Region("KF Storms Grotto", player, multiworld)
    
    region.locations.append(OOTLocations.KFSTORMS_GROTTO_FISH)
    region.locations.append(OOTLocations.KFSTORMS_GROTTO_GOSSIP_STONE_FAIRY)
    region.locations.append(OOTLocations.KFSTORMS_GROTTO_GOSSIP_STONE_FAIRY_BIG)
    region.locations.append(OOTLocations.KFSTORMS_GROTTO_BEEHIVE_LEFT)
    region.locations.append(OOTLocations.KFSTORMS_GROTTO_BEEHIVE_RIGHT)
    region.locations.append(OOTLocations.KFSTORMS_GROTTO_GRASS_1)
    region.locations.append(OOTLocations.KFSTORMS_GROTTO_GRASS_2)
    region.locations.append(OOTLocations.KFSTORMS_GROTTO_GRASS_3)
    region.locations.append(OOTLocations.KFSTORMS_GROTTO_GRASS_4)
    
    return region

def set_kokiri_forest_entrances(regions: Dict[str, Region], entrances_map: Dict[str, str]) -> None:
    """Set up entrances between Kokiri Forest regions."""
    
    # Main Kokiri Forest connections
    connect_entrance(regions[OOTRegions.KOKIRI_FOREST], regions[OOTRegions.KF_LINKS_HOUSE], lambda state: True)
    connect_entrance(regions[OOTRegions.KOKIRI_FOREST], regions[OOTRegions.KF_SARIAS_HOUSE], lambda state: True)
    connect_entrance(regions[OOTRegions.KOKIRI_FOREST], regions[OOTRegions.KF_HOUSE_OF_TWINS], lambda state: True)
    connect_entrance(regions[OOTRegions.KOKIRI_FOREST], regions[OOTRegions.KF_BROTHERS_HOUSE], lambda state: True)
    connect_entrance(regions[OOTRegions.KOKIRI_FOREST], regions[OOTRegions.KF_KNOW_IT_ALL_HOUSE], lambda state: True)
    connect_entrance(regions[OOTRegions.KOKIRI_FOREST], regions[OOTRegions.KF_KOKIRI_SHOP], lambda state: True)
    connect_entrance(regions[OOTRegions.KOKIRI_FOREST], regions[OOTRegions.KF_STORMS_GROTTO], lambda state: can_use_song_of_storms(state))
    
    # Connections back to main forest
    connect_entrance(regions[OOTRegions.KF_LINKS_HOUSE], regions[OOTRegions.KOKIRI_FOREST], lambda state: True)
    connect_entrance(regions[OOTRegions.KF_SARIAS_HOUSE], regions[OOTRegions.KOKIRI_FOREST], lambda state: True)
    connect_entrance(regions[OOTRegions.KF_HOUSE_OF_TWINS], regions[OOTRegions.KOKIRI_FOREST], lambda state: True)
    connect_entrance(regions[OOTRegions.KF_BROTHERS_HOUSE], regions[OOTRegions.KOKIRI_FOREST], lambda state: True)
    connect_entrance(regions[OOTRegions.KF_KNOW_IT_ALL_HOUSE], regions[OOTRegions.KOKIRI_FOREST], lambda state: True)
    connect_entrance(regions[OOTRegions.KF_KOKIRI_SHOP], regions[OOTRegions.KOKIRI_FOREST], lambda state: True)
    connect_entrance(regions[OOTRegions.KF_STORMS_GROTTO], regions[OOTRegions.KOKIRI_FOREST], lambda state: True)

def set_kokiri_forest_rules(regions: Dict[str, Region], logic: "OOTLogic") -> None:
    """Set access rules for all Kokiri Forest locations."""
    
    kf_region = regions[OOTRegions.KOKIRI_FOREST]
    
    # Gossip stone interactions
    set_rule(kf_region.locations[OOTLocations.KFDEKU_TREE_LEFT_GOSSIP_STONE_FAIRY], 
             lambda state: can_call_gossip_fairy_except_suns(state, logic))
    set_rule(kf_region.locations[OOTLocations.KFDEKU_TREE_LEFT_GOSSIP_STONE_FAIRY_BIG], 
             lambda state: can_use_song_of_storms(state))
    set_rule(kf_region.locations[OOTLocations.KFDEKU_TREE_RIGHT_GOSSIP_STONE_FAIRY], 
             lambda state: can_call_gossip_fairy_except_suns(state, logic))
    set_rule(kf_region.locations[OOTLocations.KFDEKU_TREE_RIGHT_GOSSIP_STONE_FAIRY_BIG], 
             lambda state: can_use_song_of_storms(state))
    set_rule(kf_region.locations[OOTLocations.KF_GOSSIP_STONE_FAIRY], 
             lambda state: can_call_gossip_fairy_except_suns(state, logic))
    set_rule(kf_region.locations[OOTLocations.KF_GOSSIP_STONE_FAIRY_BIG], 
             lambda state: can_use_song_of_storms(state))
    
    # Bean sprout fairies - need magic bean and song of storms
    bean_sprout_rule = lambda state: (is_child(state) and 
                                     has_item(state, "Magic Bean") and 
                                     can_use_song_of_storms(state))
    set_rule(kf_region.locations[OOTLocations.KF_BEAN_SPROUT_FAIRY_1], bean_sprout_rule)
    set_rule(kf_region.locations[OOTLocations.KF_BEAN_SPROUT_FAIRY_2], bean_sprout_rule)
    set_rule(kf_region.locations[OOTLocations.KF_BEAN_SPROUT_FAIRY_3], bean_sprout_rule)
    
    # Boulder rupees - need to blast or smash
    blast_rule = lambda state: blast_or_smash(state)
    set_rule(kf_region.locations[OOTLocations.KF_BOULDER_RUPEE_1], blast_rule)
    set_rule(kf_region.locations[OOTLocations.KF_BOULDER_RUPEE_2], blast_rule)
    
    # Bean area rupees - need magic bean to access
    bean_rule = lambda state: is_child(state) and has_item(state, "Magic Bean") and can_use_song_of_storms(state)
    for i in range(1, 7):
        set_rule(kf_region.locations[getattr(OOTLocations, f"KF_BEAN_RUPEE_{i}")], bean_rule)
    set_rule(kf_region.locations[OOTLocations.KF_BEAN_RED_RUPEE], bean_rule)
    
    # Saria's roof hearts - need to be adult to access roof
    roof_rule = lambda state: is_adult(state)
    set_rule(kf_region.locations[OOTLocations.KF_SARIAS_ROOF_WEST_HEART], roof_rule)
    set_rule(kf_region.locations[OOTLocations.KF_SARIAS_ROOF_EAST_HEART], roof_rule)
    set_rule(kf_region.locations[OOTLocations.KF_SARIAS_ROOF_NORTH_HEART], roof_rule)
    
    # Grass cutting locations - need ability to cut shrubs
    grass_rule = lambda state: can_cut_shrubs(state)
    for i in range(1, 13):
        set_rule(kf_region.locations[getattr(OOTLocations, f"KF_CHILD_GRASS_{i}")], grass_rule)
    for i in range(1, 4):
        set_rule(kf_region.locations[getattr(OOTLocations, f"KF_CHILD_GRASS_MAZE_{i}")], grass_rule)
    for i in range(1, 21):
        set_rule(kf_region.locations[getattr(OOTLocations, f"KF_ADULT_GRASS_{i}")], grass_rule)
    
    # Gold Skulltula rules
    set_rule(kf_region.locations[OOTLocations.KF_GS_BEAN_PATCH], 
             lambda state: can_spawn_soil_skull(state) and can_attack(state))
    set_rule(kf_region.locations[OOTLocations.KF_GS_KNOW_IT_ALL_HOUSE], 
             lambda state: can_get_night_time_gs(state) and 
                          (is_adult(state) or 
                           (logic.logic_tricks and can_jumpslash(state))))
    set_rule(kf_region.locations[OOTLocations.KF_GS_HOUSE_OF_TWINS], 
             lambda state: can_get_night_time_gs(state) and is_adult(state))
    
    # House access rules
    set_kokiri_forest_house_rules(regions, logic)
    
    # Shop rules
    set_kokiri_forest_shop_rules(regions, logic)
    
    # Storms grotto rules
    set_kokiri_forest_storms_grotto_rules(regions, logic)

def set_kokiri_forest_house_rules(regions: Dict[str, Region], logic: "OOTLogic") -> None:
    """Set access rules for house locations."""
    
    # Link's House - cow needs Epona's Song
    links_house = regions[OOTRegions.KF_LINKS_HOUSE]
    set_rule(links_house.locations[OOTLocations.KF_LINKS_HOUSE_COW], 
             lambda state: can_use_eponas_song(state))
    set_rule(links_house.locations[OOTLocations.KF_LINKS_HOUSE_POT], 
             lambda state: can_break_pots(state))
    
    # Saria's House - heart pieces are always accessible inside the house
    sarias_house = regions[OOTRegions.KF_SARIAS_HOUSE]
    for location in sarias_house.locations:
        set_rule(location, lambda state: True)
    
    # Twins House - pots need ability to break them
    twins_house = regions[OOTRegions.KF_HOUSE_OF_TWINS]
    pot_rule = lambda state: can_break_pots(state)
    set_rule(twins_house.locations[OOTLocations.KF_TWINS_HOUSE_POT_1], pot_rule)
    set_rule(twins_house.locations[OOTLocations.KF_TWINS_HOUSE_POT_2], pot_rule)
    
    # Brothers House - pots need ability to break them
    brothers_house = regions[OOTRegions.KF_BROTHERS_HOUSE]
    set_rule(brothers_house.locations[OOTLocations.KF_BROTHERS_HOUSE_POT_1], pot_rule)
    set_rule(brothers_house.locations[OOTLocations.KF_BROTHERS_HOUSE_POT_2], pot_rule)

def set_kokiri_forest_shop_rules(regions: Dict[str, Region], logic: "OOTLogic") -> None:
    """Set access rules for shop locations."""
    
    shop_region = regions[OOTRegions.KF_KOKIRI_SHOP]
    
    # Shop items are always accessible once inside the shop (wallet restrictions handled elsewhere)
    for location in shop_region.locations:
        set_rule(location, lambda state: True)

def set_kokiri_forest_storms_grotto_rules(regions: Dict[str, Region], logic: "OOTLogic") -> None:
    """Set access rules for Storms Grotto locations."""
    
    grotto_region = regions[OOTRegions.KF_STORMS_GROTTO]
    
    # Fish needs bottle
    set_rule(grotto_region.locations[OOTLocations.KFSTORMS_GROTTO_FISH], 
             lambda state: has_bottle(state))
    
    # Gossip stone fairies
    set_rule(grotto_region.locations[OOTLocations.KFSTORMS_GROTTO_GOSSIP_STONE_FAIRY], 
             lambda state: can_call_gossip_fairy(state))
    set_rule(grotto_region.locations[OOTLocations.KFSTORMS_GROTTO_GOSSIP_STONE_FAIRY_BIG], 
             lambda state: can_use_song_of_storms(state))
    
    # Beehives need ability to break them
    beehive_rule = lambda state: can_break_lower_beehives(state)
    set_rule(grotto_region.locations[OOTLocations.KFSTORMS_GROTTO_BEEHIVE_LEFT], beehive_rule)
    set_rule(grotto_region.locations[OOTLocations.KFSTORMS_GROTTO_BEEHIVE_RIGHT], beehive_rule)
    
    # Grass cutting
    grass_rule = lambda state: can_cut_shrubs(state)
    for i in range(1, 5):
        set_rule(grotto_region.locations[getattr(OOTLocations, f"KFSTORMS_GROTTO_GRASS_{i}")], grass_rule)
