from CommonClient import CommonContext, ClientCommandProcessor, logger
# Python standard libraries
import asyncio
import json
import logging
import os
import subprocess
import sys

from asyncio import Task
from datetime import datetime
from logging import Logger
from typing import Awaitable

# Misc imports
import colorama
import pymem

from pymem.exception import ProcessNotFound

# Archipelago imports
import ModuleUpdate
import Utils

from CommonClient import ClientCommandProcessor, CommonContext, server_loop, gui_enabled
from NetUtils import ClientStatus


class UnlockerContext(ClientCommandProcessor):

    unlocker_client = {}

    def _cmd_force(self, difficulty: str = "") -> bool:
        self.unlock_all_available_items()

    def unlock_all_available_items(self):
            #unlock all locations we have an item for
            for item in self.ctx.items_received:
                self.ctx.check_locations(item.item)

class UnlockerClient(CommonContext):
    game = "Unlocker"
    command_processor = UnlockerContext
    items_handling = 0b111
    __debug = True  # Enable debug mode for Unlocker client

    item_name_to_unlocker_location = {} # remove this I think?
    required_for_finish_player_location_table = {}
    item_id_to_location_name = {}

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super(TextContext, self).server_auth(password_requested)
        await self.get_username()
        await self.send_connect(game="Unlocker")

    __current_loop = None
    def on_package(self, cmd: str, args: dict):
        # Handle custom server commands for Unlocker
        if self.__current_loop is None:
            try:
                self.__current_loop = asyncio.get_event_loop()
            except RuntimeError:
                pass # ??

        if cmd == 'Connected':
            if __debug__:
                logger.debug(f"Connected to Unlocker server with args: {args}")
            slot_data = args.get('slot_data', None)
            if slot_data:
                if __debug__:
                    logger.debug(f"Received slot data: {slot_data}")
                self.item_name_to_unlocker_location = slot_data.get('item_name_to_unlocker_location')
                self.required_for_finish_player_location_table = slot_data.get('player_location_table')
                self.item_id_to_location_name = slot_data.get('item_id_to_location_name')
            logger.info(f"Connected to Unlocker server with slot data: {slot_data}")
        if cmd == "ReceivedItems":
            if __debug__:
                logger.debug(f"Received items: {args['items']}")
            #self.on_items_received(args["items"])

            if self.__current_loop is not None:
                if __debug__:
                    logger.debug("Running unlock_all_available_items in event loop")
                self.__current_loop.create_task(self.unlock_all_available_items())
            else:
                asyncio.run(self.unlock_all_available_items())

        super().on_package(cmd, args)



    async def unlock_all_available_items(self):
            #unlock all locations we have an item for
            if __debug__:
                logger.debug(f"Unlocking all available items; game {self.game}; items received: {self.items_received}")

            items = [obj.item for obj in self.items_received]
            await self.check_locations(items)
            # check if we have all items in required_for_finish_player_location_table
            if __debug__:
                logger.debug(f"Checking locations for items: {items}")
            # Check if all required items are received
            required_items = set(self.required_for_finish_player_location_table.values())
            received_items = set(obj.item for obj in self.items_received)
            if required_items.issubset(received_items):
                if __debug__:
                    logger.debug("All required items for finish are received.")
                self.finished_game = True

            else:
                missing = required_items - received_items
                if __debug__:
                    logger.debug(f"Missing required items for finish: {missing}")





async def main():
    Utils.init_logging("UnlockerClient", exception_logger="Client")

    ctx = UnlockerClient(None, None)


    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    await ctx.exit_event.wait()
    await ctx.shutdown()


def launch():
    # use colorama to display colored text highlighting
    colorama.just_fix_windows_console()
    asyncio.run(main())
    colorama.deinit()
