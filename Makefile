.PHONY: help install format 

help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies with uv"
	@echo "  format       - Format code with ruff"

install:
	uv sync

format:
	uv run ruff format .
	uv run ruff check --fix .
	uv run ruff check --select I --fix .