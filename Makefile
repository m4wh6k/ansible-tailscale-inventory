.DEFAULT_GOAL = dev

.PHONY: clean
clean:
	rm -rf \
		__pycache__ \
		.mypy_cache \
		.pytest_cache \
		.ruff_cache \
		**/__pycache__

.PHONY: dev
dev: 
	pip3 install -U -r dev-requirements.txt

.PHONY: fmt
fmt: dev
	ruff format .
	ruff --fix .

.PHONY: test
test: test-mypy test-pytest test-ruff

.PHONY: test-mypy
test-mypy: dev
	mypy

.PHONY: test-pytest
test-pytest: dev
	pytest

.PHONY: test-ruff
test-ruff: dev
	ruff format --check .
	ruff check .
