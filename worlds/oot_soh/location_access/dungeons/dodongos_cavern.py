from typing import TYPE_CHECKING

from BaseClasses import Region
from worlds.generic.Rules import set_rule

from worlds.oot_soh.Items import SohItem
from worlds.oot_soh.Locations import SohLocation, SohLocationData, base_location_table
from worlds.oot_soh.Rules import (can_break_mud_walls, is_adult, has_explosives, can_attack, take_damage, can_shield, can_kill_enemy,
                                  has_fire_source_with_torch, can_use, can_do_trick, can_jump_slash, can_break_pots, can_break_crates,
                                  can_stun_deku, has_projectile, can_hit_eye_targets, has_item)
from worlds.oot_soh.Enums import Regions, Items, Locations

if TYPE_CHECKING:
    from worlds.oot_soh import SohWorld


# when python 3.10 and 3.11 are dropped, this should just become a StrEnum to make it easier
region_names: list[str] = [
    Regions.DODONGOS_CAVERN_BEGINNING,
    Regions.DODONGOS_CAVERN_LOBBY,
    Regions.DODONGOS_CAVERN_LOBBY_SWITCH,
    Regions.DODONGOS_CAVERN_SE_CORRIDOR,
    Regions.DODONGOS_CAVERN_SE_ROOM,
    Regions.DODONGOS_CAVERN_NEAR_LOWER_LIZALFOS,
    Regions.DODONGOS_CAVERN_LOWER_LIZALFOS,
    Regions.DODONGOS_CAVERN_DODONGO_ROOM,
    Regions.DODONGOS_CAVERN_NEAR_DODONGO_ROOM,
    Regions.DODONGOS_CAVERN_STAIRS_LOWER,
    Regions.DODONGOS_CAVERN_STAIRS_UPPER,
    Regions.DODONGOS_CAVERN_COMPASS_ROOM,
    Regions.DODONGOS_CAVERN_ARMOS_ROOM,
    Regions.DODONGOS_CAVERN_BOMB_ROOM_LOWER,
    Regions.DODONGOS_CAVERN_2F_SIDE_ROOM,
    Regions.DODONGOS_CAVERN_FIRST_SLINGSHOT_ROOM,
    Regions.DODONGOS_CAVERN_UPPER_LIZALFOS,
    Regions.DODONGOS_CAVERN_SECOND_SLINGSHOT_ROOM,
    Regions.DODONGOS_CAVERN_BOMB_ROOM_UPPER,
    Regions.DODONGOS_CAVERN_FAR_BRIDGE,
    Regions.DODONGOS_CAVERN_BOSS_REGION,
    Regions.DODONGOS_CAVERN_BACK_ROOM,
    Regions.DODONGOS_CAVERN_BOSS_ENTRYWAY,
]


events: dict[str, SohLocationData] = {
    "Dodongos Cavern Lobby Switch": SohLocationData(Regions.DODONGOS_CAVERN_LOBBY_SWITCH,
                                                    event_item="Dodongos Cavern Lobby Switch Activated"),
    "Dodongos Cavern Far Bridge Switch": SohLocationData(Regions.DODONGOS_CAVERN_FAR_BRIDGE,
                                                         event_item="Dodongos Cavern Far Bridge Switch Activated"),
    "Dodongos Cavern Lower Lizalfos": SohLocationData(Regions.DODONGOS_CAVERN_LOWER_LIZALFOS,
                                                      event_item="Defeated Dodongos Cavern Lower Lizalfos")
}


def create_regions_and_rules(world: "SohWorld") -> None:
    for region_name in region_names:
        region = Region(region_name, world.player, world.multiworld)
        world.multiworld.regions.append(region)
        region.add_locations({loc_name: loc_data.address for loc_name, loc_data in base_location_table.items()
                              if loc_data.region == region_name}, SohLocation)

    for event_name, data in events.items():
        region = world.get_region(data.region)
        region.add_event(event_name, data.event_item, location_type=SohLocation, item_type=SohItem)

    set_region_rules(world)
    set_location_rules(world)


# I'm writing this with events in mind, even though the original for this dungeon doesn't use them
# Probably will be easier that way
def set_region_rules(world: "SohWorld") -> None:
    player = world.player

    world.get_region(Regions.DODONGOS_CAVERN_ENTRYWAY).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BEGINNING))

    world.get_region(Regions.DODONGOS_CAVERN_BEGINNING).connect(
        world.get_region(Regions.DODONGOS_CAVERN_ENTRYWAY))

    world.get_region(Regions.DODONGOS_CAVERN_BEGINNING).connect(
        world.get_region(Regions.DODONGOS_CAVERN_LOBBY),
        rule=lambda state: can_break_mud_walls(state, world)
        or state.has(Items.STRENGTH_UPGRADE, player))

    world.get_region(Regions.DODONGOS_CAVERN_LOBBY).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BEGINNING))

    world.get_region(Regions.DODONGOS_CAVERN_LOBBY).connect(
        world.get_region(Regions.DODONGOS_CAVERN_LOBBY_SWITCH),
        rule=lambda state: is_adult(state, world))

    world.get_region(Regions.DODONGOS_CAVERN_LOBBY).connect(
        world.get_region(Regions.DODONGOS_CAVERN_SE_CORRIDOR),
        rule=lambda state: can_break_mud_walls(state, world)
        or state.has(Items.STRENGTH_UPGRADE, player))

    world.get_region(Regions.DODONGOS_CAVERN_LOBBY).connect(
        world.get_region(Regions.DODONGOS_CAVERN_STAIRS_LOWER),
        rule=lambda state: state.has("Dodongos Cavern Lobby Switch Activated", player))

    world.get_region(Regions.DODONGOS_CAVERN_LOBBY).connect(
        world.get_region(Regions.DODONGOS_CAVERN_FAR_BRIDGE),
        rule=lambda state: state.has("Dodongos Cavern Far Bridge Switch Activated", player))

    world.get_region(Regions.DODONGOS_CAVERN_LOBBY).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BOSS_REGION),
        rule=lambda state: state.has("Dodongos Cavern Far Bridge Switch Activated", player)
        and has_explosives(state, world))

    world.get_region(Regions.DODONGOS_CAVERN_LOBBY_SWITCH).connect(
        world.get_region(Regions.DODONGOS_CAVERN_LOBBY))

    world.get_region(Regions.DODONGOS_CAVERN_LOBBY_SWITCH).connect(
        world.get_region(Regions.DODONGOS_CAVERN_DODONGO_ROOM))

    world.get_region(Regions.DODONGOS_CAVERN_SE_CORRIDOR).connect(
        world.get_region(Regions.DODONGOS_CAVERN_LOBBY))

    world.get_region(Regions.DODONGOS_CAVERN_SE_CORRIDOR).connect(
        world.get_region(Regions.DODONGOS_CAVERN_SE_ROOM),
        rule=lambda state: can_break_mud_walls(state, world)
        or can_attack(state, world)
        or (take_damage(state, world) and can_shield(state, world)))

    world.get_region(Regions.DODONGOS_CAVERN_SE_CORRIDOR).connect(
        world.get_region(Regions.DODONGOS_CAVERN_NEAR_LOWER_LIZALFOS))

    world.get_region(Regions.DODONGOS_CAVERN_SE_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_SE_CORRIDOR))

    world.get_region(Regions.DODONGOS_CAVERN_NEAR_LOWER_LIZALFOS).connect(
        world.get_region(Regions.DODONGOS_CAVERN_SE_CORRIDOR))

    world.get_region(Regions.DODONGOS_CAVERN_NEAR_LOWER_LIZALFOS).connect(
        world.get_region(Regions.DODONGOS_CAVERN_LOWER_LIZALFOS))

    world.get_region(Regions.DODONGOS_CAVERN_LOWER_LIZALFOS).connect(
        world.get_region(Regions.DODONGOS_CAVERN_NEAR_LOWER_LIZALFOS),
        rule=lambda state: can_kill_enemy(state, world, "Lizalfos", 0, quantity=2))

    world.get_region(Regions.DODONGOS_CAVERN_LOWER_LIZALFOS).connect(
        world.get_region(Regions.DODONGOS_CAVERN_DODONGO_ROOM),
        rule=lambda state: can_kill_enemy(state, world, "Lizalfos", 0, quantity=2))

    world.get_region(Regions.DODONGOS_CAVERN_DODONGO_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_LOBBY_SWITCH),
        rule=lambda state: has_fire_source_with_torch(state, world))

    world.get_region(Regions.DODONGOS_CAVERN_DODONGO_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_LOWER_LIZALFOS))

    world.get_region(Regions.DODONGOS_CAVERN_DODONGO_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_NEAR_DODONGO_ROOM),
        rule=lambda state: can_break_mud_walls(state, world)
        or state.has(Items.STRENGTH_UPGRADE, player))

    world.get_region(Regions.DODONGOS_CAVERN_NEAR_DODONGO_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_DODONGO_ROOM))

    world.get_region(Regions.DODONGOS_CAVERN_STAIRS_LOWER).connect(
        world.get_region(Regions.DODONGOS_CAVERN_LOBBY))

    world.get_region(Regions.DODONGOS_CAVERN_STAIRS_LOWER).connect(
        world.get_region(Regions.DODONGOS_CAVERN_STAIRS_UPPER),
        rule=lambda state: has_explosives(state, world)
        or state.has(Items.STRENGTH_UPGRADE, player)
        or can_use(Items.DINS_FIRE, state, world)
        or (can_do_trick("DC Stairs With Bow", state, world) and can_use(Items.FAIRY_BOW, state, world)))

    world.get_region(Regions.DODONGOS_CAVERN_STAIRS_LOWER).connect(
        world.get_region(Regions.DODONGOS_CAVERN_COMPASS_ROOM),
        rule=lambda state: can_break_mud_walls(state, world)
        or state.has(Items.STRENGTH_UPGRADE, player))

    world.get_region(Regions.DODONGOS_CAVERN_STAIRS_UPPER).connect(
        world.get_region(Regions.DODONGOS_CAVERN_STAIRS_LOWER))

    world.get_region(Regions.DODONGOS_CAVERN_STAIRS_UPPER).connect(
        world.get_region(Regions.DODONGOS_CAVERN_ARMOS_ROOM))

    world.get_region(Regions.DODONGOS_CAVERN_COMPASS_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_STAIRS_LOWER),
        rule=lambda state: can_use(Items.MASTER_SWORD, state, world)
        or can_use(Items.BIGGORONS_SWORD, state, world)
        or can_use(Items.MEGATON_HAMMER, state, world)
        or has_explosives(state, world)
        or state.has(Items.STRENGTH_UPGRADE, player))

    world.get_region(Regions.DODONGOS_CAVERN_ARMOS_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_STAIRS_UPPER))

    world.get_region(Regions.DODONGOS_CAVERN_ARMOS_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_LOWER))

    world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_LOWER).connect(
        world.get_region(Regions.DODONGOS_CAVERN_ARMOS_ROOM))

    world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_LOWER).connect(
        world.get_region(Regions.DODONGOS_CAVERN_2F_SIDE_ROOM),
        rule=lambda state: can_break_mud_walls(state, world)
        or (can_do_trick("DC Scrub Room", state, world) and state.has(Items.STRENGTH_UPGRADE, player)))

    world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_LOWER).connect(
        world.get_region(Regions.DODONGOS_CAVERN_FIRST_SLINGSHOT_ROOM),
        rule=lambda state: can_break_mud_walls(state, world)
        or state.has(Items.STRENGTH_UPGRADE, player))

    world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_LOWER).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_UPPER),
        rule=lambda state: (is_adult(state, world) and can_do_trick("DC Jump", state, world))
        or can_use(Items.HOVER_BOOTS, state, world)
        or (is_adult(state, world) and can_use(Items.LONGSHOT, state, world))
        or (can_do_trick("Damage Boost Simple", state, world) and has_explosives(state, world)
            and can_jump_slash(state, world)))

    world.get_region(Regions.DODONGOS_CAVERN_2F_SIDE_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_LOWER))

    world.get_region(Regions.DODONGOS_CAVERN_FIRST_SLINGSHOT_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_LOWER))

    world.get_region(Regions.DODONGOS_CAVERN_FIRST_SLINGSHOT_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_UPPER_LIZALFOS),
        rule=lambda state: can_hit_eye_targets(state, world))

    world.get_region(Regions.DODONGOS_CAVERN_UPPER_LIZALFOS).connect(
        world.get_region(Regions.DODONGOS_CAVERN_LOWER_LIZALFOS))

    world.get_region(Regions.DODONGOS_CAVERN_UPPER_LIZALFOS).connect(
        world.get_region(Regions.DODONGOS_CAVERN_FIRST_SLINGSHOT_ROOM),
        rule=lambda state: state.has("Defeated Dodongos Cavern Lower Lizalfos", player))

    world.get_region(Regions.DODONGOS_CAVERN_UPPER_LIZALFOS).connect(
        world.get_region(Regions.DODONGOS_CAVERN_SECOND_SLINGSHOT_ROOM),
        rule=lambda state: state.has("Defeated Dodongos Cavern Lower Lizalfos", player))

    world.get_region(Regions.DODONGOS_CAVERN_SECOND_SLINGSHOT_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_UPPER_LIZALFOS))

    world.get_region(Regions.DODONGOS_CAVERN_SECOND_SLINGSHOT_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_UPPER),
        rule=lambda state: can_hit_eye_targets(state, world))

    world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_UPPER).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_LOWER))

    world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_UPPER).connect(
        world.get_region(Regions.DODONGOS_CAVERN_SECOND_SLINGSHOT_ROOM))

    world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_UPPER).connect(
        world.get_region(Regions.DODONGOS_CAVERN_FAR_BRIDGE))

    world.get_region(Regions.DODONGOS_CAVERN_FAR_BRIDGE).connect(
        world.get_region(Regions.DODONGOS_CAVERN_LOBBY))

    world.get_region(Regions.DODONGOS_CAVERN_FAR_BRIDGE).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BOMB_ROOM_UPPER))

    world.get_region(Regions.DODONGOS_CAVERN_BOSS_REGION).connect(
        world.get_region(Regions.DODONGOS_CAVERN_LOBBY))

    world.get_region(Regions.DODONGOS_CAVERN_BOSS_REGION).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BACK_ROOM),
        rule=lambda state: can_break_mud_walls(state, world))

    world.get_region(Regions.DODONGOS_CAVERN_BOSS_REGION).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BOSS_ENTRYWAY))

    world.get_region(Regions.DODONGOS_CAVERN_BACK_ROOM).connect(
        world.get_region(Regions.DODONGOS_CAVERN_BOSS_REGION))


def set_location_rules(world: "SohWorld") -> None:
    player = world.player

    # Lobby locations
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_MAP_CHEST),
             rule=lambda state: can_break_mud_walls(state, world)
             or state.has(Items.STRENGTH_UPGRADE, player))

    set_rule(world.get_location(Locations.DODONGOS_CAVERN_DEKU_SCRUB_LOBBY),
             rule=lambda state: can_stun_deku(state, world)
             or state.has(Items.STRENGTH_UPGRADE, player))

    # SE Corridor and SE Room locations  
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_GS_SCARECROW),
             rule=lambda state: can_use(Items.SCARECROWS_SONG, state, world)
             or (is_adult(state, world) and can_use(Items.LONGSHOT, state, world))
             or (can_do_trick("DC Scarecrow GS", state, world) and can_attack(state, world)))

    set_rule(world.get_location(Locations.DODONGOS_CAVERN_SIDE_ROOM_POT1),
             rule=lambda state: can_break_pots(state, world))
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_SIDE_ROOM_POT2),
             rule=lambda state: can_break_pots(state, world))
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_SIDE_ROOM_POT3),
             rule=lambda state: can_break_pots(state, world))
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_SIDE_ROOM_POT4),
             rule=lambda state: can_break_pots(state, world))
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_SIDE_ROOM_POT5),
             rule=lambda state: can_break_pots(state, world))
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_SIDE_ROOM_POT6),
             rule=lambda state: can_break_pots(state, world))

    set_rule(world.get_location(Locations.DODONGOS_CAVERN_GSSIDE_ROOM_NEAR_LOWER_LIZALFOS),
             rule=lambda state: can_attack(state, world))

    # Lower Lizalfos locations
    set_rule(world.get_location("Dodongos Cavern Lower Lizalfos"),
             rule=lambda state: can_kill_enemy(state, world, "Lizalfos", 0, quantity=2))

    set_rule(world.get_location(Locations.DODONGOS_CAVERN_LIZALFOS_POT1),
             rule=lambda state: can_break_pots(state, world))
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_LIZALFOS_POT2),
             rule=lambda state: can_break_pots(state, world))
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_LIZALFOS_POT3),
             rule=lambda state: can_break_pots(state, world))
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_LIZALFOS_POT4),
             rule=lambda state: can_break_pots(state, world))

    # Dodongo Room (torch room) locations
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_TORCH_ROOM_POT1),
             rule=lambda state: can_break_pots(state, world))
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_TORCH_ROOM_POT2),
             rule=lambda state: can_break_pots(state, world))
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_TORCH_ROOM_POT3),
             rule=lambda state: can_break_pots(state, world))
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_TORCH_ROOM_POT4),
             rule=lambda state: can_break_pots(state, world))

    # Near Dodongo Room
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_DEKU_SCRUB_SIDE_ROOM_NEAR_DODONGOS),
             rule=lambda state: can_stun_deku(state, world))

    # Stairs Upper locations
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_GSALCOVE_ABOVE_STAIRS),
             rule=lambda state: can_reach_from_far_bridge(state, world)
             or can_use(Items.LONGSHOT, state, world))

    set_rule(world.get_location(Locations.DODONGOS_CAVERN_GSVINES_ABOVE_STAIRS),
             rule=lambda state: is_adult(state, world)
             or can_attack(state, world)
             or (can_use(Items.LONGSHOT, state, world) and can_do_trick("DC Vines GS", state, world)))

    # Compass Room
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_COMPASS_CHEST),
             rule=lambda state: True)  # No additional requirements once in room

    # Bomb Room Lower locations
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_BOMB_FLOWER_PLATFORM_CHEST),
             rule=lambda state: True)  # No additional requirements

    # 2F Side Room
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_DEKU_SCRUB_NEAR_BOMB_BAG_LEFT),
             rule=lambda state: can_stun_deku(state, world))
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_DEKU_SCRUB_NEAR_BOMB_BAG_RIGHT),
             rule=lambda state: can_stun_deku(state, world))

    # First Slingshot Room - require eye switch to be shot
    # Locations in here require hitting the eye switch to access

    # Bomb Room Upper
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_BOMB_BAG_CHEST),
             rule=lambda state: True)  # No additional requirements once in room

    # Far Bridge
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_END_OF_BRIDGE_CHEST),
             rule=lambda state: can_break_mud_walls(state, world))

    # Boss Area and Back Room
    set_rule(world.get_location(Locations.DODONGOS_CAVERN_GSBACK_ROOM),
             rule=lambda state: can_attack(state, world))

    # Many more locations that aren't in the main location table but are in the C++ code
    # These would be pot/crate/grass locations that may be added later
    
    # If these locations exist in the location table, add rules for them:
    location_names_to_check = [
        Locations.DODONGOS_CAVERN_STAIRCASE_POT1,
        Locations.DODONGOS_CAVERN_STAIRCASE_POT2,
        Locations.DODONGOS_CAVERN_STAIRCASE_POT3,
        Locations.DODONGOS_CAVERN_STAIRCASE_POT4,
        "Dodongos Cavern Lower Lizalfos Heart",
        "Dodongos Cavern Upper Lizalfos Left Heart",
        "Dodongos Cavern Upper Lizalfos Right Heart",
        "Dodongos Cavern Blade Room Heart",
        "Dodongos Cavern First Bridge Grass",
        "Dodongos Cavern Blade Grass",
        Locations.DODONGOS_CAVERN_SINGLE_EYE_POT1,
        Locations.DODONGOS_CAVERN_SINGLE_EYE_POT2,
        "Dodongos Cavern Single Eye Grass",
        "Dodongos Cavern Double Eye Pot 1",
        "Dodongos Cavern Double Eye Pot 2",
        Locations.DODONGOS_CAVERN_BLADE_POT1,
        "Dodongos Cavern Blade Pot 2",
        "Dodongos Cavern Before Boss Grass",
        "Dodongos Cavern Back Room Pot 1",
        "Dodongos Cavern Back Room Pot 2",
        "Dodongos Cavern Back Room Pot 3",
        "Dodongos Cavern Back Room Pot 4"
    ]
    
    for location_name in location_names_to_check:
        try:
            location = world.get_location(location_name)
            if "Pot" in location_name:
                set_rule(location, rule=lambda state: can_break_pots(state, world))
            elif "Grass" in location_name:
                set_rule(location, rule=lambda state: can_cut_shrubs(state, world))
            elif "Heart" in location_name:
                set_rule(location, rule=lambda state: True)  # Hearts usually have no additional requirements
        except KeyError:
            # Location doesn't exist in the table, skip it
            pass
    
    # For locations that are currently mapped to "Hyrule" region in Locations.py but should be in dungeon regions:
    # These locations need their region assignments updated in Locations.py to match the proper regions defined above
    
    locations_needing_region_updates = [
        # These should be updated in Locations.py:
        # "Dodongos Cavern GS Side Room Near Lower Lizalfos": "Dodongos Cavern SE Room",
        # "Dodongos Cavern GS Scarecrow": "Dodongos Cavern SE Corridor", 
        # "Dodongos Cavern GS Alcove Above Stairs": "Dodongos Cavern Stairs Upper",
        # "Dodongos Cavern GS Vines Above Stairs": "Dodongos Cavern Stairs Upper",
        # "Dodongos Cavern GS Back Room": "Dodongos Cavern Back Room",
        # "Dodongos Cavern Deku Scrub Side Room Near Dodongos": "Dodongos Cavern Near Dodongo Room",
        # "Dodongos Cavern Deku Scrub Lobby": "Dodongos Cavern Lobby",
        # "Dodongos Cavern Deku Scrub Near Bomb Bag Left": "Dodongos Cavern 2F Side Room",
        # "Dodongos Cavern Deku Scrub Near Bomb Bag Right": "Dodongos Cavern 2F Side Room",
        # Many pot locations should be moved to their proper regions too
    ]
