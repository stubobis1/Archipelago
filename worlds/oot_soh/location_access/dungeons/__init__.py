"""
Dungeons module for Ocarina of Time Archipelago randomizer.
"""

from .dodongos_cavern import create_regions_and_rules as setup_dodongos_cavern
# from .deku_tree import setup_deku_tree  # Temporarily commented out
# from .bottom_of_the_well import setup_bottom_of_the_well  # Temporarily commented out


def setup_all_dungeons(world: "SohWorld") -> None:
    """Setup all dungeon regions, locations, and rules."""
    setup_dodongos_cavern(world)
    # setup_deku_tree(world)  # Temporarily commented out
    # setup_bottom_of_the_well(world)  # Temporarily commented out


__all__ = [
    "setup_all_dungeons",
    "setup_dodongos_cavern", 
    # "setup_deku_tree",  # Temporarily commented out
    # "setup_bottom_of_the_well"  # Temporarily commented out
]