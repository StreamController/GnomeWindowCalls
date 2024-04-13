# Import StreamController modules
from GtkHelper.GtkHelper import BetterPreferencesGroup, AttributeRow
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

# Import python modules
import os

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

import globals as gl

class Resize(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)
        
        self.HAS_CONFIGURATION = True
        
    def on_ready(self) -> None:
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "resize.png")
        self.set_media(media_path=icon_path, size=0.75)
        
    def get_config_rows(self) -> list:
        self.wm_row = Adw.EntryRow(title=self.plugin_base.lm.get("actions.wm_class_regex_entry.title"), text=".*")
        self.title_row = Adw.EntryRow(title=self.plugin_base.lm.get("actions.title_regex_entry.title"), text=".*")

        self.width_spinner = Adw.SpinRow.new_with_range(0, 8000, 1)
        self.height_spinner = Adw.SpinRow.new_with_range(0, 8000, 1)

        self.width_spinner.set_title(self.plugin_base.lm.get("actions.width.title"))
        self.height_spinner.set_title(self.plugin_base.lm.get("actions.height.title"))

        self.load_defaults()

        self.wm_row.connect("changed", self.on_row_changed)
        self.title_row.connect("changed", self.on_row_changed)
        self.width_spinner.connect("changed", self.on_row_changed)
        self.height_spinner.connect("changed", self.on_row_changed)

        return [self.wm_row, self.title_row, self.width_spinner, self.height_spinner]
    
    def load_defaults(self) -> None:
        settings = self.get_settings()
        self.wm_row.set_text(settings.get("wm_class", ".*"))
        self.title_row.set_text(settings.get("title", ".*"))
        self.width_spinner.set_value(settings.get("size", {}).get("width", 0))
        self.height_spinner.set_value(settings.get("size", {}).get("height", 0))
    
    def on_row_changed(self, *args) -> None:
        settings = self.get_settings()
        settings["wm_class"] = self.wm_row.get_text()
        settings["title"] = self.title_row.get_text()
        settings.setdefault("size", {})
        settings["size"]["width"] = int(self.width_spinner.get_value())
        settings["size"]["height"] = int(self.height_spinner.get_value())
        self.set_settings(settings)

    def on_key_down(self):
        settings = self.get_settings()
        wm = settings.get("wm_class", "")
        title = settings.get("title", "")
        width = settings.get("size", {}).get("width")
        height = settings.get("size", {}).get("height")

        if None in [wm, title, width, height]:
            return
        
        matching_windows = self.plugin_base.window_manager.find_windows_by_class_and_title(wm, title)
        for window_id in matching_windows:
            self.plugin_base.window_manager.resize_window_to(window_id, width, height)