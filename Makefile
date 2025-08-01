.PHONY: help install format benchmark 

help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies with uv"
	@echo "  format       - Format code with ruff"
	@echo "  benchmark    - Run benchmark (usage: make benchmark mode=sequential queries=100)"

install:
	uv sync

format:
	uv run ruff format .
	uv run ruff check --fix .
	uv run ruff check --select I --fix .

benchmark:
	uv run benchmark.py --mode=$(mode) --queries=$(queries)

example:
	uv run example.py