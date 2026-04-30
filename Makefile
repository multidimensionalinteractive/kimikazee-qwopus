# Kimikazee Qwopus Makefile
# =========================
# Test commands for the project
#
# Usage:
#   make test          - Run all tests
#   make test-watch    - Run tests in watch mode
#   make coverage      - Run tests with coverage report
#   make help          - Show this help message

.PHONY: test test-unit test-integration test-watch coverage coverage-report help clean

# Test settings
COVERAGE_REPORT = html
TESTS_DIR = tests
SERVER_MODULE = server
PYTHON = python3
PYTEST = pytest

# Default target
all: test

# Run all tests
test:
	$(PYTEST) $(TESTS_DIR) -v --tb=short

# Run tests with verbose output
test-verbose:
	$(PYTEST) $(TESTS_DIR) -v -s --tb=long

# Run specific test file
test-server:
	$(PYTEST) $(TESTS_DIR)/test_server.py -v

test-config:
	$(PYTEST) $(TESTS_DIR)/test_config.py -v

test-models:
	$(PYTEST) $(TESTS_DIR)/test_models.py -v

# Run tests with coverage
coverage:
	$(PYTEST) $(TESTS_DIR) --cov=$(SERVER_MODULE) --cov-report=term-missing --cov-report=$(COVERAGE_REPORT) -v

# Generate coverage report and open in browser
coverage-report:
	$(PYTEST) $(TESTS_DIR) --cov=$(SERVER_MODULE) --cov-report=html -v
	@echo ""
	@echo "Coverage report generated at: htmlcov/index.html"
	@echo "Open in browser: xdg-open htmlcov/index.html"

# Run tests with detailed coverage
coverage-detailed:
	$(PYTEST) $(TESTS_DIR) \
		--cov=$(SERVER_MODULE) \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml \
		--cov-fail-under=80 \
		-v

# Watch mode - run tests on file changes
test-watch:
	pytest-watch $(TESTS_DIR) -v

# Run with async support
test-async:
	$(PYTEST) $(TESTS_DIR) --asyncio-mode=auto -v

# Run single test file
run-test:
	$(PYTEST) $(TESTS_DIR)/$(TEST_FILE) -v

# Run specific test
run-single:
	$(PYTEST) $(TESTS_DIR)/$(TEST_FILE)::$(TEST_CLASS)::$(TEST_METHOD) -v

# Test with specific markers
test-markers:
	$(PYTEST) $(TESTS_DIR) -m "unit or integration" -v

# Quick test (no coverage)
quick:
	$(PYTEST) $(TESTS_DIR) -v --tb=short

# Clean test artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml 2>/dev/null || true
	@echo "Cleaned test artifacts"

# Install test dependencies
install-test:
	$(PYTHON) -m pip install -r requirements.txt
	@echo "Test dependencies installed"

# Full test setup
setup: install-test clean test

# Help command
help:
	@echo "Kimikazee Qwopus Test Suite"
	@echo "==========================="
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "  test              - Run all tests"
	@echo "  test-verbose      - Run tests with verbose output"
	@echo "  test-server       - Run server endpoint tests"
	@echo "  test-config       - Run configuration tests"
	@echo "  test-models       - Run Pydantic model tests"
	@echo "  test-async        - Run tests with asyncio mode"
	@echo "  test-watch        - Run tests in watch mode"
	@echo "  coverage          - Run tests with coverage report"
	@echo "  coverage-report   - Generate and open coverage report"
	@echo "  coverage-detailed - Run tests with detailed coverage"
	@echo "  quick             - Run quick tests without coverage"
	@echo "  run-test FILE     - Run specific test file"
	@echo "  run-single FILE::CLASS::METHOD"
	@echo "                    - Run specific test method"
	@echo "  clean             - Clean test artifacts"
	@echo "  install-test      - Install test dependencies"
	@echo "  setup             - Full test setup"
	@echo "  help              - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make test                    # Run all tests"
	@echo "  make test-watch              # Watch mode"
	@echo "  make coverage                # With coverage"
	@echo "  make run-test TEST_FILE=test_server.py"
	@echo ""

# Integration tests (requires model loaded)
integration:
	$(PYTEST) $(TESTS_DIR) -m "integration" -v --tb=short

# Unit tests only
unit:
	$(PYTEST) $(TESTS_DIR) -m "unit" -v --tb=short

# Run tests with specific keyword
keyword:
	$(PYTEST) $(TESTS_DIR) -k "$(KWD)" -v

# Run tests for specific category
category:
	@if [ "$(CAT)" = "health" ]; then \
		$(PYTEST) $(TESTS_DIR)/test_server.py -k "health" -v; \
	elif [ "$(CAT)" = "models" ]; then \
		$(PYTEST) $(TESTS_DIR)/test_server.py -k "models" -v; \
	elif [ "$(CAT)" = "chat" ]; then \
		$(PYTEST) $(TESTS_DIR)/test_server.py -k "chat" -v; \
	elif [ "$(CAT)" = "config" ]; then \
		$(PYTEST) $(TESTS_DIR)/test_config.py -v; \
	elif [ "$(CAT)" = "error" ]; then \
		$(PYTEST) $(TESTS_DIR) -k "error" -v; \
	elif [ "$(CAT)" = "cors" ]; then \
		$(PYTEST) $(TESTS_DIR)/test_server.py -k "cors" -v; \
	else \
		$(PYTEST) $(TESTS_DIR) -v; \
	fi
