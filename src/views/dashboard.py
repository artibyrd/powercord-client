import flet as ft

from src.api_client import api


def view_dashboard(page: ft.Page, ext_manager) -> ft.View:
    page.title = "Dashboard"

    async def logout_click(e):
        await page.push_route("/settings")

    app_bar = ft.AppBar(
        leading=ft.Icon(ft.Icons.DASHBOARD),
        title=ft.Text("My Servers"),
        center_title=False,
        actions=[ft.IconButton(ft.Icons.SETTINGS, on_click=logout_click)],
    )

    grid = ft.GridView(
        expand=1,
        runs_count=5,
        max_extent=250,
        child_aspect_ratio=1.0,
        spacing=20,
        run_spacing=20,
    )

    loading_indicator = ft.ProgressRing(visible=True)
    error_text = ft.Text(color=ft.Colors.ERROR, visible=False)

    plugins_grid = ft.GridView(
        expand=1,
        runs_count=8,
        max_extent=200,
        child_aspect_ratio=1.0,
        spacing=20,
        run_spacing=20,
    )

    # Render loaded extensions
    for ext in ext_manager.loaded_extensions.values():
        nav_item = ext.get_navigation_item()
        if not nav_item:
            continue

        def go_to_ext_route(route):
            async def handler(e):
                await page.push_route(route)
            return handler

        # Try to find the first route of this extension
        # In a real app we might specify a 'main_route' in the base class
        ext_routes = list(ext.get_routes().keys())
        main_route = ext_routes[0] if ext_routes else "/"

        plugin_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(nav_item.icon, size=40, color=ft.Colors.PRIMARY),
                        ft.Text(nav_item.label, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                padding=20,
                ink=True,
                on_click=go_to_ext_route(main_route),
            ),
            elevation=2,
        )
        plugins_grid.controls.append(plugin_card)

    def go_to_server(guild_id):
        async def handler(e):
            await page.push_route(f"/server/{guild_id}")
        return handler

    def on_load():
        # Using api.get inside a Future to fetch data asynchronously
        pass

    import asyncio

    async def fetch_guilds():
        try:
            resp = await api.get("/client/guilds")
            guilds = resp.get("guilds", [])
            is_admin = resp.get("is_global_admin", False)

            if is_admin:
                async def go_admin(e):
                    await page.push_route("/admin")

                app_bar.actions.insert(
                    0,
                    ft.Button(
                        "Admin Panel",
                        icon=ft.Icons.SECURITY,
                        color=ft.Colors.ERROR,
                        on_click=go_admin,
                    ),
                )

            if not guilds:
                error_text.value = "You don't manage any servers."
                error_text.visible = True
            else:
                for g in guilds:
                    icon_url = (
                        f"https://cdn.discordapp.com/icons/{g['id']}/{g['icon']}.png"
                        if g.get("icon")
                        else "https://cdn.discordapp.com/embed/avatars/0.png"
                    )

                    card = ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Image(
                                        src=icon_url,
                                        width=80,
                                        height=80,
                                        border_radius=40,
                                        fit=ft.BoxFit.COVER,
                                    ),
                                    ft.Text(
                                        g["name"],
                                        weight=ft.FontWeight.BOLD,
                                        text_align=ft.TextAlign.CENTER,
                                        no_wrap=False,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Button("Manage", on_click=go_to_server(g["id"])),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=15,
                            ),
                            padding=20,
                            ink=True,
                            on_click=go_to_server(g["id"]),
                        ),
                        elevation=2,
                    )
                    grid.controls.append(card)
        except Exception as e:
            error_text.value = f"Failed to load servers: {str(e)}"
            error_text.visible = True
        finally:
            loading_indicator.visible = False
            page.update()

    # Schedule the fetch task when view is rendered
    asyncio.create_task(fetch_guilds())

    return ft.View(
        route="/",
        controls=[
            app_bar,
            ft.Container(
                content=ft.Column(
                    [
                        loading_indicator,
                        error_text,
                        ft.Text("My Servers", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.LEFT),
                        grid,
                        ft.Divider(),
                        ft.Text("Installed Plugins", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.LEFT),
                        plugins_grid
                        if plugins_grid.controls
                        else ft.Text("No client plugins installed.", color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                padding=20,
                expand=True,
            ),
        ],
    )
