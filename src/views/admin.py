import asyncio

import flet as ft

from src.api_client import api


def view_admin(page: ft.Page) -> ft.View:
    page.title = "Global Admin Configuration"

    async def back_click(e):
        await page.push_route("/")

    app_bar = ft.AppBar(
        leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=back_click),
        title=ft.Text("Global Architecture Configuration"),
        center_title=False,
    )

    loading_indicator = ft.ProgressRing(visible=True)
    error_text = ft.Text(color=ft.Colors.ERROR, visible=False)

    extensions_column = ft.Column(spacing=15, expand=True, scroll=ft.ScrollMode.AUTO)

    async def toggle_extension(ext_name, is_enabled):
        try:
            await api.post(
                "/client/guilds/0/config/toggle", data={"extension_name": ext_name, "enabled": is_enabled}
            )
            # Reload
            await fetch_config()
        except Exception as e:
            error_text.value = f"Failed to toggle: {str(e)}"
            error_text.visible = True
            page.update()

    async def fetch_config():
        loading_indicator.visible = True
        error_text.visible = False
        page.update()

        try:
            resp = await api.get("/client/guilds/0/config")
            config = resp.get("config", [])
    
            extensions_column.controls.clear()
    
            for ext in config:
                name = ext["name"]
                is_enabled = ext["is_enabled"]
                gadgets = ", ".join(ext["gadgets"])
    
                # We need a closure to capture the loop variables correctly
                def make_toggle(ext_name):
                    return lambda e: asyncio.create_task(toggle_extension(ext_name, e.control.value))
    
                switch = ft.Switch(value=is_enabled, on_change=make_toggle(name), active_color=ft.Colors.PRIMARY)
    
                card = ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(name.capitalize(), weight=ft.FontWeight.BOLD, size=18),
                                        ft.Text(f"Components: {gadgets}", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                                    ],
                                    expand=True,
                                ),
                                switch,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=15,
                    )
                )
                extensions_column.controls.append(card)
    
        except Exception as e:
            error_text.value = f"Failed to load global config: {str(e)}"
            error_text.visible = True
        finally:
            loading_indicator.visible = False
            page.update()

    asyncio.create_task(fetch_config())

    return ft.View(
        route="/admin",
        controls=[
            app_bar,
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Global System Extensions",
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Divider(),
                        loading_indicator,
                        error_text,
                        extensions_column,
                    ]
                ),
                padding=20,
                expand=True,
            ),
        ],
    )
