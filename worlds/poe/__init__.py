from worlds.LauncherComponents import components, Component, launch_subprocess, Type, icon_paths

from BaseClasses import Region, MultiWorld, Item, Location, LocationProgressType, ItemClassification
from worlds.AutoWorld import World, WebWorld
from Utils import visualize_regions
import os
import yaml
import logging

logger = logging.getLogger("poe")

def launch_client():
    from . import Client
    launch_subprocess(client.launch, name="poeClient", )

components.append(Component("Path of Exile Client",
                            func=launch_client,
                            component_type=Type.CLIENT,
                            icon="poe"))

icon_paths["poe"] = f"ap:{__name__}/icons/poeicon.png"