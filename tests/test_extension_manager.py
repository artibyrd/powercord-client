import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.extensions.manager import ClientExtensionManager
from src.extensions.base import ClientExtension


class MockValidExtension(ClientExtension):
    def __init__(self, api_client):
        super().__init__(api_client)
        self.name = "mock_ext"
        self.display_name = "Mock Extension"

    def get_routes(self):
        return {"/mock_ext": lambda p: None}

    def get_navigation_item(self):
        return {"icon": "MOCK", "label": "Mock"}


@pytest.fixture
def api_client_mock():
    return MagicMock()


@pytest.fixture
def temp_plugins_dir(tmp_path):
    # Set up a fake plugins directory structure
    plugins_dir = tmp_path / "src" / "plugins"
    plugins_dir.mkdir(parents=True)
    
    # Valid plugin
    valid_plugin = plugins_dir / "valid_plugin"
    valid_plugin.mkdir()
    (valid_plugin / "client_ext.py").write_text(
        "from src.extensions.base import ClientExtension\\n"
        "class MyExt(ClientExtension):\\n"
        "    def __init__(self, api):\\n"
        "        super().__init__(api)\\n"
        "        self.name = 'valid'\\n"
        "        self.display_name = 'Valid Plugin'\\n"
        "    def get_routes(self): return {'/valid': lambda p: None}\\n"
        "    def get_navigation_item(self): return 'nav_item'\\n"
    )
    
    # Invalid plugin (no client_ext.py)
    invalid_plugin = plugins_dir / "invalid_plugin"
    invalid_plugin.mkdir()
    
    # Invalid plugin (client_ext.py but no ClientExtension subclass)
    no_class_plugin = plugins_dir / "no_class_plugin"
    no_class_plugin.mkdir()
    (no_class_plugin / "client_ext.py").write_text("def random_func(): pass")
    
    return plugins_dir


def test_manager_initialization(api_client_mock, tmp_path):
    extensions_dir = tmp_path / "plugins"
    manager = ClientExtensionManager(api_client_mock, str(extensions_dir))
    
    assert manager.api == api_client_mock
    assert manager.extensions_dir == extensions_dir
    assert extensions_dir.exists()
    assert str(extensions_dir.parent.parent.resolve()) in sys.path


def test_load_all_extensions(api_client_mock, temp_plugins_dir):
    manager = ClientExtensionManager(api_client_mock, str(temp_plugins_dir))
    
    # Patch import_module to return our fake module class or error based on the path
    original_import = __import__
    
    def mock_import(name, *args, **kwargs):
        if name == "src.plugins.valid_plugin.client_ext":
            mock_module = MagicMock()
            mock_module.MyExt = MockValidExtension
            return mock_module
        elif name == "src.plugins.no_class_plugin.client_ext":
            mock_module = MagicMock()
            return mock_module
        elif name == "src.plugins.invalid_plugin.client_ext":
            raise ModuleNotFoundError(f"No module named '{name}'")
        return original_import(name, *args, **kwargs)

    with patch("importlib.import_module", side_effect=mock_import):
        manager.load_all()

    # Only "valid_plugin" should be loaded into the dictionary 
    # (MockValidExtension sets its name to "mock_ext")
    assert len(manager.loaded_extensions) == 1
    assert "mock_ext" in manager.loaded_extensions
    assert isinstance(manager.loaded_extensions["mock_ext"], MockValidExtension)


def test_get_all_routes_and_nav_items(api_client_mock, tmp_path):
    manager = ClientExtensionManager(api_client_mock, str(tmp_path))
    
    # Inject a couple of mock extensions directly
    ext1 = MockValidExtension(api_client_mock)
    ext1.name = "ext1"
    
    ext2 = MockValidExtension(api_client_mock)
    ext2.name = "ext2"
    ext2.get_routes = lambda: {"/ext2": lambda p: None}
    ext2.get_navigation_item = lambda: "ext2_nav"
    
    manager.loaded_extensions = {"ext1": ext1, "ext2": ext2}
    
    routes = manager.get_all_routes()
    assert "/mock_ext" in routes
    assert "/ext2" in routes
    
    nav_items = manager.get_navigation_items()
    assert len(nav_items) == 2
    assert {"icon": "MOCK", "label": "Mock"} in nav_items
    assert "ext2_nav" in nav_items
