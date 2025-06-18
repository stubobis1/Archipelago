from __future__ import annotations

import ModuleUpdate
ModuleUpdate.update()

from worlds.unlocker.client import launch
import Utils

if __name__ == "__main__":
    Utils.init_logging("poe", exception_logger="Client")
    launch()
