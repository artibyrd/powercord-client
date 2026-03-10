import sys
from pathlib import Path

# Add project root to sys.path to allow 'src' imports when running via 'flet run src/app.py'
sys.path.insert(0, str(Path(__file__).parent.parent))

import flet as ft

from src.api_client import api
from src.extensions.manager import ClientExtensionManager


async def main(page: ft.Page):
    page.title = "Powercord Client"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    # Initialize Extension Manager
    ext_manager = ClientExtensionManager(api)
    ext_manager.load_all()

    # Shared views dictionary
    views = {}

    def get_core_routes(manager):
        from src.views.admin import view_admin
        from src.views.dashboard import view_dashboard
        from src.views.login import view_login
        from src.views.settings import view_settings

        def dashboard_handler(p):
            return view_dashboard(p, manager)

        return {"/login": view_login, "/settings": view_settings, "/admin": view_admin, "/": dashboard_handler}

    # Load all routes
    views.update(get_core_routes(ext_manager))
    views.update(ext_manager.get_all_routes())

    async def route_change(route_event):
        try:
            page.views.clear()

            # Determine if we have a valid session token
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                saved_token = await page.shared_preferences.get("api_key")
                saved_url = await page.shared_preferences.get("base_url")
            if saved_url and saved_token and not api.base_url:
                api.configure(saved_url, saved_token)

            # Basic Auth Guard
            if not saved_token and page.route != "/login":
                await page.push_route("/login")
                return

            # Handle dynamic routes (like /server/12345)
            # Check exact matches first
            route_handler = views.get(page.route)

            if not route_handler:
                if page.route.startswith("/server/"):
                    from src.views.server import view_server

                    guild_id = page.route.split("/")[-1]

                    def server_handler(p):
                        return view_server(p, guild_id)

                    # Inject a lazy evaluator
                    route_handler = server_handler

            if route_handler:
                page.views.append(route_handler(page))
            else:
                # Fallback to home/dashboard if route not found
                if saved_token:
                    if "/" in views:
                        page.views.append(views["/"](page))
                    else:
                        page.views.append(ft.View("/", [ft.Text("Dashboard Placeholder")]))
                else:
                    page.views.append(views["/login"](page))

            page.update()
        except Exception as e:
            print(f"ROUTE CHANGE EXCEPTION: {str(e)}", flush=True)

    async def view_pop(view_event):
        page.views.pop()
        top_view = page.views[-1]
        await page.push_route(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # Start app by evaluating the current route
    await route_change(None)


if __name__ == "__main__":
    ft.run(main)
