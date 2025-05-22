install:
	uv sync

run:
	uv run fitness_bot/bot.py

test:
	uv run pytest

test-coverage:
	uv run pytest --cov=***package_name*** --cov-report xml

lint:
	uv run ruff check

lintf:
	uv run ruff check --fix

check:
	test lint

build:
	uv build