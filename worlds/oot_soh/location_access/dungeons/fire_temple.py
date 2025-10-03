from typing import TYPE_CHECKING

from ...Enums import *
from ...LogicHelpers import *

if TYPE_CHECKING:
    from worlds.oot_soh import SohWorld


class EventLocations(str, Enum):
    FIRE_TEMPLE_NEAR_BOSS_FAIRY_POT = "Fire Temple Near Boss Fairy Pot"
    FIRE_TEMPLE_FIRE_LOOP_SWITCH = "Fire Temple Fire Loop Switch"
    FIRE_TEMPLE_MQ_FAIRY_POT_IRON_KNUCKLE = "Fire Temple MQ Iron Knuckle Fairy Pot"
    FIRE_TEMPLE_MQ_OPENED_LOWEST_GORON_CAGE = "Fire Temple MQ Opened Lowest Goron Cage"
    FIRE_TEMPLE_MQ_TORCH_FIREWALL_FAIRY_POT = "Fire Temple MQ Torch Firewall Fairy Pot"
    FIRE_TEMPLE_MQ_OPENED_UPPER_FIRE_SHORTCUT = "Fire Temple MQ Opened Upper Fire Shortcut"
    FIRE_TEMPLE_MQ_BOSS_FAIRY_POT = "Fire Temple MQ Boss Fairy Pot"
    FIRE_TEMPLE_MQ_HIT_FIRE_TEMPLE_PLATFORM = "Fire Temple MQ Hit Fire Temple Platform"
    FIRE_TEMPLE_MQ_OPENED_FIRE_MQ_FIRE_MAZE_DOOR = "Fire Temple MQ Opened Fire MQ Fire Maze Door"
    FIRE_TEMPLE_CLEAR = "Fire Temple Clear"


class LocalEvents(str, Enum):
    FIRE_LOOP_SWITCH = "Fire Loop Switch"
    OPENED_LOWEST_GORON_CAGE = "Opened Lowest Goron Cage"
    OPENED_UPPER_FIRE_SHORTCUT = "Opened Upper Fire Shortcut"
    HIT_FIRE_TEMPLE_PLATFORM = "Hit Fire Temple Platform"
    OPENED_FIRE_MQ_FIRE_MAZE_DOOR = "Opened Fire MQ Fire Maze Door"


def set_region_rules(world: "SohWorld") -> None:
    player = world.player

    ## Fire Temple Entryway
    # Connections
    connect_regions(Regions.FIRE_TEMPLE_ENTRYWAY, world, [
        # TODO: Add vanilla/MQ check
        [Regions.FIRE_TEMPLE_FIRST_ROOM, lambda state: True],  # ctx->GetDungeon(FIRE_TEMPLE)->IsVanilla()
        [Regions.FIRE_TEMPLE_MQ_FIRST_ROOM_LOWER, lambda state: False],  # ctx->GetDungeon(FIRE_TEMPLE)->IsMQ()
        [Regions.DMC_CENTRAL_LOCAL, lambda state: True]
    ])

    ## Fire Temple First Room
    # Connections
    connect_regions(Regions.FIRE_TEMPLE_FIRST_ROOM, world, [
        [Regions.FIRE_TEMPLE_ENTRYWAY, lambda state: True],
        [Regions.FIRE_TEMPLE_NEAR_BOSS_ROOM, lambda state: has_fire_timer(state, world, 24)],
        [Regions.FIRE_TEMPLE_LOOP_ENEMIES, lambda state: can_use(state, Items.MEGATON_HAMMER) and 
         (has_small_keys(state, world, 8) or not world.fire_loop_locked)],
        [Regions.FIRE_TEMPLE_LOOP_EXIT, lambda state: True],
        [Regions.FIRE_TEMPLE_BIG_LAVA_ROOM, lambda state: has_small_keys(state, world, 2) and has_fire_timer(state, world, 24)]
    ])

    ## Fire Temple Near Boss Room
    # Events
    add_events(Regions.FIRE_TEMPLE_NEAR_BOSS_ROOM, world, [
        [EventLocations.FIRE_TEMPLE_NEAR_BOSS_FAIRY_POT, Events.FAIRY_POT, 
         lambda state: can_use(state, Items.HOVER_BOOTS) or can_use(state, Items.HOOKSHOT)]
    ])

    # Locations
    add_locations(Regions.FIRE_TEMPLE_NEAR_BOSS_ROOM, world, [
        [Locations.FIRE_TEMPLE_NEAR_BOSS_CHEST, lambda state: True],
        [Locations.FIRE_TEMPLE_NEAR_BOSS_POT_1, lambda state: can_break_pots(state, world) and 
         (can_use(state, Items.HOVER_BOOTS) or can_use(state, Items.HOOKSHOT))],
        [Locations.FIRE_TEMPLE_NEAR_BOSS_POT_2, lambda state: can_break_pots(state, world) and 
         (can_use(state, Items.HOVER_BOOTS) or can_use(state, Items.HOOKSHOT))],
        [Locations.FIRE_TEMPLE_NEAR_BOSS_POT_3, lambda state: can_break_pots(state, world) and 
         (can_use(state, Items.HOVER_BOOTS) or can_use(state, Items.HOOKSHOT))],
        [Locations.FIRE_TEMPLE_NEAR_BOSS_POT_4, lambda state: can_break_pots(state, world) and 
         (can_use(state, Items.HOVER_BOOTS) or can_use(state, Items.HOOKSHOT))]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_NEAR_BOSS_ROOM, world, [
        [Regions.FIRE_TEMPLE_FIRST_ROOM, lambda state: True],
        [Regions.FIRE_TEMPLE_BOSS_ENTRYWAY, lambda state: is_adult(state, world) and 
         (world.fire_boss_door_jump or can_use(state, Items.HOVER_BOOTS) or 
          (can_use(state, Items.MEGATON_HAMMER) and state.can_reach(Regions.FIRE_TEMPLE_FIRE_MAZE_UPPER)))]
    ])

    ## Fire Temple Loop Enemies
    # Connections
    connect_regions(Regions.FIRE_TEMPLE_LOOP_ENEMIES, world, [
        [Regions.FIRE_TEMPLE_FIRST_ROOM, lambda state: has_small_keys(state, world, 8) or not world.fire_loop_locked],
        [Regions.FIRE_TEMPLE_LOOP_TILES, lambda state: can_kill_enemy(state, world, EnemyType.TORCH_SLUG) and 
         can_kill_enemy(state, world, EnemyType.FIRE_KEESE)]
    ])

    ## Fire Temple Loop Tiles
    # Locations
    add_locations(Regions.FIRE_TEMPLE_LOOP_TILES, world, [
        [Locations.FIRE_TEMPLE_GS_BOSS_KEY_LOOP, lambda state: can_attack(state, world)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_LOOP_TILES, world, [
        [Regions.FIRE_TEMPLE_LOOP_ENEMIES, lambda state: True],
        [Regions.FIRE_TEMPLE_LOOP_FLARE_DANCER, lambda state: True]
    ])

    ## Fire Temple Loop Flare Dancer
    # Locations
    add_locations(Regions.FIRE_TEMPLE_LOOP_FLARE_DANCER, world, [
        [Locations.FIRE_TEMPLE_FLARE_DANCER_CHEST, lambda state: (has_explosives(state, world) or 
         can_use(state, Items.MEGATON_HAMMER)) and is_adult(state, world)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_LOOP_FLARE_DANCER, world, [
        [Regions.FIRE_TEMPLE_LOOP_TILES, lambda state: True],
        [Regions.FIRE_TEMPLE_LOOP_HAMMER_SWITCH, lambda state: can_kill_enemy(state, world, EnemyType.FLARE_DANCER)]
    ])

    ## Fire Temple Loop Hammer Switch
    # Events
    add_events(Regions.FIRE_TEMPLE_LOOP_HAMMER_SWITCH, world, [
        [EventLocations.FIRE_TEMPLE_FIRE_LOOP_SWITCH, LocalEvents.FIRE_LOOP_SWITCH, 
         lambda state: can_use(state, Items.MEGATON_HAMMER)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_LOOP_HAMMER_SWITCH, world, [
        [Regions.FIRE_TEMPLE_LOOP_FLARE_DANCER, lambda state: True],
        [Regions.FIRE_TEMPLE_LOOP_GORON_ROOM, lambda state: state.has(LocalEvents.FIRE_LOOP_SWITCH, player)]
    ])

    ## Fire Temple Loop Goron Room
    # Locations
    add_locations(Regions.FIRE_TEMPLE_LOOP_GORON_ROOM, world, [
        [Locations.FIRE_TEMPLE_BOSS_KEY_CHEST, lambda state: True]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_LOOP_GORON_ROOM, world, [
        [Regions.FIRE_TEMPLE_LOOP_HAMMER_SWITCH, lambda state: state.has(LocalEvents.FIRE_LOOP_SWITCH, player)],
        [Regions.FIRE_TEMPLE_LOOP_EXIT, lambda state: state.has(LocalEvents.FIRE_LOOP_SWITCH, player)]
    ])

    ## Fire Temple Loop Exit
    # Connections
    connect_regions(Regions.FIRE_TEMPLE_LOOP_EXIT, world, [
        [Regions.FIRE_TEMPLE_FIRST_ROOM, lambda state: True],
        [Regions.FIRE_TEMPLE_LOOP_GORON_ROOM, lambda state: state.has(LocalEvents.FIRE_LOOP_SWITCH, player)]
    ])

    ## Fire Temple Big Lava Room
    # Locations
    add_locations(Regions.FIRE_TEMPLE_BIG_LAVA_ROOM, world, [
        [Locations.FIRE_TEMPLE_BIG_LAVA_POT_1, lambda state: can_break_pots(state, world)],
        [Locations.FIRE_TEMPLE_BIG_LAVA_POT_2, lambda state: can_break_pots(state, world)],
        [Locations.FIRE_TEMPLE_BIG_LAVA_POT_3, lambda state: can_break_pots(state, world)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_BIG_LAVA_ROOM, world, [
        [Regions.FIRE_TEMPLE_FIRST_ROOM, lambda state: has_small_keys(state, world, 2)],
        [Regions.FIRE_TEMPLE_BIG_LAVA_ROOM_NORTH_GORON, lambda state: True],
        [Regions.FIRE_TEMPLE_BIG_LAVA_ROOM_NORTH_TILES, lambda state: is_adult(state, world) and 
         (can_use(state, Items.SONG_OF_TIME) or world.fire_sot_trick)],
        [Regions.FIRE_TEMPLE_BIG_LAVA_ROOM_SOUTH_GORON, lambda state: is_adult(state, world) and has_explosives(state, world)],
        [Regions.FIRE_TEMPLE_FIRE_PILLAR_ROOM, lambda state: has_small_keys(state, world, 3)]
    ])

    ## Fire Temple Big Lava Room North Goron
    # Locations
    add_locations(Regions.FIRE_TEMPLE_BIG_LAVA_ROOM_NORTH_GORON, world, [
        [Locations.FIRE_TEMPLE_BIG_LAVA_ROOM_LOWER_OPEN_DOOR_CHEST, lambda state: True]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_BIG_LAVA_ROOM_NORTH_GORON, world, [
        [Regions.FIRE_TEMPLE_BIG_LAVA_ROOM, lambda state: True]
    ])

    ## Fire Temple Big Lava Room North Tiles
    # Locations
    add_locations(Regions.FIRE_TEMPLE_BIG_LAVA_ROOM_NORTH_TILES, world, [
        [Locations.FIRE_TEMPLE_GS_SONG_OF_TIME_ROOM, lambda state: (is_adult(state, world) and can_attack(state, world)) or 
         hookshot_or_boomerang(state, world)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_BIG_LAVA_ROOM_NORTH_TILES, world, [
        [Regions.FIRE_TEMPLE_BIG_LAVA_ROOM, lambda state: True]
    ])

    ## Fire Temple Big Lava Room South Goron
    # Locations
    add_locations(Regions.FIRE_TEMPLE_BIG_LAVA_ROOM_SOUTH_GORON, world, [
        [Locations.FIRE_TEMPLE_BIG_LAVA_ROOM_BLOCKED_DOOR_CHEST, lambda state: True]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_BIG_LAVA_ROOM_SOUTH_GORON, world, [
        [Regions.FIRE_TEMPLE_BIG_LAVA_ROOM, lambda state: True]
    ])

    ## Fire Temple Fire Pillar Room
    # Locations
    add_locations(Regions.FIRE_TEMPLE_FIRE_PILLAR_ROOM, world, [
        [Locations.FIRE_TEMPLE_FIRE_PILLAR_LEFT_HEART, lambda state: has_fire_timer(state, world, 56)],
        [Locations.FIRE_TEMPLE_FIRE_PILLAR_RIGHT_HEART, lambda state: has_fire_timer(state, world, 56)],
        [Locations.FIRE_TEMPLE_FIRE_PILLAR_BACK_HEART, lambda state: has_fire_timer(state, world, 56)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_FIRE_PILLAR_ROOM, world, [
        [Regions.FIRE_TEMPLE_BIG_LAVA_ROOM, lambda state: has_small_keys(state, world, 3)],
        [Regions.FIRE_TEMPLE_SHORTCUT_ROOM, lambda state: has_fire_timer(state, world, 56) and has_small_keys(state, world, 4)]
    ])

    ## Fire Temple Shortcut Room
    # Locations
    add_locations(Regions.FIRE_TEMPLE_SHORTCUT_ROOM, world, [
        [Locations.FIRE_TEMPLE_BOULDER_MAZE_SHORTCUT_CHEST, lambda state: state.can_reach(Regions.FIRE_TEMPLE_SHORTCUT_CLIMB)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_SHORTCUT_ROOM, world, [
        [Regions.FIRE_TEMPLE_FIRE_PILLAR_ROOM, lambda state: has_small_keys(state, world, 4)],
        [Regions.FIRE_TEMPLE_SHORTCUT_CLIMB, lambda state: state.can_reach(Regions.FIRE_TEMPLE_SHORTCUT_CLIMB)],
        [Regions.FIRE_TEMPLE_BOULDER_MAZE_LOWER, lambda state: is_adult(state, world) and 
         (has_item(state, Items.GORONS_BRACELET) or world.fire_strength_trick) and 
         (has_explosives(state, world) or can_use(state, Items.FAIRY_BOW) or 
          can_use(state, Items.HOOKSHOT) or can_use(state, Items.FAIRY_SLINGSHOT))]
    ])

    ## Fire Temple Shortcut Climb
    # Connections
    connect_regions(Regions.FIRE_TEMPLE_SHORTCUT_CLIMB, world, [
        [Regions.FIRE_TEMPLE_SHORTCUT_ROOM, lambda state: True],
        [Regions.FIRE_TEMPLE_BOULDER_MAZE_UPPER, lambda state: True]
    ])

    ## Fire Temple Boulder Maze Lower
    # Locations
    add_locations(Regions.FIRE_TEMPLE_BOULDER_MAZE_LOWER, world, [
        [Locations.FIRE_TEMPLE_BOULDER_MAZE_LOWER_CHEST, lambda state: True],
        [Locations.FIRE_TEMPLE_GS_BOULDER_MAZE, lambda state: has_explosives(state, world) and 
         (is_adult(state, world) or hookshot_or_boomerang(state, world))]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_BOULDER_MAZE_LOWER, world, [
        [Regions.FIRE_TEMPLE_SHORTCUT_ROOM, lambda state: True],
        [Regions.FIRE_TEMPLE_BOULDER_MAZE_LOWER_SIDE_ROOM, lambda state: True],
        [Regions.FIRE_TEMPLE_EAST_CENTRAL_ROOM, lambda state: has_small_keys(state, world, 5)],
        # Boulder maze upper entrance is false in original
    ])

    ## Fire Temple Boulder Maze Lower Side Room
    # Locations
    add_locations(Regions.FIRE_TEMPLE_BOULDER_MAZE_LOWER_SIDE_ROOM, world, [
        [Locations.FIRE_TEMPLE_BOULDER_MAZE_SIDE_ROOM_CHEST, lambda state: True]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_BOULDER_MAZE_LOWER_SIDE_ROOM, world, [
        [Regions.FIRE_TEMPLE_BOULDER_MAZE_LOWER, lambda state: True]
    ])

    ## Fire Temple East Central Room
    # Locations
    add_locations(Regions.FIRE_TEMPLE_EAST_CENTRAL_ROOM, world, [
        [Locations.FIRE_TEMPLE_EAST_CENTRAL_LEFT_HEART, lambda state: True],
        [Locations.FIRE_TEMPLE_EAST_CENTRAL_RIGHT_HEART, lambda state: True],
        [Locations.FIRE_TEMPLE_EAST_CENTRAL_MIDDLE_HEART, lambda state: True]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_EAST_CENTRAL_ROOM, world, [
        [Regions.FIRE_TEMPLE_BIG_LAVA_ROOM, lambda state: can_take_damage(state, world)],
        [Regions.FIRE_TEMPLE_BOULDER_MAZE_LOWER, lambda state: has_small_keys(state, world, 5)],
        [Regions.FIRE_TEMPLE_FIRE_WALL_CHASE, lambda state: has_small_keys(state, world, 6)],
        [Regions.FIRE_TEMPLE_MAP_REGION, lambda state: can_use(state, Items.FAIRY_SLINGSHOT) or can_use(state, Items.FAIRY_BOW)]
    ])

    ## Fire Temple Fire Wall Chase
    # Locations
    add_locations(Regions.FIRE_TEMPLE_FIRE_WALL_CHASE, world, [
        [Locations.FIRE_TEMPLE_FIRE_WALL_EAST_HEART, lambda state: has_fire_timer(state, world, 24) and 
         (is_adult(state, world) or can_use(state, Items.BOOMERANG))],
        [Locations.FIRE_TEMPLE_FIRE_WALL_WEST_HEART, lambda state: has_fire_timer(state, world, 24) and 
         (is_adult(state, world) or can_use(state, Items.BOOMERANG))],
        [Locations.FIRE_TEMPLE_FIRE_WALL_EXIT_HEART, lambda state: has_fire_timer(state, world, 24)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_FIRE_WALL_CHASE, world, [
        [Regions.FIRE_TEMPLE_EAST_CENTRAL_ROOM, lambda state: has_fire_timer(state, world, 24) and has_small_keys(state, world, 6)],
        [Regions.FIRE_TEMPLE_MAP_REGION, lambda state: is_adult(state, world)],
        [Regions.FIRE_TEMPLE_BOULDER_MAZE_UPPER, lambda state: has_fire_timer(state, world, 24) and is_adult(state, world)],
        [Regions.FIRE_TEMPLE_CORRIDOR, lambda state: has_fire_timer(state, world, 24) and is_adult(state, world) and 
         has_small_keys(state, world, 7)]
    ])

    ## Fire Temple Map Region
    # Locations
    add_locations(Regions.FIRE_TEMPLE_MAP_REGION, world, [
        [Locations.FIRE_TEMPLE_MAP_CHEST, lambda state: True]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_MAP_REGION, world, [
        [Regions.FIRE_TEMPLE_EAST_CENTRAL_ROOM, lambda state: True]
    ])

    ## Fire Temple Boulder Maze Upper
    # Locations
    add_locations(Regions.FIRE_TEMPLE_BOULDER_MAZE_UPPER, world, [
        [Locations.FIRE_TEMPLE_BOULDER_MAZE_UPPER_CHEST, lambda state: True]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_BOULDER_MAZE_UPPER, world, [
        [Regions.FIRE_TEMPLE_SHORTCUT_CLIMB, lambda state: has_explosives(state, world)],
        [Regions.FIRE_TEMPLE_BOULDER_MAZE_LOWER, lambda state: True],
        [Regions.FIRE_TEMPLE_FIRE_WALL_CHASE, lambda state: True],
        [Regions.FIRE_TEMPLE_SCARECROW_ROOM, lambda state: can_use(state, Items.SCARECROW) or 
         (world.fire_scarecrow_trick and is_adult(state, world) and can_use(state, Items.LONGSHOT))]
    ])

    ## Fire Temple Scarecrow Room
    # Locations
    add_locations(Regions.FIRE_TEMPLE_SCARECROW_ROOM, world, [
        [Locations.FIRE_TEMPLE_GS_SCARECROW_CLIMB, lambda state: can_jumpslash_except_hammer(state, world) or 
         can_use(state, Items.FAIRY_SLINGSHOT) or can_use(state, Items.BOOMERANG) or has_explosives(state, world) or 
         can_use(state, Items.FAIRY_BOW) or can_use(state, Items.HOOKSHOT) or can_use(state, Items.DINS_FIRE)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_SCARECROW_ROOM, world, [
        [Regions.FIRE_TEMPLE_BOULDER_MAZE_UPPER, lambda state: True],
        [Regions.FIRE_TEMPLE_EAST_PEAK, lambda state: True]
    ])

    ## Fire Temple East Peak
    # Locations
    add_locations(Regions.FIRE_TEMPLE_EAST_PEAK, world, [
        [Locations.FIRE_TEMPLE_SCARECROW_CHEST, lambda state: True],
        [Locations.FIRE_TEMPLE_GS_SCARECROW_TOP, lambda state: can_use_projectile(state, world)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_EAST_PEAK, world, [
        [Regions.FIRE_TEMPLE_SCARECROW_ROOM, lambda state: True],
        [Regions.FIRE_TEMPLE_EAST_CENTRAL_ROOM, lambda state: can_take_damage(state, world)]
    ])

    ## Fire Temple Corridor
    # Connections
    connect_regions(Regions.FIRE_TEMPLE_CORRIDOR, world, [
        [Regions.FIRE_TEMPLE_FIRE_WALL_CHASE, lambda state: has_small_keys(state, world, 7)],
        [Regions.FIRE_TEMPLE_FIRE_MAZE_ROOM, lambda state: True]
    ])

    ## Fire Temple Fire Maze Room
    # Locations
    add_locations(Regions.FIRE_TEMPLE_FIRE_MAZE_ROOM, world, [
        [Locations.FIRE_TEMPLE_FLAME_MAZE_LEFT_POT_1, lambda state: can_break_pots(state, world)],
        [Locations.FIRE_TEMPLE_FLAME_MAZE_LEFT_POT_2, lambda state: can_break_pots(state, world)],
        [Locations.FIRE_TEMPLE_FLAME_MAZE_LEFT_POT_3, lambda state: can_break_pots(state, world)],
        [Locations.FIRE_TEMPLE_FLAME_MAZE_LEFT_POT_4, lambda state: can_break_pots(state, world)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_FIRE_MAZE_ROOM, world, [
        [Regions.FIRE_TEMPLE_CORRIDOR, lambda state: True],
        [Regions.FIRE_TEMPLE_FIRE_MAZE_UPPER, lambda state: can_use(state, Items.HOVER_BOOTS)],
        [Regions.FIRE_TEMPLE_FIRE_MAZE_SIDE_ROOM, lambda state: True],
        [Regions.FIRE_TEMPLE_WEST_CENTRAL_LOWER, lambda state: has_small_keys(state, world, 8)],
        [Regions.FIRE_TEMPLE_LATE_FIRE_MAZE, lambda state: world.fire_flame_maze_trick]
    ])

    ## Fire Temple Fire Maze Upper
    # Connections
    connect_regions(Regions.FIRE_TEMPLE_FIRE_MAZE_UPPER, world, [
        [Regions.FIRE_TEMPLE_NEAR_BOSS_ROOM, lambda state: can_use(state, Items.MEGATON_HAMMER)],
        [Regions.FIRE_TEMPLE_FIRE_MAZE_ROOM, lambda state: True],
        [Regions.FIRE_TEMPLE_WEST_CENTRAL_UPPER, lambda state: can_use(state, Items.MEGATON_HAMMER)]
    ])

    ## Fire Temple Fire Maze Side Room
    # Locations
    add_locations(Regions.FIRE_TEMPLE_FIRE_MAZE_SIDE_ROOM, world, [
        [Locations.FIRE_TEMPLE_COMPASS_CHEST, lambda state: True]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_FIRE_MAZE_SIDE_ROOM, world, [
        [Regions.FIRE_TEMPLE_FIRE_MAZE_ROOM, lambda state: True]
    ])

    ## Fire Temple West Central Lower
    # Locations
    add_locations(Regions.FIRE_TEMPLE_WEST_CENTRAL_LOWER, world, [
        [Locations.FIRE_TEMPLE_HIGHEST_GORON_CHEST, lambda state: state.can_reach(Regions.FIRE_TEMPLE_WEST_CENTRAL_UPPER) and
         (can_use(state, Items.SONG_OF_TIME) or world.rusted_switches_trick) and can_use(state, Items.MEGATON_HAMMER)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_WEST_CENTRAL_LOWER, world, [
        [Regions.FIRE_TEMPLE_FIRE_MAZE_ROOM, lambda state: has_small_keys(state, world, 8)],
        [Regions.FIRE_TEMPLE_WEST_CENTRAL_UPPER, lambda state: is_adult(state, world) and can_use(state, Items.SONG_OF_TIME)],
        [Regions.FIRE_TEMPLE_LATE_FIRE_MAZE, lambda state: True]
    ])

    ## Fire Temple West Central Upper
    # Connections
    connect_regions(Regions.FIRE_TEMPLE_WEST_CENTRAL_UPPER, world, [
        # Boss entryway is false in original
        [Regions.FIRE_TEMPLE_FIRE_MAZE_UPPER, lambda state: True],
        [Regions.FIRE_TEMPLE_WEST_CENTRAL_LOWER, lambda state: True]
    ])

    ## Fire Temple Late Fire Maze
    # Locations
    add_locations(Regions.FIRE_TEMPLE_LATE_FIRE_MAZE, world, [
        [Locations.FIRE_TEMPLE_FLAME_MAZE_RIGHT_POT_1, lambda state: can_break_pots(state, world)],
        [Locations.FIRE_TEMPLE_FLAME_MAZE_RIGHT_POT_2, lambda state: can_break_pots(state, world)],
        [Locations.FIRE_TEMPLE_FLAME_MAZE_RIGHT_POT_3, lambda state: can_break_pots(state, world)],
        [Locations.FIRE_TEMPLE_FLAME_MAZE_RIGHT_POT_4, lambda state: can_break_pots(state, world)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_LATE_FIRE_MAZE, world, [
        # Fire maze room entrance is false in original
        [Regions.FIRE_TEMPLE_WEST_CENTRAL_LOWER, lambda state: True],
        [Regions.FIRE_TEMPLE_UPPER_FLARE_DANCER, lambda state: has_explosives(state, world)]
    ])

    ## Fire Temple Upper Flare Dancer
    # Connections
    connect_regions(Regions.FIRE_TEMPLE_UPPER_FLARE_DANCER, world, [
        [Regions.FIRE_TEMPLE_LATE_FIRE_MAZE, lambda state: can_kill_enemy(state, world, EnemyType.FLARE_DANCER)],
        [Regions.FIRE_TEMPLE_WEST_CLIMB, lambda state: can_kill_enemy(state, world, EnemyType.FLARE_DANCER)]
    ])

    ## Fire Temple West Climb
    # Connections
    connect_regions(Regions.FIRE_TEMPLE_WEST_CLIMB, world, [
        [Regions.FIRE_TEMPLE_UPPER_FLARE_DANCER, lambda state: True],
        [Regions.FIRE_TEMPLE_WEST_PEAK, lambda state: can_use_projectile(state, world)]
    ])

    ## Fire Temple West Peak
    # Locations
    add_locations(Regions.FIRE_TEMPLE_WEST_PEAK, world, [
        [Locations.FIRE_TEMPLE_MEGATON_HAMMER_CHEST, lambda state: True]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_WEST_PEAK, world, [
        [Regions.FIRE_TEMPLE_WEST_CENTRAL_UPPER, lambda state: can_take_damage(state, world)],
        [Regions.FIRE_TEMPLE_WEST_CLIMB, lambda state: True],
        [Regions.FIRE_TEMPLE_HAMMER_RETURN_PATH, lambda state: can_use(state, Items.MEGATON_HAMMER)]
    ])

    ## Fire Temple Hammer Return Path
    # Locations
    add_locations(Regions.FIRE_TEMPLE_HAMMER_RETURN_PATH, world, [
        [Locations.FIRE_TEMPLE_AFTER_HAMMER_SMALL_CRATE_1, lambda state: can_break_small_crates(state, world)],
        [Locations.FIRE_TEMPLE_AFTER_HAMMER_SMALL_CRATE_2, lambda state: can_break_small_crates(state, world)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_HAMMER_RETURN_PATH, world, [
        [Regions.FIRE_TEMPLE_ABOVE_FIRE_MAZE, lambda state: can_use(state, Items.MEGATON_HAMMER)]
    ])

    ## Fire Temple Above Fire Maze
    # Connections
    connect_regions(Regions.FIRE_TEMPLE_ABOVE_FIRE_MAZE, world, [
        [Regions.FIRE_TEMPLE_HAMMER_RETURN_PATH, lambda state: True],
        [Regions.FIRE_TEMPLE_FIRE_MAZE_UPPER, lambda state: can_use(state, Items.MEGATON_HAMMER)]
    ])

    ## Fire Temple Boss Entryway
    # Connections
    connect_regions(Regions.FIRE_TEMPLE_BOSS_ENTRYWAY, world, [
        # Vanilla and MQ near boss room connections are false in original
        [Regions.FIRE_TEMPLE_BOSS_ROOM, lambda state: has_item(state, Items.FIRE_TEMPLE_BOSS_KEY)]
    ])

    ## Fire Temple Boss Room
    # Events
    add_events(Regions.FIRE_TEMPLE_BOSS_ROOM, world, [
        [EventLocations.FIRE_TEMPLE_CLEAR, Events.FIRE_TEMPLE_CLEAR, 
         lambda state: has_fire_timer(state, world, 64) and can_kill_enemy(state, world, EnemyType.VOLVAGIA)]
    ])

    # Locations
    add_locations(Regions.FIRE_TEMPLE_BOSS_ROOM, world, [
        [Locations.FIRE_TEMPLE_VOLVAGIA_HEART, lambda state: state.has(Events.FIRE_TEMPLE_CLEAR, player)],
        [Locations.VOLVAGIA, lambda state: state.has(Events.FIRE_TEMPLE_CLEAR, player)]
    ])

    # Connections
    connect_regions(Regions.FIRE_TEMPLE_BOSS_ROOM, world, [
        # Boss entryway connection is false in original
        [Regions.DMC_CENTRAL_LOCAL, lambda state: state.has(Events.FIRE_TEMPLE_CLEAR, player)]
    ])

    # TODO: Add Master Quest regions and locations
    # For now focusing on vanilla implementation
    
