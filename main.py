# Import StreamController modules
import time
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from .actions.Move.Move import Move
from .actions.Status.Status import Status
from .actions.Resize.Resize import Resize
from .actions.MoveResize.MoveResize import MoveResize

# Import python modules
import dbus
from loguru import logger as log
import json
import re

class GnomeWindowCalls(PluginBase):
    def __init__(self):
        super().__init__()

        self.lm = self.locale_manager

        ## Register actions
        self.simple_action_holder = ActionHolder(
            plugin_base = self,
            action_base = Move,
            action_id = "com_core447_GnomeWindowCalls::Move",
            action_name = self.lm.get("actions.move.name"),
        )
        self.add_action_holder(self.simple_action_holder)

        self.status_action_holder = ActionHolder(
            plugin_base = self,
            action_base = Status,
            action_id = "com_core447_GnomeWindowCalls::Status",
            action_name = self.lm.get("actions.status.name"),
        )
        self.add_action_holder(self.status_action_holder)

        self.resize_action_holder = ActionHolder(
            plugin_base = self,
            action_base = Resize,
            action_id = "com_core447_GnomeWindowCalls::Resize",
            action_name = self.lm.get("actions.resize.name"),
        )
        self.add_action_holder(self.resize_action_holder)

        self.move_resize_action_holder = ActionHolder(
            plugin_base = self,
            action_base = MoveResize,
            action_id = "com_core447_GnomeWindowCalls::MoveResize",
            action_name = self.lm.get("actions.move_resize.name"),
        )
        self.add_action_holder(self.move_resize_action_holder)

        # Register plugin
        self.register(
            plugin_name = self.lm.get("plugin.name"),
            github_repo = "https://github.com/StreamController/GnomeWindowCalls",
            plugin_version = "1.0.0",
            app_version = "1.2.0-alpha"
        )

        self.bus = dbus.SessionBus()
        self.extension_manager = ExtensionManager(self.bus)
        self.handle_extension_installation()
        self.window_manager = WindowManager(self.bus)

    def handle_extension_installation(self):
        uuid = "window-calls@domandoman.xyz"

        if uuid in self.extension_manager.get_installed_extensions():
            log.info(f"Extension {uuid} is already installed")
        else:
            self.extension_manager.install_extension(uuid)

        
class ExtensionManager:
    def __init__(self, bus: dbus.SessionBus):
        self.bus = bus
        self.gnome_shell_extensions: dbus.Interface = None
        self.interface: dbus.Interface = None
        try:
            self.gnome_shell_extensions = self.bus.get_object("org.gnome.Shell", "/org/gnome/Shell")
            self.interface = dbus.Interface(self.gnome_shell_extensions, "org.gnome.Shell.Extensions")
        except dbus.exceptions.DBusException as e:
            log.error(f"Failed to get gnome shell extensions. Error: {e}")

    def get_installed_extensions(self) -> list[str]:
        extensions: list[str] = []
        if not self.get_is_connected(): return extensions

        for extension in self.interface.ListExtensions():
            extensions.append(extension)
        return extensions

    def install_extension(self, uuid: str) -> bool:
        if not self.get_is_connected(): return False
        response = self.interface.InstallRemoteExtension(uuid)
        if response == "cancelled":
            return False
        if response == "successful":
            return True
        
    def get_is_connected(self) -> bool:
        return None not in [self.gnome_shell_extensions, self.interface]
        
class WindowManager:
    def __init__(self, bus):
        self.bus = bus
        self.proxy = None
        self.interface = None
        try:
            self.proxy = bus.get_object("org.gnome.Shell", "/org/gnome/Shell/Extensions/Windows")
            self.interface = dbus.Interface(self.proxy, "org.gnome.Shell.Extensions.Windows")
        except dbus.exceptions.DBusException:
            pass

    def get_all_windows(self) -> list[dict]:
        if not self.get_is_connected(): return []
        return json.loads(self.interface.List())
    
    def get_window_details(self, id: int) -> dict:
        if not self.get_is_connected(): return {}
        return json.loads(self.interface.Details(str(id)))
    
    def move_window_to(self, id: int, x: int, y: int):
        if not self.get_is_connected(): return
        self.interface.Move(str(id), x, y)

    def move_resize_window(self, id: int, x: int, y: int, width: int, height: int):
        if not self.get_is_connected(): return
        self.interface.MoveResize(str(id), x, y, width, height)
        return
        self.move_window_to(id, x, y)
        time.sleep(0.05)
        self.resize_window_to(id, width, height)
        time.sleep(0.05)
        self.move_window_to(id, x, y)

    def resize_window_to(self, id: int, width: int, height: int):
        if not self.get_is_connected(): return
        self.interface.Resize(str(id), width, height)

    def maximize_window(self, id: int) -> None:
        if not self.get_is_connected(): return
        self.interface.Maximize(str(id))

    def minimize_window(self, id: int) -> None:
        if not self.get_is_connected(): return
        self.interface.Minimize(str(id))

    def unmaximize_window(self, id: int) -> None:
        if not self.get_is_connected(): return
        self.interface.Unmaximize(str(id))

    def unminimize_window(self, id: int) -> None:
        if not self.get_is_connected(): return
        self.interface.Unminimize(str(id))

    def activate_window(self, id: int) -> None:
        if not self.get_is_connected(): return
        self.interface.Activate(str(id))

    def close_window(self, id: int) -> None:
        if not self.get_is_connected(): return
        self.interface.Close(str(id))

    def get_title(self, id: int) -> str:
        if not self.get_is_connected(): return ""
        return self.interface.GetTitle(str(id))
    
    def get_all_wm_classes(self) -> list[str]:
        if not self.get_is_connected(): return []
        classes: str = []
        for window in self.get_all_windows():
            classes.append(window["wm_class"])
        return classes
    
    def get_all_titles(self) -> list[str]:
        if not self.get_is_connected(): return []
        titles: str = []
        for window in self.get_all_windows():
            title = self.get_title(window["id"])
            titles.append(str(title))
        return titles
    
    def find_windows_by_class_and_title(self, wm_class_pattern: str, title_pattern: str) -> list[int]:
        if not self.get_is_connected(): return []
        matching_window_ids = []
        all_windows = self.get_all_windows()

        for window in all_windows:
            try:
                if window.get("wm_class", "") == None:
                    continue
                wm_class_match = re.search(wm_class_pattern, window.get("wm_class", ""), re.IGNORECASE)
                title_match = re.search(title_pattern, self.get_title(window["id"]), re.IGNORECASE)
            except re.error:
                return []

            if wm_class_match and title_match:
                matching_window_ids.append(window["id"])

        return matching_window_ids
    
    def get_is_connected(self) -> bool:
        return None not in [self.proxy, self.interface]