from dataclasses import dataclass
from Options import OptionList, PerGameCommonOptions, Toggle, DefaultOnToggle, Accessibility


class RequiredItemList(OptionList):
    """Comma-separated list of items to unlock in this game. These items are logically required in the multiworld."""
    display_name = "Required Items to unlock"
    default = ["Item 1", "Item 2", "Item 3"]

class OptionalItemList(OptionList):
    """Comma-separated list of items to unlock in this game. These items are optionally required in the multiworld."""
    display_name = "Optional items to unlock"
    default = []

class OnlyAllowOtherGamesItems(DefaultOnToggle):
    """If enabled, only items from other games will be used. if false, items from any unlocker game can also be used."""
    display_name = "Only allow items from other games"
    description = "If enabled, only items from other games will be used."


# maybe have a separate option for progression items vs non-progression items?
# maybe have an option for if unlocker will allow any unlocker items to be used in generation?

@dataclass
class UnlockerOptions(PerGameCommonOptions):
    required_item_list: RequiredItemList
    optional_item_list: OptionalItemList
    only_allow_other_games_items: OnlyAllowOtherGamesItems