from worlds.poe.Options import PathOfExileOptions
from .Locations import PathOfExileLocation, base_item_types, acts
from . import Items
from BaseClasses import CollectionState, Region

MAX_GEAR_UPGRADES   = 50
MAX_FLASK_SLOTS     = 10
MAX_GEM_SLOTS       = 21
MAX_SKILL_GEMS      = 20 # you will get more, but this is the max required for "logic"
_debug = True
_very_debug = False


req_to_use_weapon_types = ["Axe","Bow","Claw","Dagger","Mace","Sceptre","Staff","Sword","Wand",
                            #"Fishing Rod", # yeahhhh no
                            #"Unarmed" # every character can use unarmed, so no need to check this
                            ]

def can_reach(act: int, world , state: CollectionState) -> bool:
    opt : PathOfExileOptions = world.options

    reachable = True
    if act < 1:
        return True


    ascedancy_amount = opt.ascendancies_available_per_class.value if act == 3 else 0
    gear_amount = min(opt.gear_upgrades_per_act.value * (act - 1), MAX_GEAR_UPGRADES)
    flask_amount = 0 if not opt.flask_slot_upgrades else min(opt.flask_slots_per_act.value * (act - 1), MAX_FLASK_SLOTS)
    gem_slot_amount = 0 if not opt.support_gem_slot_upgrades else min(opt.support_gem_slots_per_act.value * (act - 1), MAX_GEM_SLOTS)
    skill_gem_amount = min(opt.skill_gems_per_act.value * (act - 1), MAX_SKILL_GEMS)

    # make a list of valid weapon types, based on the state

    valid_weapon_types = {
        item for item in req_to_use_weapon_types
        if state.has_from_list([i["name"] for i in Items.get_by_category(item)], world.player, 1)
    }
    valid_weapon_types.add("Unarmed")  # every character can use unarmed, so we always add it
    
    ascedancy_count = state.count_from_list([item['name'] for item in Items.get_ascendancy_class_items(opt.starting_character.current_option_name)], world.player)
    gear_count = state.count_from_list([item['name'] for item in Items.get_gear_items()], world.player)
    flask_count = state.count_from_list([item['name'] for item in Items.get_flask_items()], world.player)
    gem_slot_count = state.count_from_list([item['name'] for item in Items.get_max_links_items()], world.player)

    usable_skill_gem_count = 0


    gems_for_our_weapons = [item['name'] for item in Items.get_main_skill_gems_by_required_level_and_useable_weapon(
            available_weapons= valid_weapon_types, level_minimum=1, level_maximum=acts[act].get("maxMonsterLevel", 0) )]
    usable_skill_gem_count = (state.count_from_list(gems_for_our_weapons, world.player))


    
    if act == 1:
        normal_weapons = state.count_from_list([item['name'] for item in Items.get_by_has_every_category({"Weapon","Normal"})], world.player)
        normal_armour = state.count_from_list([item['name'] for item in Items.get_by_has_every_category({"Armour", "Normal"})], world.player)
        reachable &= usable_skill_gem_count >= 2
        reachable &= normal_weapons >= 1
        reachable &= normal_armour >= 1
        reachable &= flask_count >= 1


    reachable &= ascedancy_count >= ascedancy_amount and \
           gear_count >= gear_amount and \
           flask_count >= flask_amount and \
           gem_slot_count >= gem_slot_amount and \
           usable_skill_gem_count >= skill_gem_amount
           
    if not reachable:
        if _debug:
            print (f"[DEBUG] Act {act} not reachable with gear: {gear_count}/{gear_amount}, flask: {flask_count}/{flask_amount}, gem slots: {gem_slot_count}/{gem_slot_amount}, skill gems: {usable_skill_gem_count}/{skill_gem_amount}, ascendancies: {ascedancy_count}/{ascedancy_amount} for {opt.starting_character.current_option_name}")
        if _very_debug:
            print(f"[DEBUG] expecting Act {act} - Gear: {gear_amount}, Flask: {flask_amount}, Gem Slots: {gem_slot_amount}, Skill Gems: {skill_gem_amount}, Ascendancies: {ascedancy_amount}")
            print(f"[DEBUG] we have   Act {act} - Gear: {gear_count}, Flask: {flask_count}, Gem Slots: {gem_slot_count}, Skill Gems: {usable_skill_gem_count}, Ascendancies: {ascedancy_count}")
            #add up all the prog items


            total_items = state.count_from_list([item["name"] for item in Items.get_gear_items()], world.player) + \
                          state.count_from_list([item["name"] for item in Items.get_flask_items()], world.player) + \
                          state.count_from_list([item["name"] for item in Items.get_max_links_items()], world.player) + \
                          state.count_from_list([item["name"] for item in Items.get_main_skill_gem_items()], world.player) + \
                          state.count_from_list([item["name"] for item in Items.get_ascendancy_class_items(opt.starting_character.current_option_name)], world.player)
            print(f"[DEBUG] total items {total_items}, ")
            print(f"[DEBUG] expecting   {gear_amount + flask_amount + gem_slot_amount + skill_gem_amount} items")
            print(f"\n\n")

    if _debug:
#        print(f"[DEBUG] Act {act} reachable: {reachable}")
        pass
    
    
    return reachable



