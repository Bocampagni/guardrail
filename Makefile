.PHONY: help install format benchmark docker-build shell docker-benchmark docker-clean

help:
	@echo "Available commands:"
	@echo "  install         	- Install dependencies locally with uv"
	@echo "  format          	- Format code with ruff"
	@echo "  benchmark       	- Run benchmark locally (usage: make benchmark mode=sequential queries=100)"
	@echo "  docker-build    	- Build Docker image"
	@echo "  shell           	- Open shell in Docker container"
	@echo "  docker-benchmark 	- Run benchmark in Docker (usage: make docker-benchmark mode=sequential queries=100)"
	@echo "  docker-lean    	- Remove Docker image"

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

docker-build:
	docker build -t guardrail:latest .

shell: docker-build
	docker run -it --rm guardrail:latest /bin/bash

docker-benchmark: docker-build
	docker run --rm guardrail:latest python benchmark.py --mode=$(mode) --queries=$(queries)

docker-clean:
	docker rmi guardrail:latest || true