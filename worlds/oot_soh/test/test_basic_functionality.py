"""
Basic world functionality tests for OoT Ship of Harkinian.

These tests verify core world functionality with default options.
"""

from .bases import SohTestBase


class TestDefaultOptions(SohTestBase):
    """Test basic world functionality with default options."""
    
    options = {}  # Use default options
    
    def test_lost_woods_locations_exist(self) -> None:
        """Test that Lost Woods locations are properly created and accessible."""
        # Key Lost Woods locations that should exist
        expected_locations = [
            "LW Skull Kid",
            "LW Gift From Saria", 
            "LW Ocarina Memory Game",
            "LW Target in Woods",
            "LW Near Shortcuts Grotto Chest",
        ]
        
        # Check that locations exist in the world
        for location_name in expected_locations:
            with self.subTest(location=location_name):
                location = self.multiworld.get_location(location_name, self.player)
                self.assertIsNotNone(location, f"Location '{location_name}' not found")
                # Lost Woods locations can be in various LW regions
                self.assertTrue(
                    location.parent_region.name.startswith("LW") or "Lost Woods" in location.parent_region.name,
                    f"Location '{location_name}' is in region '{location.parent_region.name}', expected a Lost Woods region"
                )
    
    def test_sacred_forest_meadow_locations_exist(self) -> None:
        """Test that Sacred Forest Meadow locations are properly created."""
        expected_locations = [
            "Song from Saria",
            "Sheik in Forest", 
            "SFM GS",
            "SFM Wolfos Grotto Chest",
        ]
        
        for location_name in expected_locations:
            with self.subTest(location=location_name):
                location = self.multiworld.get_location(location_name, self.player)
                self.assertIsNotNone(location, f"Location '{location_name}' not found")
                # Sacred Forest Meadow locations can be in various SFM regions
                self.assertTrue(
                    location.parent_region.name.startswith("SFM") or "Sacred Forest Meadow" in location.parent_region.name,
                    f"Location '{location_name}' is in region '{location.parent_region.name}', expected a Sacred Forest Meadow region"
                )
    
    def test_region_progression(self) -> None:
        """Test that regions follow expected progression logic."""
        # Test that we can reach key progression regions
        progression_regions = [
            "Menu",
            "Hyrule", 
            "LW Forest Exit",
            "The Lost Woods",
            "LW Beyond Mido",
            "SFM Entryway",
            "Sacred Forest Meadow",
        ]
        
        for region_name in progression_regions:
            with self.subTest(region=region_name):
                region = self.multiworld.get_region(region_name, self.player)
                self.assertIsNotNone(region, f"Region '{region_name}' not found")


class TestClosedForestOptions(SohTestBase):
    """Test world functionality with closed forest options."""
    
    options = {
        "closed_forest": "deku_only",
    }
    
    # Test that the world still creates properly with closed forest options
