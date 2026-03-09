.PHONY: install install-dev test lint fmt typecheck eval clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/ -v

lint:
	ruff check harness/ tests/
	black --check harness/ tests/

fmt:
	ruff check --fix harness/ tests/
	black harness/ tests/

typecheck:
	mypy harness/

eval-single:
	maorch run --suite single_agent --adapter claude-code

eval-full:
	maorch run --suite full --adapter $(ADAPTER)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .coverage htmlcov/ dist/ *.egg-info
