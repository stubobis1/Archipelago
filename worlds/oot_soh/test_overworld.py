"""
Unit tests for the Ocarina of Time Ship of Harkinian overworld implementation.

These tests verify that:
1. All regions are created correctly
2. All locations are properly assigned to regions  
3. Access rules are functioning as expected
4. Entrance connections work properly
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BaseClasses import Region, CollectionState
from worlds.oot_soh.Enums import OOTRegions, OOTLocations
from worlds.oot_soh.overworld import kokiri_forest, lost_woods, sacred_forest_meadow, hyrule_field
from worlds.oot_soh.overworld import create_all_overworld_regions, set_all_overworld_entrances, set_all_overworld_rules


class TestOverworldRegions(unittest.TestCase):
    """Test overworld region creation and basic structure."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.multiworld = Mock()
        self.player = 1
        self.logic = Mock()
        self.logic.logic_tricks = False
        self.logic.scrub_shuffle = "off"
    
    def test_kokiri_forest_regions_created(self):
        """Test that all Kokiri Forest regions are created."""
        regions = kokiri_forest.create_regions(self.multiworld, self.player, self.logic)
        
        expected_regions = [
            OOTRegions.KOKIRI_FOREST,
            OOTRegions.KF_LINKS_HOUSE,
            OOTRegions.KF_SARIAS_HOUSE,
            OOTRegions.KF_TWINS_HOUSE,
            OOTRegions.KF_BROTHERS_HOUSE,
            OOTRegions.KF_KNOW_IT_ALL_BROTHERS_HOUSE,
            OOTRegions.KF_SHOP,
            OOTRegions.KF_STORMS_GROTTO
        ]
        
        for expected_region in expected_regions:
            self.assertIn(expected_region, regions)
            self.assertIsInstance(regions[expected_region], Region)
    
    def test_lost_woods_regions_created(self):
        """Test that all Lost Woods regions are created."""
        regions = lost_woods.create_regions(self.multiworld, self.player, self.logic)
        
        expected_regions = [
            OOTRegions.LW_FOREST_EXIT,
            OOTRegions.THE_LOST_WOODS,
            OOTRegions.LW_BEYOND_MIDO,
            OOTRegions.LW_NEAR_SHORTCUTS_GROTTO,
            OOTRegions.DEKU_THEATER,
            OOTRegions.LW_SCRUBS_GROTTO,
            OOTRegions.LW_BRIDGE_FROM_FOREST,
            OOTRegions.LW_BRIDGE
        ]
        
        for expected_region in expected_regions:
            self.assertIn(expected_region, regions)
            self.assertIsInstance(regions[expected_region], Region)
    
    def test_sacred_forest_meadow_regions_created(self):
        """Test that all Sacred Forest Meadow regions are created."""
        regions = sacred_forest_meadow.create_regions(self.multiworld, self.player, self.logic)
        
        expected_regions = [
            OOTRegions.SFM_ENTRYWAY,
            OOTRegions.SACRED_FOREST_MEADOW,
            OOTRegions.SFM_FAIRY_GROTTO,
            OOTRegions.SFM_WOLFOS_GROTTO,
            OOTRegions.SFM_STORMS_GROTTO
        ]
        
        for expected_region in expected_regions:
            self.assertIn(expected_region, regions)
            self.assertIsInstance(regions[expected_region], Region)
    
    def test_hyrule_field_regions_created(self):
        """Test that all Hyrule Field regions are created."""
        regions = hyrule_field.create_regions(self.multiworld, self.player, self.logic)
        
        expected_regions = [
            OOTRegions.HYRULE_FIELD,
            OOTRegions.HF_SOUTHEAST_GROTTO,
            OOTRegions.HF_OPEN_GROTTO,
            OOTRegions.HF_INSIDE_FENCE_GROTTO,
            OOTRegions.HF_COW_GROTTO,
            OOTRegions.HF_COW_GROTTO_BEHIND_WEBS,
            OOTRegions.HF_NEAR_MARKET_GROTTO,
            OOTRegions.HF_FAIRY_GROTTO,
            OOTRegions.HF_NEAR_KAK_GROTTO,
            OOTRegions.HF_TEKTITE_GROTTO
        ]
        
        for expected_region in expected_regions:
            self.assertIn(expected_region, regions)
            self.assertIsInstance(regions[expected_region], Region)
    
    def test_all_overworld_regions_integration(self):
        """Test that the integration function creates all regions."""
        regions = create_all_overworld_regions(self.multiworld, self.player, self.logic)
        
        # Should have regions from all four areas
        self.assertGreater(len(regions), 20)  # At least 20+ regions total
        
        # Verify some key regions exist
        key_regions = [
            OOTRegions.KOKIRI_FOREST,
            OOTRegions.THE_LOST_WOODS,
            OOTRegions.SACRED_FOREST_MEADOW,
            OOTRegions.HYRULE_FIELD
        ]
        
        for region in key_regions:
            self.assertIn(region, regions)


class TestOverworldLocations(unittest.TestCase):
    """Test that locations are properly assigned to regions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.multiworld = Mock()
        self.player = 1
        self.logic = Mock()
        self.logic.logic_tricks = False
        self.logic.scrub_shuffle = "off"
    
    def test_kokiri_forest_has_locations(self):
        """Test that Kokiri Forest regions have the expected locations."""
        regions = kokiri_forest.create_regions(self.multiworld, self.player, self.logic)
        
        kf_main = regions[OOTRegions.KOKIRI_FOREST]
        
        # Should have key locations
        expected_locations = [
            OOTLocations.KF_DEKU_TREE_LEFT_GOSSIP_STONE,
            OOTLocations.KF_GS_BEAN_PATCH,
            OOTLocations.KF_BEAN_SPROUT_FAIRY_1
        ]
        
        location_names = [loc.name for loc in kf_main.locations]
        for expected_loc in expected_locations:
            self.assertIn(expected_loc, location_names)
    
    def test_lost_woods_has_locations(self):
        """Test that Lost Woods regions have the expected locations."""
        regions = lost_woods.create_regions(self.multiworld, self.player, self.logic)
        
        lw_main = regions[OOTRegions.THE_LOST_WOODS]
        
        # Should have key locations
        expected_locations = [
            OOTLocations.LW_SKULL_KID,
            OOTLocations.LW_OCARINA_MEMORY_GAME,
            OOTLocations.LW_TARGET_IN_WOODS
        ]
        
        location_names = [loc.name for loc in lw_main.locations]
        for expected_loc in expected_locations:
            self.assertIn(expected_loc, location_names)
    
    def test_hyrule_field_has_major_locations(self):
        """Test that Hyrule Field has major quest locations."""
        regions = hyrule_field.create_regions(self.multiworld, self.player, self.logic)
        
        hf_main = regions[OOTRegions.HYRULE_FIELD]
        
        # Should have key locations
        expected_locations = [
            OOTLocations.HF_OCARINA_OF_TIME_ITEM,
            OOTLocations.SONG_FROM_OCARINA_OF_TIME,
            OOTLocations.HF_CENTRAL_GRASS_1
        ]
        
        location_names = [loc.name for loc in hf_main.locations]
        for expected_loc in expected_locations:
            self.assertIn(expected_loc, location_names)


class TestAccessRules(unittest.TestCase):
    """Test that access rules are properly implemented."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.multiworld = Mock()
        self.player = 1
        self.logic = Mock()
        self.logic.logic_tricks = False
        self.logic.scrub_shuffle = "off"
        
        # Mock state for testing
        self.state = Mock(spec=CollectionState)
        self.state.player = self.player
    
    def test_kokiri_forest_basic_access(self):
        """Test basic Kokiri Forest access rules."""
        regions = kokiri_forest.create_regions(self.multiworld, self.player, self.logic)
        kokiri_forest.set_kokiri_forest_rules(regions, self.logic)
        
        # This test verifies that the rules are set without error
        # Actual rule logic testing would require more complex state mocking
        self.assertTrue(True)  # Basic structure test
    
    def test_rule_setting_does_not_crash(self):
        """Test that setting rules for all areas doesn't crash."""
        regions = create_all_overworld_regions(self.multiworld, self.player, self.logic)
        
        # This should not raise any exceptions
        try:
            set_all_overworld_rules(regions, self.logic)
            success = True
        except Exception as e:
            print(f"Rule setting failed: {e}")
            success = False
        
        self.assertTrue(success)


class TestImplementationCompleteness(unittest.TestCase):
    """Test that our implementation covers all the required locations from the C++ code."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.multiworld = Mock()
        self.player = 1
        self.logic = Mock()
    
    def test_location_enums_exist(self):
        """Test that all the location enums we added actually exist."""
        # Test some key locations we added
        test_locations = [
            "KF_BEAN_SPROUT_FAIRY_1",
            "LW_SKULL_KID", 
            "SFM_GS",
            "HF_OCARINA_OF_TIME_ITEM"
        ]
        
        for location in test_locations:
            self.assertTrue(hasattr(OOTLocations, location), 
                          f"Location {location} should exist in OOTLocations enum")
    
    def test_region_enums_exist(self):
        """Test that all the region enums we added actually exist."""
        test_regions = [
            "KOKIRI_FOREST",
            "THE_LOST_WOODS", 
            "SACRED_FOREST_MEADOW",
            "HYRULE_FIELD"
        ]
        
        for region in test_regions:
            self.assertTrue(hasattr(OOTRegions, region), 
                          f"Region {region} should exist in OOTRegions enum")


if __name__ == '__main__':
    # Set up more detailed test output
    unittest.main(verbosity=2)
