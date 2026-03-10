# Powercord Client Extension Development

Powercord is designed to be highly modular. Just as the backend supports adding Discord Cogs and FastAPI endpoints, the `powercord-client` allows you to inject fully native Flet views into the client application.

This is especially helpful for complex functionalities like bulk-uploading MIDI files, managing files, viewing real-time graphs, or executing specialized tools that exceed simple Web browser capabilities.

## Extension Architecture

All client extensions reside in the `src/extensions/` directory.

An extension requires two core files:
1. `extension.json` - A manifest declaring the extension name, version, and pip dependencies.
2. `client_ext.py` - The main python entry point containing your Flet code.

Below is the required folder structure of an extension repository:

```text
my_extension/
├── extension.json
├── __init__.py
└── client_ext.py
```

### The Extension Manifest

Your `extension.json` file is required for the installation manager to process your extension.

```json
{
    "name": "my_extension",
    "version": "1.0.0",
    "description": "A custom Flet tool",
    "python_dependencies": ["pandas>=2.0"]
}
```

### Installing and Uninstalling

Client extensions are managed using the Powercord Client's Justfile CLI.

**To install an extension from a local directory:**
```bash
just ext-install /path/to/my_extension
```
This command will copy the extension files into the `src/extensions/` directory and automatically execute `poetry add` to install any packages defined in `python_dependencies`.

**Graceful Reinstalls for Development:**
During development, you can repeatedly run `just ext-install /path/to/my_extension` to overwrite your installed extension with your newest code. The CLI will safely wipe the existing destination and intelligently check the manifests. If your `python_dependencies` haven't changed, it will completely skip the lengthy `poetry add` resolution step, deploying your updates instantly.

**To uninstall an extension:**
```bash
just ext-uninstall my_extension
```
This command safely removes the extension from `src/extensions/` and automatically strips away any unique `python_dependencies` using `poetry remove`.

## Creating `ClientExtension`

Your `client_ext.py` MUST contain a class that inherits from `src.extensions.base.ClientExtension`. The `ClientExtensionManager` will automatically discover it on startup and load it.

```python
import flet as ft
from src.extensions.base import ClientExtension

class MyCustomExtension(ClientExtension):
    name = "my_custom_ext"
    display_name = "Custom Tool"
    icon = ft.Icons.BUILD

    def get_navigation_item(self):
        """
        Defines how the extension appears on the Dashboard 'Plugins' section.
        """
        return ft.NavigationRailDestination(
            icon=self.icon,
            selected_icon=self.icon,
            label=self.display_name,
        )

    def get_routes(self):
        """
        Returns a dictionary mapping route URLs to Flet View generators.
        """
        return {
            "/ext/my_tool": self.view_main,
        }

    def view_main(self, page: ft.Page) -> ft.View:
        page.title = self.display_name

        def go_back(e):
            page.go("/")

        app_bar = ft.AppBar(
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back),
            title=ft.Text(self.display_name),
            center_title=False,
        )

        return ft.View(
            "/ext/my_tool",
            controls=[
                app_bar,
                ft.Text("Welcome to the custom extension!")
            ]
        )
```

## Using the API Client

Your extension instance is initialized with a reference to the main Powercord API client (`self.api`).
You can use this to make authenticated network calls to the backend.

```python
    async def fetch_data(self):
        try:
            # Hit your backend extension's custom FastAPI route
            result = await self.api.get("/api/v1/my_tool/data")
            print(result)
        except Exception as e:
            print(f"Error: {e}")
```

The api methods natively handle JSON serialization, `Bearer` token injection, and error raising for `4xx` and `5xx` responses.
