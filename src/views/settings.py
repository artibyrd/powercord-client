import flet as ft

from src.api_client import api


def view_settings(page: ft.Page) -> ft.View:
    page.title = "Settings"

    async def logout_click(e):
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            await page.shared_preferences.remove("api_key")
            await page.shared_preferences.remove("base_url")
        await api.close()
        # Reset config
        api.configure("", "")
        await page.push_route("/login")

    async def back_click(e):
        await page.push_route("/")

    app_bar = ft.AppBar(
        leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=back_click),
        title=ft.Text("Settings"),
        center_title=False,
    )

    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # We can't await this synchronously here, so we will initialize a blank connected server state
        # A more robust fix will load this async via on_load event
        url = "Connected System"

    server_info = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.CLOUD_DONE, color=ft.Colors.GREEN),
                        title=ft.Text("Connected Server"),
                        subtitle=ft.Text(url),
                    ),
                    ft.Row(
                        [
                            ft.Button(
                                "Disconnect & Logout",
                                icon=ft.Icons.LOGOUT,
                                color=ft.Colors.ERROR,
                                on_click=logout_click,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ]
            ),
            padding=10,
        ),
        margin=ft.margin.all(10),
    )

    return ft.View(route="/settings", controls=[app_bar, server_info])
