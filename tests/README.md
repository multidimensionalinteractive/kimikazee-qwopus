# Kimikazee Qwopus Test Suite

Comprehensive test suite for the Kimikazee Qwopus project. This test suite covers server endpoints, configuration, and Pydantic model validation.

## Table of Contents

- [Overview](#overview)
- [Test Coverage](#test-coverage)
- [Quick Start](#quick-start)
- [Running Tests](#running-tests)
- [Test Files](#test-files)
- [Fixtures](#fixtures)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

This test suite is built with pytest and provides:

- **Endpoint Testing**: Comprehensive tests for FastAPI endpoints
- **Configuration Testing**: YAML parsing and environment variable substitution
- **Model Validation**: Pydantic model testing and validation
- **Error Handling**: Validation of error responses
- **Async Support**: Full asyncio test support

## Test Coverage

### Server Tests (`test_server.py`)

| Test Category | Endpoints | Coverage |
|---------------|-----------|----------|
| Health | `/health` | ✅ Status checks, model loaded flag |
| Models | `/v1/models` | ✅ List models, format validation |
| Chat Completions | `/v1/chat/completions` | ✅ Streaming & non-streaming |
| Request Validation | All | ✅ 422 responses, field validation |
| CORS | All | ✅ Headers, preflight requests |
| Timeout | All | ✅ Response time, graceful handling |

### Configuration Tests (`test_config.py`)

| Test Category | Coverage |
|---------------|----------|
| Config Loading | ✅ Valid/invalid files |
| Environment Variables | ✅ Substitution, defaults |
| Default Values | ✅ Missing fields |
| Nested Sections | ✅ Discord, Telegram configs |
| Path Handling | ✅ Home directory expansion |
| Edge Cases | ✅ Empty files, comments |

### Model Tests (`test_models.py`)

| Model | Tests |
|-------|-------|
| `ChatMessage` | ✅ Role validation, content handling |
| `ChatCompletionRequest` | ✅ All field constraints |
| `ChatCompletionResponse` | ✅ Serialization, structure |
| `ModelResponse` | ✅ Format validation |
| `HealthResponse` | ✅ Status values |
| Stream Models | ✅ SSE format |

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
make test
```

### First Test Run

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=server --cov-report=html

# Open coverage report
xdg-open htmlcov/index.html
```

## Running Tests

### Basic Commands

```bash
# Run all tests
make test

# Run specific test file
make test-server
make test-config
make test-models

# Run with verbose output
make test-verbose

# Quick tests (no coverage)
make quick
```

### With Coverage

```bash
# Generate coverage report
make coverage

# Open HTML report
make coverage-report

# Detailed coverage with XML output
make coverage-detailed
```

### Watch Mode

```bash
# Watch for changes and auto-run
make test-watch
```

### Specific Test Execution

```bash
# Run specific test file
pytest tests/test_server.py -v

# Run specific test class
pytest tests/test_server.py::TestHealthEndpoint -v

# Run specific test method
pytest tests/test_server.py::TestHealthEndpoint::test_health_returns_healthy_when_model_loaded -v
```

## Test Files

### `test_server.py`

Server endpoint tests covering:

- **Health Endpoint**: `/health` status checks
- **Models Endpoint**: `/v1/models` listing
- **Chat Completions**: `/v1/chat/completions` with streaming support
- **Error Handling**: 422, 503, 500 responses
- **Request Validation**: Field constraints, role validation
- **CORS Headers**: All allowed origins, preflight
- **Timeout Handling**: Response time, graceful handling

### `test_config.py`

Configuration tests covering:

- **File Loading**: Valid/invalid YAML files
- **Environment Variables**: Substitution and defaults
- **Config Structure**: Nested sections, lists
- **Path Handling**: Home directory expansion
- **Validation**: Value ranges, types

### `test_models.py`

Pydantic model tests covering:

- **ChatMessage**: Role validation, content handling
- **ChatCompletionRequest**: Field constraints, defaults
- **Response Models**: Serialization, structure
- **Edge Cases**: Empty strings, special characters
- **Validation**: Bounds checking, type enforcement

## Fixtures

The test suite provides the following reusable fixtures:

### Configuration Fixtures

| Fixture | Description |
|---------|-------------|
| `sample_config` | Sample configuration dictionary |
| `temp_config_file` | Temporary config file for testing |
| `invalid_config_file` | Malformed YAML file for error testing |

### Mock Fixtures

| Fixture | Description |
|---------|-------------|
| `mock_llama_instance` | Mocked Llama model instance |
| `mock_app_state` | Mocked AppState with loaded model |
| `mock_unloaded_state` | Mocked AppState without model |
| `mock_llama_error` | Llama instance that raises errors |

### Test Client Fixtures

| Fixture | Description |
|---------|-------------|
| `test_client` | TestClient for FastAPI app |
| `async_test_client` | Async test client |
| `app_with_loaded_model` | App with model loaded flag |

### Sample Data Fixtures

| Fixture | Description |
|---------|-------------|
| `valid_chat_message` | Valid chat message dict |
| `valid_chat_request` | Complete chat request |
| `streaming_chat_request` | Streaming mode request |
| `minimal_chat_request` | Minimal valid request |
| `invalid_roles` | List of invalid role values |
| `empty_messages_request` | Request with empty messages |

### Test Data Helpers

```python
from tests.conftest import (
    create_health_response,
    create_model_response,
    create_chat_response
)
```

## Examples

### Testing Health Endpoint

```python
def test_health_healthy(test_client):
    """Test health returns healthy status."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
```

### Testing Request Validation

```python
def test_invalid_role(test_client):
    """Test invalid roles return 422."""
    request = {
        "messages": [{"role": "admin", "content": "test"}]
    }
    response = test_client.post("/v1/chat/completions", json=request)
    assert response.status_code == 422
```

### Testing with Mock

```python
def test_chat_with_mock(mock_llama_instance, test_client, monkeypatch):
    """Test chat completions with mocked model."""
    monkeypatch.setattr("server.app_state.model", mock_llama_instance)
    monkeypatch.setattr("server.app_state.is_loaded", True)
    
    request = {
        "messages": [{"role": "user", "content": "Hello"}]
    }
    response = test_client.post("/v1/chat/completions", json=request)
    assert response.status_code == 200
```

### Testing Streaming

```python
def test_streaming_response(test_client, streaming_request):
    """Test streaming returns correct content type."""
    response = test_client.post(
        "/v1/chat/completions",
        json=streaming_request,
        headers={"Accept": "text/event-stream"}
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
```

## Troubleshooting

### Common Issues

#### Test Client Timeout

If tests timeout:
```bash
# Increase timeout for specific test
@pytest.mark.timeout(30)
def test_long_running():
    ...
```

#### Mock Not Working

Ensure mocks are applied before the request:
```python
def test_with_mock(mock_llama_instance, test_client, monkeypatch):
    monkeypatch.setattr("server.app_state.model", mock_llama_instance)
    # Now make request
```

#### Config Loading Errors

Use the provided fixtures:
```python
def test_config(temp_config_file, sample_config):
    config = load_config(temp_config_file)
    assert config == sample_config
```

### Debug Tips

```bash
# Run with detailed output
pytest tests/ -v -s --tb=long

# Run single failing test
pytest tests/test_server.py::TestHealthEndpoint::test_name -v -s

# See all available tests
pytest tests/ --collect-only

# Run with verbose traceback
pytest tests/ --tb=long
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=server --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Test Markers

The test suite uses the following markers:

| Marker | Description |
|--------|-------------|
| `asyncio` | Async test case |
| `integration` | Integration test |
| `unit` | Unit test |
| `slow` | Slow running test |

Run tests with markers:
```bash
pytest tests/ -m "unit"  # Run only unit tests
pytest tests/ -m "not slow"  # Exclude slow tests
```

## Contributing

When adding new tests:

1. **Place in appropriate file**:
   - Server endpoints → `test_server.py`
   - Configuration → `test_config.py`
   - Models → `test_models.py`

2. **Use existing fixtures** from `conftest.py`

3. **Follow naming conventions**:
   - Test functions: `test_` prefix
   - Test classes: `Test` prefix
   - Clear, descriptive names

4. **Include assertions**:
   - Status codes
   - Response structure
   - Data values

5. **Run tests before committing**:
   ```bash
   make test
   ```

## License

Same as the parent project (Kimikazee Qwopus).
