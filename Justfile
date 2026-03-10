# use with https://just.systems
set shell := ["cmd.exe", "/c"]
set export

# Default target
default:
    @just --list --unsorted

export PYTHONPATH := "."

# Install python dependencies
[group: "dev"]
install:
    poetry install

# Clean up temporary files
[group: "dev"]
dev-clean:
    @echo "Cleaning up..."
    for /d /r . %d in (__pycache__ .pytest_cache .mypy_cache) do @if exist "%d" rd /s /q "%d"
    @if exist ".venv" rd /s /q ".venv"
    @echo "Cleanup complete!"

# Run the Flet client locally in development mode (hot reload)
[group: "dev"]
run:
    poetry run flet run src/app.py -d

# Quality Assurance. Usage: just qa [fix] (pass "fix" to auto-fix lint and format issues)
[group: "qa"]
qa fix="": (lint fix) (format fix) check test

# Linting. Usage: just lint [fix] (pass "fix" to auto-fix issues)
[group: "qa"]
lint fix="":
    @if "{{fix}}" == "fix" ( \
        poetry run ruff check . --fix \
    ) else ( \
        poetry run ruff check . \
    )

# Formatting. Usage: just format [fix] (pass "fix" to apply formatting, otherwise check-only)
[group: "qa"]
format fix="":
    @if "{{fix}}" == "fix" ( \
        poetry run ruff format . \
    ) else ( \
        poetry run ruff format . --check \
    )

# Type Checking
[group: "qa"]
check:
    poetry run mypy .

# Run tests. Usage: just test [type] (type: unit, integration, or empty for all)
[group: "qa"]
test type="":
    @if "{{type}}" == "" ( \
        poetry run pytest tests src/extensions \
    ) else ( \
        poetry run pytest tests src/extensions -m {{type}} \
    )

# Run tests and generate coverage report
[group: "qa"]
coverage:
    poetry run pytest --cov=src --cov-report=term-missing

# Export dependencies to requirements.txt
[group: "build"]
export-reqs:
    poetry export -f requirements.txt --output requirements.txt --without-hashes

# Build for Windows (Executable)
[group: "build"]
build target="windows":
    poetry run flet build {{target}}

# Clean build artifacts
[group: "build"]
clean:
    @if exist "build" rd /s /q "build"
    @if exist "dist" rd /s /q "dist"

# Install a Flet Client extension from a local path. Usage: just ext-install <source_path>
[group: "extensions"]
ext-install source_path:
    poetry run python -m src.extensions.manager install {{source_path}}

# Uninstall a Flet Client extension by name. Usage: just ext-uninstall <name>
[group: "extensions"]
ext-uninstall name:
    poetry run python -m src.extensions.manager uninstall {{name}}

# List all installed Flet Client extensions
[group: "extensions"]
ext-list:
    poetry run python -m src.extensions.manager list
