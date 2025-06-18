import asyncio
import colorama
import Utils
from CommonClient import ClientCommandProcessor, CommonContext, server_loop, gui_enabled


class PathOfExileCommandProcessor(ClientCommandProcessor):


    def _cmd_force(self, difficulty: str = "") -> bool:
        self.unlock_all_available_items()



class PathOfExileContext(CommonContext):
    game = "Path of Exile"
    command_processor = PathOfExileCommandProcessor
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

    def on_package(self, cmd: str, args: dict):
        if cmd == 'Connected':
            pass
        if cmd == "ReceivedItems":
            pass
        super().on_package(cmd, args)


    def run_gui(self) -> None:
        #from .ClientGui import start_gui # custom UI
        #start_gui(self)
        super().run_gui()






async def main():
    Utils.init_logging("PathOfExileContext", exception_logger="Client")

    ctx = PathOfExileContext(None, None)


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
