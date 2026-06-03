# use with https://just.systems
set shell := ["bash", "-cu"]
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
    find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache \) -exec rm -rf {} +
    [ -d .venv ] && rm -rf .venv || true
    @echo "Cleanup complete!"

# Run the Flet client locally in development mode (hot reload)
[group: "dev"]
run:
    poetry run flet run src/app.py -d

# Quality Assurance. Usage: just qa [--fix]
[group: "qa"]
[arg("fix", long, value="true")]
qa fix="false": (lint fix) (format fix) check test

# Linting. Usage: just lint [--fix] (auto-fix issues)
[group: "qa"]
[arg("fix", long, value="true")]
lint fix="false":
    poetry run ruff check . {{ if fix == "true" { "--fix" } else { "" } }}

# Formatting. Usage: just format [--fix] (apply formatting, otherwise check-only)
[group: "qa"]
[arg("fix", long, value="true")]
format fix="false":
    poetry run ruff format . {{ if fix == "false" { "--check" } else { "" } }}

# Type Checking
[group: "qa"]
check:
    poetry run mypy .

# Run tests. Usage: just test [--type unit|integration]
[group: "qa"]
[arg("type", long)]
test type="":
    #!/usr/bin/env bash
    if [ "{{type}}" = "" ]; then
      poetry run pytest tests src/extensions
    else
      poetry run pytest tests src/extensions -m "{{type}}"
    fi

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
    rm -rf build dist

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
