# Powercord Client Guidelines (`powercord-client/`)

This repository houses the companion desktop application built with Flet and HTTPX.

---

## Core Client Invariants

1. **Flet v0.82+ Async Routing**: Follow strict async navigation patterns. Never perform synchronous blocking network calls inside UI components.
2. **HTTP API Communication**: Communicate with the Powercord backend exclusively via the HTTP client abstraction (`httpx.AsyncClient`).
3. **No Server Module Imports**: Never import server modules (`app.*`, `nextcord`, `fasthtml`, `sqlmodel`) into client views.
4. **Pre-Commit Checks**: Always run `poetry run ruff check --fix . && poetry run ruff format .` and `poetry run pytest` before submitting changes for human review.
