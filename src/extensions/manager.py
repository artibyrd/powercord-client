import importlib
import logging
import sys
from pathlib import Path
from typing import Dict, List

from src.api_client import PowercordApiClient
from src.extensions.base import ClientExtension


class ClientExtensionManager:
    """
    Discovers, loads, and manages lifecycle for Flet Client Extensions.
    """

    def __init__(self, api_client: PowercordApiClient, extensions_dir: str = "src/plugins"):
        self.api = api_client
        self.extensions_dir = Path(extensions_dir)
        self.loaded_extensions: Dict[str, ClientExtension] = {}

        # Ensure the plugins directory exists
        self.extensions_dir.mkdir(parents=True, exist_ok=True)

        # Add the parent of src to sys.path so 'src.plugins.x' imports work
        project_root = self.extensions_dir.parent.parent.resolve()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

    def load_all(self):
        """Scans the extensions directory and loads all valid extensions."""
        self.loaded_extensions.clear()

        if not self.extensions_dir.exists():
            return

        for ext_folder in self.extensions_dir.iterdir():
            if ext_folder.is_dir() and not ext_folder.name.startswith("__"):
                self._load_extension(ext_folder.name)

    def _load_extension(self, ext_name: str):
        """Attempts to load a single extension by treating it as a python module."""
        module_path = f"src.plugins.{ext_name}.client_ext"

        try:
            module = importlib.import_module(module_path)
            # Find any subclass of ClientExtension in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, ClientExtension) and attr is not ClientExtension:
                    # Instantiate it
                    instance = attr(self.api)
                    self.loaded_extensions[instance.name] = instance
                    logging.info(f"Loaded client extension: {instance.name} ({instance.display_name})")
                    return

            logging.warning(f"Plugin '{ext_name}' has 'client_ext.py' but no ClientExtension subclass found.")
        except ModuleNotFoundError:
            # It's fine if a directory doesn't have a client_ext.py
            pass
        except Exception as e:
            logging.error(f"Failed to load client extension '{ext_name}': {e}", exc_info=True)

    def get_all_routes(self) -> Dict:
        """Collects all routes from all loaded extensions."""
        all_routes = {}
        for ext in self.loaded_extensions.values():
            try:
                all_routes.update(ext.get_routes())
            except Exception as e:
                logging.error(f"Error getting routes from {ext.name}: {e}")
        return all_routes

    def get_navigation_items(self) -> List:
        """Collects all navigation items from loaded extensions."""
        items = []
        for ext in self.loaded_extensions.values():
            item = ext.get_navigation_item()
            if item:
                items.append(item)
        return items
