from typing import Callable, Dict, Optional

import flet as ft


class ClientExtension:
    """
    Base class for all Powercord Client Extensions.

    Client extensions are used to inject new views/screens into the main client,
    typically to provide native Flet UI that corresponds to a server extension.
    """

    # The internal name of the extension (e.g. 'midi_client')
    name: str = "base_extension"

    # Human readable name for UI
    display_name: str = "Base Extension"

    # Flet Icon name for the navigation rail/bar (e.g. ft.Icons.MUSIC_NOTE)
    icon = ft.Icons.EXTENSION

    def __init__(self, api_client):
        """
        Initializes the extension with a reference to the main API client.
        :param api_client: The PowercordApiClient instance.
        """
        self.api = api_client

    def get_navigation_item(self) -> Optional[ft.NavigationRailDestination]:
        """
        Return the navigation destination for the sidebar/bottom bar.
        Override to return None if this extension has no main view.
        """
        return ft.NavigationRailDestination(
            icon=self.icon,
            selected_icon=self.icon,
            label=self.display_name,
        )

    def get_routes(self) -> Dict[str, Callable[[ft.Page], ft.View]]:
        """
        Return a dictionary mapping route strings to View generators.
        For example:
        {
            "/ext/midi": self.view_midi_scanner,
            "/ext/midi/settings": self.view_midi_settings
        }
        """
        return {}
