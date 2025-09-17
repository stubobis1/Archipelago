"""
Overworld module for Ocarina of Time Ship of Harkinian randomizer.

This module contains all overworld area implementations including:
- Kokiri Forest and surrounding areas
- Lost Woods and Sacred Forest Meadow
- Hyrule Field and all its grottos
- Market and Castle areas
- Kakariko Village and Graveyard
- Death Mountain areas
- Zora areas and Lake Hylia
- Gerudo areas and Desert Colossus
- Lon Lon Ranch

Each area module follows the same pattern:
1. create_regions() - Creates all regions for the area
2. set_*_entrances() - Sets up entrance connections
3. set_*_rules() - Sets access rules for all locations
"""

from typing import Dict
from BaseClasses import Region
from . import kokiri_forest, lost_woods, sacred_forest_meadow, hyrule_field

def create_all_overworld_regions(multiworld, player: int, logic: "OOTLogic") -> Dict[str, Region]:
    """
    Create all overworld regions and return them as a dictionary.
    
    Args:
        multiworld: The multiworld instance
        player: The player number
        logic: The OOT logic instance
        
    Returns:
        Dictionary mapping region names to Region objects
    """
    regions = {}
    
    # Kokiri Forest area
    regions.update(kokiri_forest.create_regions(multiworld, player, logic))
    
    # Lost Woods area
    regions.update(lost_woods.create_regions(multiworld, player, logic))
    
    # Sacred Forest Meadow area
    regions.update(sacred_forest_meadow.create_regions(multiworld, player, logic))
    
    # Hyrule Field area
    regions.update(hyrule_field.create_regions(multiworld, player, logic))
    
    # TODO: Add remaining overworld areas:
    # - Market and Castle areas
    # - Kakariko Village and Graveyard
    # - Death Mountain areas (Trail, Crater, Goron City)
    # - Zora areas (River, Domain, Fountain)
    # - Lake Hylia
    # - Gerudo areas (Valley, Fortress, Training Ground)
    # - Desert Colossus
    # - Lon Lon Ranch
    
    return regions

def set_all_overworld_entrances(regions: Dict[str, Region], entrances_map: Dict[str, str]) -> None:
    """
    Set up all entrance connections between overworld regions.
    
    Args:
        regions: Dictionary of all regions
        entrances_map: Mapping of entrance randomization
    """
    # Set up entrances for each area
    kokiri_forest.set_kokiri_forest_entrances(regions, entrances_map)
    lost_woods.set_lost_woods_entrances(regions, entrances_map)
    sacred_forest_meadow.set_sacred_forest_meadow_entrances(regions, entrances_map)
    hyrule_field.set_hyrule_field_entrances(regions, entrances_map)
    
    # TODO: Add remaining area entrances

def set_all_overworld_rules(regions: Dict[str, Region], logic: "OOTLogic") -> None:
    """
    Set access rules for all overworld locations.
    
    Args:
        regions: Dictionary of all regions
        logic: The OOT logic instance
    """
    # Set rules for each area
    kokiri_forest.set_kokiri_forest_rules(regions, logic)
    lost_woods.set_lost_woods_rules(regions, logic)
    sacred_forest_meadow.set_sacred_forest_meadow_rules(regions, logic)
    hyrule_field.set_hyrule_field_rules(regions, logic)
    
    # TODO: Add remaining area rules

# Export the main functions that will be called from the main world implementation
__all__ = [
    'create_all_overworld_regions',
    'set_all_overworld_entrances', 
    'set_all_overworld_rules'
]
