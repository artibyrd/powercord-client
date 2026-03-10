import flet as ft

from src.api_client import ApiError, api


def view_login(page: ft.Page) -> ft.View:
    page.title = "Connect to Powercord"

    # Input Fields
    server_url_field = ft.TextField(
        label="Powercord Server URL",
        hint_text="https://powercord.example.com",
        prefix_icon=ft.Icons.CLOUD,
        expand=True,
    )

    api_key_field = ft.TextField(
        label="Client API Key",
        hint_text="pc_...",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.VPN_KEY,
        expand=True,
    )

    error_text = ft.Text(color=ft.Colors.ERROR, visible=False)
    progress_ring = ft.ProgressRing(visible=False, width=20, height=20)

    # Pre-fill if we have existing storage (this works in sync via page.client_storage but we might need a blank default if we can't await it here)

    async def on_connect_click(e):
        url = server_url_field.value.strip()
        key = api_key_field.value.strip()

        if not url or not key:
            error_text.value = "Both Server URL and API Key are required."
            error_text.visible = True
            page.update()
            return

        error_text.visible = False
        progress_ring.visible = True
        btn_connect.disabled = True
        page.update()

        # Attempt to configure and test the connection
        api.configure(url, key)

        try:
            # Note: We need a lightweight endpoint on the server to test auth.
            # Assuming `/api/v1/users/@me` or we'll add one in Phase 3.5.
            # For now, hit a public endpoint to see if the server exists
            # and let the later dashboard fetch prove the token works.
            # Let's try to hit the root health API or just trust it and go to dashboard.

            # Validate the connection and API Key identity
            await api.get("/client/guilds")

            # If we get here, connection didn't immediately fail.
            # Store credentials securely (suppressing deprecation warnings internally)
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                await page.shared_preferences.set("base_url", url)
                await page.shared_preferences.set("api_key", key)

            await page.push_route("/")  # Redirect to dashboard

        except ApiError as err:
            error_text.value = f"Connection failed: {str(err)}"
            error_text.visible = True
        except Exception as err:
            error_text.value = f"Unexpected error: {str(err)}"
            error_text.visible = True
        finally:
            progress_ring.visible = False
            btn_connect.disabled = False
            page.update()

    btn_connect = ft.Button(
        "Connect",
        icon=ft.Icons.LOGIN,
        on_click=on_connect_click,
        expand=True,
    )

    instructions = ft.Column(
        controls=[
            ft.Text("Welcome to Powercord Client", size=24, weight=ft.FontWeight.BOLD),
            ft.Text(
                "To connect, log into your server's web UI, navigate to your Profile page, "
                "and generate a new Client API Key.",
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ]
    )

    # Layout
    return ft.View(
        route="/login",
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        instructions,
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        server_url_field,
                        api_key_field,
                        error_text,
                        ft.Row([btn_connect, progress_ring], alignment=ft.MainAxisAlignment.START),
                    ],
                    width=400,
                    spacing=15,
                ),
                alignment=ft.Alignment(0, 0),  # type: ignore
                expand=True,
                padding=40,
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
    )
