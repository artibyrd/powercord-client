# Powercord Client Extension Development

Powercord is designed to be highly modular. Just as the backend supports adding Discord Cogs and FastAPI endpoints, the `powercord-client` allows you to inject fully native Flet views into the client application.

This is especially helpful for complex functionalities like bulk-uploading MIDI files, managing files, viewing real-time graphs, or executing specialized tools that exceed simple Web browser capabilities.

## The Plugin Ecosystem

All client plugins reside in the `src/plugins/` directory.

To create a new extension:
1. Create a new folder inside `src/plugins/` (e.g., `my_extension`).
2. Create a file named `client_ext.py` inside that folder.

```text
src/
└── plugins/
    └── my_extension/
        └── client_ext.py
```

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
