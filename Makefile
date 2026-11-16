.PHONY: install test lint list run run-pg db-up db-down data

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest -q

lint:
	ruff check .

list:
	sqlcases list

run:            ## all problems on DuckDB (no setup needed)
	sqlcases run all

run-pg:         ## all problems on the docker Postgres
	PG_DSN=postgresql://postgres:postgres@localhost:5432/shop sqlcases run all --engine postgres

db-up:
	docker compose up -d --wait

db-down:
	docker compose down -v

data:           ## regenerate data/*.csv (deterministic)
	sqlcases generate
