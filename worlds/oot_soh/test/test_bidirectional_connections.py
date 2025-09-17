"""
Tests for bidirectional region connections in OoT Ship of Harkinian.

These tests ensure that all region connections are properly bidirectional,
preventing players from getting stuck due to one-way connections.
"""

import unittest
from typing import Dict, Set, Tuple

from worlds.oot_soh.Regions import region_data_table


class TestBidirectionalConnections(unittest.TestCase):
    """Test that all region connections are bidirectional."""
    
    def test_all_connections_are_bidirectional(self) -> None:
        """Test that every region connection has a corresponding reverse connection."""
        missing_connections = []
        checked_pairs: Set[Tuple[str, str]] = set()
        
        for region_name, region_data in region_data_table.items():
            for connected_region in region_data.connecting_regions:
                # Create a sorted pair to avoid checking the same connection twice
                pair = tuple(sorted([region_name, connected_region]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                
                # Check if connection exists in both directions
                if connected_region in region_data_table:
                    reverse_connections = region_data_table[connected_region].connecting_regions
                    if region_name not in reverse_connections:
                        missing_connections.append(f"{region_name} → {connected_region} (missing reverse)")
                else:
                    missing_connections.append(f"{region_name} → {connected_region} (target not in table)")
        
        self.assertEqual(
            missing_connections, [],
            f"Found {len(missing_connections)} non-bidirectional connections:\n" + 
            "\n".join(missing_connections)
        )
    
    def test_no_self_connections(self) -> None:
        """Test that no region connects to itself."""
        self_connections = []
        
        for region_name, region_data in region_data_table.items():
            if region_name in region_data.connecting_regions:
                self_connections.append(region_name)
        
        self.assertEqual(
            self_connections, [],
            f"Found {len(self_connections)} regions with self-connections: {self_connections}"
        )
    
    def test_all_referenced_regions_exist(self) -> None:
        """Test that all referenced regions in connections actually exist in the table."""
        missing_targets = []
        
        for region_name, region_data in region_data_table.items():
            for connected_region in region_data.connecting_regions:
                if connected_region not in region_data_table:
                    missing_targets.append(f"{region_name} → {connected_region}")
        
        self.assertEqual(
            missing_targets, [],
            f"Found {len(missing_targets)} connections to non-existent regions:\n" + 
            "\n".join(missing_targets)
        )
    
    def test_lost_woods_connections(self) -> None:
        """Test specific Lost Woods region connections."""
        # Test that Lost Woods regions are properly connected
        expected_connections = {
            "LW Forest Exit": {"Hyrule", "The Lost Woods"},
            "The Lost Woods": {"LW Forest Exit", "LW Beyond Mido", "LW Scrubs Grotto"},
            "LW Beyond Mido": {"The Lost Woods", "SFM Entryway"},
            "LW Scrubs Grotto": {"The Lost Woods"},
        }
        
        for region_name, expected_targets in expected_connections.items():
            with self.subTest(region=region_name):
                self.assertIn(region_name, region_data_table, 
                            f"Region {region_name} not found in region table")
                
                actual_targets = set(region_data_table[region_name].connecting_regions)
                self.assertEqual(
                    actual_targets, expected_targets,
                    f"Region {region_name} connections don't match. "
                    f"Expected: {expected_targets}, Got: {actual_targets}"
                )
    
    def test_sacred_forest_meadow_connections(self) -> None:
        """Test specific Sacred Forest Meadow region connections."""
        expected_connections = {
            "SFM Entryway": {"LW Beyond Mido", "Sacred Forest Meadow", "SFM Wolfos Grotto"},
            "Sacred Forest Meadow": {"SFM Entryway", "SFM Fairy Grotto", "SFM Storms Grotto"},
            "SFM Fairy Grotto": {"Sacred Forest Meadow"},
            "SFM Wolfos Grotto": {"SFM Entryway"},
            "SFM Storms Grotto": {"Sacred Forest Meadow"},
        }
        
        for region_name, expected_targets in expected_connections.items():
            with self.subTest(region=region_name):
                self.assertIn(region_name, region_data_table,
                            f"Region {region_name} not found in region table")
                
                actual_targets = set(region_data_table[region_name].connecting_regions)
                self.assertEqual(
                    actual_targets, expected_targets,
                    f"Region {region_name} connections don't match. "
                    f"Expected: {expected_targets}, Got: {actual_targets}"
                )
    
    def test_hyrule_root_connections(self) -> None:
        """Test that the root regions (Menu/Hyrule) are properly connected."""
        # Test Menu → Hyrule bidirectional connection
        self.assertIn("Menu", region_data_table, "Menu region not found")
        self.assertIn("Hyrule", region_data_table, "Hyrule region not found")
        
        menu_connections = region_data_table["Menu"].connecting_regions
        hyrule_connections = region_data_table["Hyrule"].connecting_regions
        
        self.assertIn("Hyrule", menu_connections, "Menu should connect to Hyrule")
        self.assertIn("Menu", hyrule_connections, "Hyrule should connect back to Menu")


class TestRegionReachability(unittest.TestCase):
    """Test that regions can be reached through the connection graph."""
    
    def test_all_regions_reachable_from_menu(self) -> None:
        """Test that all regions can be reached from the Menu region using BFS."""
        if not region_data_table:
            self.skipTest("No regions defined in region_data_table")
        
        # Start from Menu region
        start_region = "Menu"
        if start_region not in region_data_table:
            self.skipTest(f"Start region '{start_region}' not found in region table")
        
        # Breadth-first search from Menu
        visited = set()
        queue = [start_region]
        visited.add(start_region)
        
        while queue:
            current = queue.pop(0)
            for connected_region in region_data_table[current].connecting_regions:
                if connected_region not in visited and connected_region in region_data_table:
                    visited.add(connected_region)
                    queue.append(connected_region)
        
        # Check that all regions are reachable
        all_regions = set(region_data_table.keys())
        unreachable_regions = all_regions - visited
        
        self.assertEqual(
            unreachable_regions, set(),
            f"Found {len(unreachable_regions)} unreachable regions: {unreachable_regions}"
        )
    
    def test_no_isolated_region_groups(self) -> None:
        """Test that there are no isolated groups of regions."""
        if not region_data_table:
            self.skipTest("No regions defined in region_data_table")
        
        all_regions = set(region_data_table.keys())
        visited_global = set()
        isolated_groups = []
        
        for region in all_regions:
            if region in visited_global:
                continue
            
            # Find all regions connected to this one
            visited_local = set()
            queue = [region]
            visited_local.add(region)
            
            while queue:
                current = queue.pop(0)
                for connected_region in region_data_table[current].connecting_regions:
                    if connected_region not in visited_local and connected_region in region_data_table:
                        visited_local.add(connected_region)
                        queue.append(connected_region)
            
            # Add this group to global visited
            visited_global.update(visited_local)
            
            # If this group doesn't contain Menu, it's isolated
            if "Menu" not in visited_local and len(visited_local) > 1:
                isolated_groups.append(sorted(visited_local))
        
        self.assertEqual(
            isolated_groups, [],
            f"Found {len(isolated_groups)} isolated region groups: {isolated_groups}"
        )


if __name__ == '__main__':
    unittest.main()
