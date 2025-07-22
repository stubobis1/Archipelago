from __future__ import annotations


import os
import sys

from worlds.poe.Client import launch
import Utils

if __name__ == "__main__":
    Utils.init_logging("poe", exception_logger="Client")
    launch()
