"""
Pytest fixtures for Kimikazee Qwopus test suite.

This module provides reusable fixtures for:
- Test configuration loading
- Mocked Llama model instances
- Test HTTP client
- Sample data for requests
- App state management

Usage:
    pytest tests/ -v --cov=server
"""

import asyncio
import json
import os
import sys
from typing import Any, AsyncGenerator, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =============================================================================
# MOCK LLAMA_CPP BEFORE IMPORTING SERVER
# =============================================================================

# Create a mock for llama_cpp module to avoid import errors
mock_llama_cpp = MagicMock()
mock_llama_cpp.Llama = MagicMock
mock_llama_cpp.LlamaGrammar = MagicMock

# Import and configure tokenizer mock
mock_tokenizer = MagicMock()
mock_llama_cpp.llama_tokenizer = mock_tokenizer
mock_tokenizer.LlamaTokenizer = MagicMock

sys.modules['llama_cpp'] = mock_llama_cpp
sys.modules['llama_cpp.llama_tokenizer'] = mock_tokenizer

# =============================================================================
# FIXTURES FOR CONFIG LOADING
# =============================================================================


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration dictionary."""
    return {
        "provider": "custom",
        "model": "Qwen3.5-9B-Uncensored-Q8_0.gguf",
        "context_window": 128000,
        "parallel": 4,
        "n_predict": -1,
        "temp": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "flash_attn": True,
        "n_threads": 8,
        "n_gpu_layers": 0,
        "log_level": "INFO",
        "log_file": "/tmp/test_server.log",
    }


@pytest.fixture
def temp_config_file(tmp_path, sample_config) -> str:
    """Create a temporary config file for testing."""
    config_path = tmp_path / "test_config.yaml"
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(sample_config, f)
    return str(config_path)


@pytest.fixture
def invalid_config_file(tmp_path) -> str:
    """Create a temporary invalid config file."""
    config_path = tmp_path / "invalid_config.yaml"
    with open(config_path, 'w') as f:
        f.write("invalid: yaml: content: [\n")  # Malformed YAML
    return str(config_path)


# =============================================================================
# FIXTURES FOR MOCKED LLAMA MODEL
# =============================================================================


@pytest.fixture
def mock_llama_instance() -> MagicMock:
    """Create a mock llama-cpp-python Llama instance."""
    mock = MagicMock()
    
    # Mock tokenize method
    mock.tokenize = Mock(side_effect=lambda text: [1, 2, 3, 4, 5] if text else [1, 2, 3])
    
    # Mock create_chat_completion for non-streaming
    def mock_create_chat_completion(messages=None, **kwargs):
        return {
            "id": "test-id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "qwopus",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a test response from the mock model."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 10,
                "total_tokens": 15
            }
        }
    
    mock.create_chat_completion = Mock(side_effect=mock_create_chat_completion)
    
    # Mock create_chat_completion for streaming
    def mock_create_chat_completion_stream(messages=None, stream=False, **kwargs):
        if not stream:
            return mock_create_chat_completion(messages, **kwargs)
        
        # Simulate streaming response
        response_text = "This is a test response."
        chunks = response_text.split()
        
        def stream_generator():
            for i, chunk in enumerate(chunks):
                yield {
                    "id": f"stream-{i}",
                    "object": "chat.completion.chunk",
                    "created": 1234567890,
                    "model": "qwopus",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant", "content": chunk + " "},
                            "finish_reason": None
                        }
                    ]
                }
            # Final chunk
            yield {
                "id": f"stream-final",
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": "qwopus",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": ""},
                        "finish_reason": "stop"
                    }
                ]
            }
        
        return stream_generator()
    
    mock.create_chat_completion = Mock(side_effect=mock_create_chat_completion_stream)
    
    return mock


@pytest.fixture
def mock_app_state(mock_llama_instance, sample_config) -> MagicMock:
    """Create a mock AppState instance."""
    mock_state = MagicMock()
    mock_state.config = sample_config
    mock_state.logger = MagicMock()
    mock_state.model = mock_llama_instance
    mock_state.model_path = "test_model.gguf"
    mock_state.is_loaded = True
    mock_state.startup_time = 1234567890.0
    
    return mock_state


# =============================================================================
# FIXTURES FOR TEST CLIENTS
# =============================================================================


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI application."""
    from server import create_app
    
    app = create_app()
    # Configure CORS explicitly
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def async_test_client() -> AsyncGenerator[TestClient, None]:
    """Create an async test client."""
    from server import create_app
    
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


# =============================================================================
# FIXTURES FOR SAMPLE DATA
# =============================================================================


@pytest.fixture
def valid_chat_message() -> Dict[str, Any]:
    """Valid chat message for testing."""
    return {
        "role": "user",
        "content": "Hello, how are you?"
    }


@pytest.fixture
def valid_chat_request(sample_config) -> Dict[str, Any]:
    """Valid chat completion request."""
    return {
        "model": "qwopus",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "max_tokens": 100,
        "stream": False
    }


@pytest.fixture
def streaming_chat_request() -> Dict[str, Any]:
    """Valid streaming chat completion request."""
    return {
        "model": "qwopus",
        "messages": [
            {"role": "user", "content": "Tell me a joke."}
        ],
        "temperature": 0.8,
        "stream": True
    }


@pytest.fixture
def minimal_chat_request() -> Dict[str, Any]:
    """Minimal valid chat request."""
    return {
        "messages": [
            {"role": "user", "content": "Test"}
        ]
    }


@pytest.fixture
def invalid_roles() -> List[Dict[str, Any]]:
    """List of invalid role values."""
    return [
        {"role": "admin", "content": "test"},
        {"role": "superuser", "content": "test"},
        {"role": "guest", "content": "test"},
        {"role": "", "content": "test"},
        {"role": "user ", "content": "test"},
    ]


@pytest.fixture
def empty_messages_request() -> Dict[str, Any]:
    """Request with empty messages list."""
    return {
        "model": "qwopus",
        "messages": []
    }


# =============================================================================
# FIXTURES FOR APP STATE MANAGEMENT
# =============================================================================


@pytest.fixture(autouse=True)
def setup_mocked_app_state(
    mock_app_state: MagicMock,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Autouse fixture to mock app_state globally.
    
    This ensures all tests use a mocked AppState instead of loading
    the actual model, making tests fast and deterministic.
    """
    import server
    monkeypatch.setattr(server, 'app_state', mock_app_state)


@pytest.fixture
def app_with_loaded_model(test_client, monkeypatch) -> FastAPI:
    """Get the FastAPI app with model loaded flag set to True."""
    from server import app
    
    # Ensure model is marked as loaded
    if server.app_state:
        server.app_state.is_loaded = True
    
    return app


# =============================================================================
# FIXTURES FOR ERROR TESTING
# =============================================================================


@pytest.fixture
def mock_unloaded_state(sample_config) -> MagicMock:
    """Create a mock AppState with model NOT loaded."""
    mock_state = MagicMock()
    mock_state.config = sample_config
    mock_state.logger = MagicMock()
    mock_state.model = None
    mock_state.model_path = "test_model.gguf"
    mock_state.is_loaded = False
    mock_state.startup_time = None
    
    return mock_state


@pytest.fixture
def mock_llama_error() -> MagicMock:
    """Create a mock Llama instance that raises errors."""
    mock = MagicMock()
    mock.create_chat_completion = Mock(side_effect=Exception("Generation failed"))
    mock.tokenize = Mock(side_effect=Exception("Tokenization error"))
    return mock


@pytest.fixture
def mock_timeout_context(monkeypatch) -> MagicMock:
    """Mock context for timeout testing."""
    mock = MagicMock()
    
    async def async_timeout(timeout):
        """Simple async timeout context."""
        if timeout <= 0:
            raise asyncio.TimeoutError("Timeout exceeded")
        yield
    
    monkeypatch.setattr('asyncio.timeout', async_timeout)
    return mock


# =============================================================================
# CONVENIENCE FUNCTIONS FOR TESTS
# =============================================================================


def create_health_response(status: str, model_loaded: bool) -> Dict[str, Any]:
    """Create a health check response."""
    return {
        "status": status,
        "model_loaded": model_loaded,
        "version": "1.0.0"
    }


def create_model_response(model_id: str = "qwopus") -> Dict[str, Any]:
    """Create a model list response."""
    import time
    return [
        {
            "id": model_id,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "qwopus"
        }
    ]


def create_chat_response(content: str = "Test response") -> Dict[str, Any]:
    """Create a chat completion response."""
    import time
    import uuid
    
    return {
        "id": str(uuid.uuid4()),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "qwopus",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 5,
            "completion_tokens": 10,
            "total_tokens": 15
        }
    }


# =============================================================================
# TEST CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Configure pytest markers and options."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async test case"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow to run"
    )
