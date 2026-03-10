import argparse
import importlib
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from src.api_client import PowercordApiClient
from src.extensions.base import ClientExtension


class ClientExtensionManager:
    """
    Discovers, loads, and manages lifecycle for Flet Client Extensions.

    Also provides a CLI interface (invoked via `python -m src.extensions.manager`)
    for managing installations and dependencies via poetry.
    """

    def __init__(self, api_client: PowercordApiClient, extensions_dir: str = "src/extensions"):
        self.api = api_client
        self.extensions_dir = Path(extensions_dir)
        self.loaded_extensions: Dict[str, ClientExtension] = {}

        # Ensure the extensions directory exists
        self.extensions_dir.mkdir(parents=True, exist_ok=True)

        # Add the parent of src to sys.path so 'src.extensions.x' imports work
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
        module_path = f"src.extensions.{ext_name}.client_ext"

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

            logging.warning(f"Extension '{ext_name}' has 'client_ext.py' but no ClientExtension subclass found.")
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


# ── CLI & Installation Management ─────────────────────────────────────


_POETRY_CMD = shutil.which("poetry") or "poetry"
# Default path relative to this file
_EXTENSIONS_DIR = Path(__file__).resolve().parents[1] / "extensions"


def load_manifest(extension_path: Path) -> Dict[str, Any]:
    """Load and validate an `extension.json` manifest from `extension_path`."""
    manifest_file = extension_path / "extension.json"
    if not manifest_file.is_file():
        raise FileNotFoundError(f"No extension.json found in {extension_path}")

    with open(manifest_file, encoding="utf-8") as fh:
        manifest: Dict[str, Any] = json.load(fh)

    required_keys = ["name", "version", "description"]
    missing = [k for k in required_keys if k not in manifest]
    if missing:
        raise ValueError(f"extension.json missing required keys: {missing}")

    return manifest


def get_installed_extensions() -> List[Dict[str, Any]]:
    """Return a list of manifest dicts for every installed extension."""
    extensions: List[Dict[str, Any]] = []
    if not _EXTENSIONS_DIR.exists():
        return []

    for ext_path in sorted(_EXTENSIONS_DIR.iterdir()):
        if not ext_path.is_dir() or ext_path.name.startswith((".", "__")):
            continue
        try:
            manifest = load_manifest(ext_path)
            manifest["_path"] = str(ext_path)
            extensions.append(manifest)
        except (FileNotFoundError, ValueError):
            extensions.append(
                {
                    "name": ext_path.name,
                    "version": "unknown",
                    "description": "(no extension.json)",
                    "_path": str(ext_path),
                }
            )
    return extensions


def install_extension(source_path: str | Path) -> None:
    """Install an extension from source_path, copying files and adding dependencies."""
    source = Path(source_path).resolve()
    if not source.is_dir():
        print(f"Error: Source path '{source}' is not a directory.")
        sys.exit(1)

    _EXTENSIONS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        manifest = load_manifest(source)
    except FileNotFoundError:
        print(f"Error: {source} does not contain an extension.json manifest.")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing manifest: {e}")
        sys.exit(1)

    name = manifest["name"]
    dest = _EXTENSIONS_DIR / name

    is_reinstall = False
    old_deps = []

    if dest.exists():
        print(f"Extension '{name}' is already installed at {dest}. Reinstalling...")
        is_reinstall = True
        try:
            old_manifest = load_manifest(dest)
            old_deps = old_manifest.get("python_dependencies", [])
        except (FileNotFoundError, ValueError):
            pass

        # Remove existing directory (handling junctions/symlinks properly if developer created manually)
        if dest.is_symlink() or (hasattr(dest, "is_junction") and dest.is_junction()):  # type: ignore
            dest.unlink()
        else:
            shutil.rmtree(dest)

    print(f"Installing client extension '{name}' v{manifest['version']}...")

    # For development repositories, offer to create a junction/symlink.
    # Otherwise, copy the tree. Since we can't be interactive natively easily in all environments,
    # we'll default to copying standard files, unless instructed otherwise.
    # To keep it completely robust and match the backend, we copy exactly, ignoring .git.
    shutil.copytree(
        source,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", ".git", ".pytest_cache", "*.pyc", ".mypy_cache"),
    )
    print(f"  ✅ Copied files to {dest}")

    # Install Python dependencies
    deps = manifest.get("python_dependencies", [])
    if deps:
        if is_reinstall and set(deps) == set(old_deps):
            print("  📦 Skipped Python dependencies installation (no changes detected).")
        else:
            print(f"  📦 Installing {len(deps)} Python dependencies...")
            try:
                subprocess.run(  # noqa: S603
                    [_POETRY_CMD, "add", *deps],  # noqa: S607
                    check=True,
                    cwd=str(_EXTENSIONS_DIR.parent.parent),
                )
                print("  ✅ Dependencies installed.")
            except subprocess.CalledProcessError as exc:
                print(f"  ⚠️  Failed to install dependencies: {exc}")
                print("     You may need to run 'poetry add' manually.")

    print(f"\n✅ Client extension '{name}' installed successfully!")


def uninstall_extension(name: str) -> None:
    """Uninstall an extension by name and remove unneeded dependencies."""
    dest = _EXTENSIONS_DIR / name
    if not dest.exists():
        print(f"Error: Extension '{name}' is not installed.")
        sys.exit(1)

    try:
        manifest = load_manifest(dest)
    except (FileNotFoundError, ValueError):
        manifest = {"name": name, "python_dependencies": []}

    print(f"Uninstalling client extension '{name}'...")

    # Remove Python dependencies unique to this extension
    deps: list[str] = list(manifest.get("python_dependencies") or [])
    if deps:
        other_deps: set[str] = set()
        for ext in get_installed_extensions():
            if ext["name"] != name:
                for dep in ext.get("python_dependencies", []):
                    pkg_name = dep.split(">=")[0].split("<=")[0].split("==")[0].split("<")[0].split(">")[0].strip()
                    other_deps.add(pkg_name)

        unique_deps = []
        for dep in deps:
            pkg_name = dep.split(">=")[0].split("<=")[0].split("==")[0].split("<")[0].split(">")[0].strip()
            if pkg_name not in other_deps:
                unique_deps.append(pkg_name)

        if unique_deps:
            print(f"  📦 Removing {len(unique_deps)} unique dependencies...")
            try:
                subprocess.run(  # noqa: S603
                    [_POETRY_CMD, "remove", *unique_deps],  # noqa: S607
                    check=True,
                    cwd=str(_EXTENSIONS_DIR.parent.parent),
                )
                print("  ✅ Dependencies removed.")
            except subprocess.CalledProcessError as exc:
                print(f"  ⚠️  Failed to remove some dependencies: {exc}")
                print("     Note: On Windows, make sure Flet is closed so files aren't locked.")
                print("     Aborting uninstallation. Stop the client and try again.")
                sys.exit(1)

    # Remove extension directory (handling junctions/symlinks properly if developer created manually)
    if dest.is_symlink() or (hasattr(dest, "is_junction") and dest.is_junction()):  # type: ignore
        dest.unlink()
    else:
        shutil.rmtree(dest)
    print(f"  ✅ Removed {dest}")

    print(f"\n✅ Extension '{name}' uninstalled successfully!")


def list_extensions() -> None:
    extensions = get_installed_extensions()
    if not extensions:
        print("No client extensions installed.")
        return

    print(f"\n{'Name':<20} {'Version':<10} {'Description'}")
    print("─" * 70)
    for ext in extensions:
        desc = ext.get("description", "")
        if len(desc) > 37:
            desc = desc[:34] + "..."
        print(f"{ext['name']:<20} {ext.get('version', '?'):<10} {desc}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="src.extensions.manager",
        description="Powercord Client Extension Manager — install, uninstall, and list Flet extensions.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    install_parser = subparsers.add_parser("install", help="Install an extension from a local path")
    install_parser.add_argument("path", help="Path to the extension directory")

    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall an extension by name")
    uninstall_parser.add_argument("name", help="Extension name to uninstall")

    subparsers.add_parser("list", help="List all installed extensions")

    args = parser.parse_args()

    if args.command == "install":
        install_extension(args.path)
    elif args.command == "uninstall":
        uninstall_extension(args.name)
    elif args.command == "list":
        list_extensions()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
