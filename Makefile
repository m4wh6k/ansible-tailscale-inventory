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
	black .
	ruff --fix .

.PHONY: test
test: test-black test-mypy test-pytest test-ruff

.PHONY: test-black
test-black: dev
	black --check .

.PHONY: test-mypy
test-mypy: dev
	mypy

.PHONY: test-pytest
test-pytest: dev
	pytest

.PHONY: test-ruff
test-ruff: dev
	ruff check .
