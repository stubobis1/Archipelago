if False:
    from . import OMFWorld  # type hint only


def set_rules(world: "OMFWorld") -> None:
    player   = world.player
    goal_idx = world.options.goal_tournament.value
    goal_all = goal_idx == 4

    # HAR buy location access rules are set by the connection rules in Regions.py
    # (each HAR Mechlab region requires the HAR unlock item via the Menu→region connection rule).
    # No additional per-location rules needed here.

    # Completion condition: player can reach the Victory event location.
    # Note: all tournament regions are accessible from Menu (money enforces ordering in-game),
    # so the Victory event is reachable as soon as the goal region is.
    if goal_all:
        from .data.tournaments import TOURNAMENTS
        goal_tournament_names = [t["name"] for t in TOURNAMENTS]
        world.multiworld.completion_condition[player] = lambda state: all(
            state.can_reach(f"Win {name}", "Location", player)
            for name in goal_tournament_names
        )
    else:
        world.multiworld.completion_condition[player] = lambda state: state.has("Victory", player)
