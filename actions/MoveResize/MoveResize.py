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

class MoveResize(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)
        
    def on_ready(self) -> None:
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "move-resize.png")
        self.set_media(media_path=icon_path, size=0.75)
        
    def get_config_rows(self) -> list:
        self.wm_row = Adw.EntryRow(title=self.plugin_base.lm.get("actions.wm_class_regex_entry.title"), text=".*")
        self.title_row = Adw.EntryRow(title=self.plugin_base.lm.get("actions.title_regex_entry.title"), text=".*")

        self.x_spinner = Adw.SpinRow.new_with_range(0, 8000, 1)
        self.y_spinner = Adw.SpinRow.new_with_range(0, 8000, 1)
        self.width_spinner = Adw.SpinRow.new_with_range(0, 8000, 1)
        self.height_spinner = Adw.SpinRow.new_with_range(0, 8000, 1)

        self.width_spinner.set_title(self.plugin_base.lm.get("actions.width.title"))
        self.height_spinner.set_title(self.plugin_base.lm.get("actions.height.title"))
        self.x_spinner.set_title(self.plugin_base.lm.get("actions.x_position.title"))
        self.y_spinner.set_title(self.plugin_base.lm.get("actions.y_position.title"))

        self.load_defaults()

        self.wm_row.connect("changed", self.on_row_changed)
        self.title_row.connect("changed", self.on_row_changed)
        self.x_spinner.connect("changed", self.on_row_changed)
        self.y_spinner.connect("changed", self.on_row_changed)
        self.width_spinner.connect("changed", self.on_row_changed)
        self.height_spinner.connect("changed", self.on_row_changed)

        return [self.wm_row, self.title_row, self.x_spinner, self.y_spinner, self.width_spinner, self.height_spinner]
    
    def load_defaults(self) -> None:
        settings = self.get_settings()
        self.wm_row.set_text(settings.get("wm_class", ".*"))
        self.title_row.set_text(settings.get("title", ".*"))
        self.x_spinner.set_value(settings.get("position", {}).get("x", 0))
        self.y_spinner.set_value(settings.get("position", {}).get("y", 0))
        self.width_spinner.set_value(settings.get("size", {}).get("width", 0))
        self.height_spinner.set_value(settings.get("size", {}).get("height", 0))
    
    def on_row_changed(self, *args) -> None:
        settings = self.get_settings()
        settings["wm_class"] = self.wm_row.get_text()
        settings["title"] = self.title_row.get_text()
        settings.setdefault("position", {})
        settings["position"]["x"] = int(self.x_spinner.get_value())
        settings["position"]["y"] = int(self.y_spinner.get_value())
        settings.setdefault("size", {})
        settings["size"]["width"] = int(self.width_spinner.get_value())
        settings["size"]["height"] = int(self.height_spinner.get_value())
        self.set_settings(settings)

    def on_key_down(self):
        settings = self.get_settings()
        wm = settings.get("wm_class", "")
        title = settings.get("title", "")
        x = settings.get("position", {}).get("x")
        y = settings.get("position", {}).get("y")
        width = settings.get("size", {}).get("width")
        height = settings.get("size", {}).get("height")

        if None in [wm, title, x, y, width, height]:
            return
        
        matching_windows = self.plugin_base.window_manager.find_windows_by_class_and_title(wm, title)
        for window_id in matching_windows:
            print("move resize")
            self.plugin_base.window_manager.move_resize_window(window_id, x, y, width, height)