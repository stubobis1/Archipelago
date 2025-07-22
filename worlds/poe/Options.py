from dataclasses import dataclass, fields, Field
from typing import FrozenSet, Union, Set

from Options import Choice, Toggle, DefaultOnToggle, ItemSet, OptionSet, Range, PerGameCommonOptions
from worlds.AutoWorld import World



class GearUnlocks(Toggle):
    """
    Specifies if normal gear should be restricted.
    """
    display_name = "Gear Unlocks"
    default = False

class GucciHoboMode(Choice):
    """
    Specifies if the world should be in Gucci Hobo Mode, this restricts use of any non-unique equipment to only 1 slot.
    This is an extremely difficult challenge intended for experienced players, and will greatly increase the length of your run.
    Expect a very slow start, involving farming early act 1 zones.
    """
    display_name = "Gucci Hobo Mode"
    option_disabled = 4
    option_allow_one_slot_of_any_rarity = 1
    option_allow_one_slot_of_normal_rarity = 2
    option_no_non_unique_items = 3
    default = 4

class GearUpgrades(Choice):
    """
    Specifies if gear rarity should be restricted to a certain rarity, unlockable through items found in the multiworld.
    """
    display_name = "Gear Unlocks"
    option_all_gear_unlocked = 0
    option_all_uniques_unlocked = 1
    option_no_gear_unlocked = 2
    default = 1

class GearUpgradesPerAct(Range):
    """
    Specifies a minimum number of rarity of gear upgrades available per act. (there are 38 total)
    This will be ignored if the "Gear Upgrades" option is turned off.
    """
    display_name = "Gear Upgrades Per Act"
    range_start = 0
    range_end = 38
    default = 5
    
class FlaskSlotUpgrades(Toggle):
    """
    Specifies if the number of flask slots should be restricted, unlockable through items found in the multiworld.
    """
    display_name = "Flask Slot Upgrades"
    default = False

class FlaskSlotsPerAct(Range):
    """
    Specifies a minimum number of available flask slots per act. (there are 5 total)
    This will be ignored if the "Flask Slots" option is turned off.
    """
    display_name = "Flask Slots Per Act"
    range_start = 0
    range_end = 5
    default = 1

class SupportGemSlotUpgrades(Toggle):
    """
    Specifies if the number of linked support gem slots you can use should be restricted, unlockable through items found in the multiworld.
    """
    display_name = "Support Gem Slot Upgrades"
    default = True

class SupportGemSlotsPerAct(Range):
    """
    Specifies a minimum number of available support gem slots (maximum usable links in items) per act. (there are 21 total)
    This will be ignored if the "Support Gem Slot Upgrades" option is turned off.
    """
    display_name = "Support Gem Slots Per Act"
    range_start = 0
    range_end = 21
    default = 2


class SkillGemsPerAct(Range):
    """
    Specifies a minimum number of available, usable skill gems per act.
    """
    display_name = "Skill Gem Slots Per Act"
    range_start = 0
    range_end = 20
    default = 2

class AscendanciesAvailablePerClass(Range):
    """
    Specifies the maximum number of available ascendancies per class.
    """
    display_name = "Ascendancies Available Per Class"
    range_start = 0
    range_end = 3
    default = 1

class AllowUnlockOfOtherCharacters(Toggle):
    """
    Allows unlocking of other characters.
    """
    display_name = "Allow Unlock of Other Characters"
    default = False

class StartingCharacter(Choice):
    """
    The starting character for the world. This will determine the class available at the start.
    """
    display_name = "Starting Character"
    option_marauder    = 1
    option_ranger      = 2
    option_witch       = 3
    option_duelist     = 4
    option_templar     = 5
    option_shadow      = 6
    option_scion       = 7
    default = "random"

class EnableTTS(Choice):
    """
    Settings for the Text-to-Speech (TTS) feature.
    """
    display_name = "Text-to-Speech"
    option_no_tts     = 0
    option_enabled_AP_Item = 1
    option_enabled_Base_Item = 2
    default = 1

class TTSSpeed(Range):
    """
    Speed of the Text-to-Speech (TTS) feature.
    """
    display_name = "TTS Speed"
    range_start = 50
    range_end = 500
    default = 200


@dataclass
class PathOfExileOptions(PerGameCommonOptions):
    """
    Common options for Path of Exile.
    """
    gear_unlocks: GearUnlocks
    gear_upgrades: GearUpgrades
    gear_upgrades_per_act: GearUpgradesPerAct
    flask_slot_upgrades: FlaskSlotUpgrades
    flask_slots_per_act: FlaskSlotsPerAct
    gucci_hobo_mode: GucciHoboMode
    support_gem_slot_upgrades: SupportGemSlotUpgrades
    support_gem_slots_per_act: SupportGemSlotsPerAct
    skill_gems_per_act: SkillGemsPerAct
    ascendancies_available_per_class: AscendanciesAvailablePerClass
    allow_unlock_of_other_characters: AllowUnlockOfOtherCharacters
    starting_character: StartingCharacter
    enable_tts: EnableTTS
    tts_speed: TTSSpeed
