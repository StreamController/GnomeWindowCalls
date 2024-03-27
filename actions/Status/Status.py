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
from gi.repository import Gtk, Adw, GLib

import globals as gl

class Status(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)
        
    def on_ready(self) -> None:
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "info.png")
        self.set_media(media_path=icon_path, size=0.75)
        
    def on_key_down(self) -> None:
        if not gl.app.main_win.get_visible():
            gl.app.on_reopen()

        GLib.idle_add(gl.app.main_win.leftArea.deck_stack.focus_controller, self.deck_controller)
        GLib.idle_add(gl.app.main_win.sidebar.action_configurator.load_for_action, self, self.get_own_action_index())
        GLib.idle_add(gl.app.main_win.sidebar.show_action_configurator)
    
    def get_config_rows(self) -> list:
        self.wm_row = Adw.EntryRow(title=self.plugin_base.lm.get("actions.wm_class_regex_entry.title"), text=".*")
        self.title_row = Adw.EntryRow(title=self.plugin_base.lm.get("actions.title_regex_entry.title"), text=".*")

        self.load_defaults()

        self.wm_row.connect("changed", self.on_row_changed)
        self.title_row.connect("changed", self.on_row_changed)

        return [self.wm_row, self.title_row]
    
    def load_defaults(self) -> None:
        settings = self.get_settings()
        self.wm_row.set_text(settings.get("wm_class", ".*"))
        self.title_row.set_text(settings.get("title", ".*"))
    
    def on_row_changed(self, *args) -> None:
        self.update_box()

        settings = self.get_settings()
        settings["wm_class"] = self.wm_row.get_text()
        settings["title"] = self.title_row.get_text()
        self.set_settings(settings)


    def get_custom_config_area(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, margin_start=4, margin_end=4)

        self.title = Gtk.Label(label=self.plugin_base.lm.get("actions.status.matching_windows"), css_classes=["page-header"], xalign=0, margin_top=10, margin_bottom=10)
        self.main_box.append(self.title)

        self.preferences_group = BetterPreferencesGroup()
        self.main_box.append(self.preferences_group)
        self.update_box()
        return self.main_box
    
    def update_box(self):
        wm_regex = self.wm_row.get_text()
        title_regex = self.title_row.get_text()


        self.preferences_group.clear()
        window_ids = self.plugin_base.window_manager.find_windows_by_class_and_title(wm_regex, title_regex)
        for window_id in window_ids:
            details = self.plugin_base.window_manager.get_window_details(window_id)
            expander = self.generate_expander_from_details(details=details)
            self.preferences_group.add(expander)

    def generate_expander_from_details(self, details: dict) -> Adw.ExpanderRow:
        expander = Adw.ExpanderRow(title=details["title"], subtitle=details["wm_class"])

        expander.add_row(AttributeRow(title=self.plugin_base.lm.get("actions.status.wm_class"), attr=details["wm_class"]))
        expander.add_row(AttributeRow(title=self.plugin_base.lm.get("actions.x_position.title"), attr=details["x"]))
        expander.add_row(AttributeRow(title=self.plugin_base.lm.get("actions.y_position.title"), attr=details["y"]))
        expander.add_row(AttributeRow(title=self.plugin_base.lm.get("actions.width.title"), attr=details["width"]))
        expander.add_row(AttributeRow(title=self.plugin_base.lm.get("actions.height.title"), attr=details["height"]))

        return expander