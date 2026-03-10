# Powercord Client

The official companion application for the Powercord framework, built with [Flet](https://flet.dev/).
This client aims to provide a unified, native desktop and mobile experience for administrating Powercord servers and utilizing Powercord extensions like the `midi_library`.

## Features
- **Native GUI Administration**: Connect to any active Powercord server using personal API keys.
- **Server Dashboard**: Manage your server's global extension states directly from the Flet interface.
- **Extensible Architecture**: Natively supports injecting client-side Flet modules that connect with external Powercord server extensions.
- **Cross-Platform**: Designed to package gracefully for Desktop platforms (Windows, macOS, Linux) and Mobile (Android, iOS).

## Setup & Installation

This project utilizes `poetry` for dependency management.

```bash
# Clone the repository
git clone https://github.com/your-org/powercord-client.git
cd powercord-client

# Install dependencies (ignoring root package installation)
poetry install --no-root
```

## Running the Application

You can use the provided `Justfile` to easily manage the project:

```bash
# Run the Flet application
just run

# Check formatting and linting
just qa
```

## Connecting to a Server

1. Launch your Powercord backend server.
2. Log into the Powercord Web UI, navigate to the **Profile** page, and generate a new **Client API Key**.
3. Run the Flet client. Enter your server's URL (e.g., `http://127.0.0.1:8000`) and the API Key you generated.
4. The client will securely store your credentials and route you to the Dashboard.

## Architecture

- `src/app.py`: The main Flet entry point and routing manager.
- `src/api_client.py`: An HTTPX wrapper that manages authentication and connects to the Powercord internal network.
- `src/views/`: Individual Flet Views (e.g., `/dashboard`, `/login`, `/server/:id`).
- `src/components/`: Reusable Flet Controls (e.g., custom buttons, headers, navigation).
- `src/extensions/manager.py`: The dynamic plugin loader that identifies and mounts local client extensions.
- `src/extensions/`: The core directory where Flet extensions reside.

## Extension Development

Developing a client extension for Powercord is simple. Client extensions allow you to build custom Flet UIs that interact with the custom APIs added by your backend Discord bot.

See the [EXTENSION_DEVELOPMENT.md](docs/EXTENSION_DEVELOPMENT.md) guide for a full walkthrough.
