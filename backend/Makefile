.PHONY: format lint test clean help

help:
	@echo "Available commands:"
	@echo "  make format    - Format code with Black"
	@echo "  make lint      - Run all linters (Black check, Flake8, Pylint)"
	@echo "  make test      - Run all tests with pytest"
	@echo "  make clean     - Remove cache and build artifacts"
	@echo "  make check     - Run format check + lint + test"

format:
	@echo "Running Black formatter..."
	python -m black app/ tests/ --line-length=120

lint:
	@echo "Running Black check..."
	python -m black app/ tests/ --check --line-length=120
	@echo "\nRunning Flake8..."
	python -m flake8 app/ tests/ --max-line-length=120
	@echo "\nRunning Pylint..."
	python -m pylint app/ --max-line-length=120 || true

test:
	@echo "Running pytest..."
	python -m pytest tests/ -v

check: lint test
	@echo "\n✓ All checks passed!"

clean:
	@echo "Cleaning cache and build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Clean complete!"
