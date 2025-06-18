from kvui import GameManager, HoverBehavior, ServerToolTip, KivyJSONtoTextParser
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivymd.uix.tooltip import MDTooltip
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty

class PoeManager(GameManager):
    logging_pairs = [
        ("Client", "Archipelago"),
        ("poe", "poe"),
    ]
    base_title = "Archipelago Path of Exile Client"
    ctx: PathOfExileClient

    def __init__(self, ctx) -> None:
        super().__init__(ctx)
        self.json_to_kivy_parser = SC2JSONtoKivyParser(ctx)

    def clear_tooltip(self) -> None:
        if self.ctx.current_tooltip:
            App.get_running_app().root.remove_widget(self.ctx.current_tooltip)

        self.ctx.current_tooltip = None

    def build(self):
        container = super().build()

        panel = self.add_client_tab("GGG auth", authTab())
        self.campaign_panel = MultiCampaignLayout()
        panel.content.add_widget(self.campaign_panel)

        Clock.schedule_interval(self.build_mission_table, 0.5)

        return container


def start_gui(context: PathOfExileClient):
    context.ui = SC2Manager(context)
    context.ui_task = asyncio.create_task(context.ui.async_run(), name="UI")
    import pkgutil
    data = pkgutil.get_data(SC2World.__module__, "Starcraft2.kv").decode()
    Builder.load_string(data)
