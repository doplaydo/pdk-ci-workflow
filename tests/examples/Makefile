install:
	uv sync

test:
	uv run pytest

test-force:
	uv run pytest --force-regen

docs:
	jupyter-book build docs

build:
	uv build

update-pre:
	pre-commit autoupdate

dev:
	uv sync --group dev
