# Justfile for powercord-client

# Default target
default:
    @just --list

export PYTHONPATH := "."

# Run the Flet client locally in development mode (hot reload)
run:
    poetry run flet run src/app.py -d

# Format code with Ruff and Black/Isort equivalents (assuming ruff in future)
format:
    poetry run ruff check --fix .
    poetry run ruff format .

# Check code quality
lint:
    poetry run ruff check .
    poetry run mypy .

# Run tests
test:
    poetry run pytest

# Run all QA checks
qa: format lint test

# Export dependencies to requirements.txt
export-reqs:
    poetry export -f requirements.txt --output requirements.txt --without-hashes

# Build for Windows (Executable)
build windows:
    poetry run flet build windows

# Clean build artifacts
clean:
    rm -rf build/
    rm -rf dist/
