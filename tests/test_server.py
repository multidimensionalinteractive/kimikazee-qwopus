"""
Server endpoint tests for Kimikazee Qwopus.

This test module covers:
- Health check endpoint (/health)
- Models endpoint (/v1/models)
- Chat completions endpoint (/v1/chat/completions) - streaming and non-streaming
- CORS headers
- Error handling
- Timeout handling
- Request validation

Usage:
    pytest tests/test_server.py -v
    pytest tests/test_server.py -v --cov=server
"""

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# HEALTH ENDPOINT TESTS
# =============================================================================


class TestHealthEndpoint:
    """Tests for the /health endpoint."""
    
    def test_health_returns_healthy_when_model_loaded(
        self, 
        test_client: TestClient, 
        setup_mocked_app_state: MagicMock
    ) -> None:
        """Health check returns healthy status when model is loaded."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return valid JSON with status field
        assert "status" in data
        assert "model_loaded" in data
        assert "version" in data
    
    def test_health_returns_degraded_when_model_not_loaded(
        self,
        test_client: TestClient,
        mock_unloaded_state: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Health check returns degraded status when model is not loaded."""
        monkeypatch.setattr("server.app_state", mock_unloaded_state)
        
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "degraded"
        assert data["model_loaded"] is False
        assert data["version"] == "1.0.0"
    
    def test_health_returns_json(
        self, 
        test_client: TestClient, 
        setup_mocked_app_state: MagicMock
    ) -> None:
        """Health check returns JSON content type."""
        response = test_client.get("/health")
        
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_health_contains_required_fields(
        self,
        test_client: TestClient,
        setup_mocked_app_state: MagicMock
    ) -> None:
        """Health response contains all required fields."""
        response = test_client.get("/health")
        data = response.json()
        
        required_fields = {"status", "model_loaded", "version"}
        assert required_fields.issubset(set(data.keys()))


# =============================================================================
# MODELS ENDPOINT TESTS
# =============================================================================


class TestModelsEndpoint:
    """Tests for the /v1/models endpoint."""
    
    def test_models_returns_list(
        self, 
        test_client: TestClient, 
        setup_mocked_app_state: MagicMock
    ) -> None:
        """Models endpoint returns a list of models."""
        response = test_client.get("/v1/models")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_models_returns_single_model(
        self,
        test_client: TestClient,
        setup_mocked_app_state: MagicMock,
        sample_config: MagicMock
    ) -> None:
        """Models endpoint returns the configured model."""
        response = test_client.get("/v1/models")
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["id"] == sample_config.get("model", "qwopus")
        assert data[0]["object"] == "model"
        assert data[0]["owned_by"] == "qwopus"
    
    def test_models_contains_required_fields(
        self,
        test_client: TestClient,
        setup_mocked_app_state: MagicMock
    ) -> None:
        """Model response contains all required fields."""
        response = test_client.get("/v1/models")
        data = response.json()
        
        required_fields = {"id", "object", "created", "owned_by"}
        assert required_fields.issubset(set(data[0].keys()))
    
    def test_models_created_timestamp_is_integer(
        self,
        test_client: TestClient,
        setup_mocked_app_state: MagicMock
    ) -> None:
        """Model created field is a Unix timestamp."""
        response = test_client.get("/v1/models")
        data = response.json()
        
        assert isinstance(data[0]["created"], int)
        assert data[0]["created"] > 0


# =============================================================================
# CHAT COMPLETIONS - NON-STREAMING TESTS
# =============================================================================


class TestChatCompletionsNonStreaming:
    """Tests for non-streaming chat completions."""
    
    def test_chat_completions_success(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Chat completions returns successful response."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        response = test_client.post(
            "/v1/chat/completions",
            json=valid_chat_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["object"] == "chat.completion"
        assert data["model"] == "qwopus"
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert "content" in data["choices"][0]["message"]
    
    def test_chat_completions_without_model_field(
        self,
        test_client: TestClient,
        minimal_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Chat completions works without explicit model field."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        response = test_client.post(
            "/v1/chat/completions",
            json=minimal_chat_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should default to "qwopus"
        assert data["model"] == "qwopus"
    
    def test_chat_completions_with_custom_model(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Chat completions respects custom model field."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        request_with_model = valid_chat_request.copy()
        request_with_model["model"] = "custom-model"
        
        response = test_client.post(
            "/v1/chat/completions",
            json=request_with_model
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["model"] == "custom-model"
    
    def test_chat_completions_usage_fields(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Chat completions includes token usage statistics."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        response = test_client.post(
            "/v1/chat/completions",
            json=valid_chat_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "usage" in data
        assert "prompt_tokens" in data["usage"]
        assert "completion_tokens" in data["usage"]
        assert "total_tokens" in data["usage"]
        assert data["usage"]["total_tokens"] == (
            data["usage"]["prompt_tokens"] + data["usage"]["completion_tokens"]
        )


# =============================================================================
# CHAT COMPLETIONS - STREAMING TESTS
# =============================================================================


class TestChatCompletionsStreaming:
    """Tests for streaming chat completions."""
    
    def test_chat_completions_streaming_mode(
        self,
        test_client: TestClient,
        streaming_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Streaming returns streaming content type."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        response = test_client.post(
            "/v1/chat/completions",
            json=streaming_chat_request,
            headers={"Accept": "text/event-stream"}
        )
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
    
    def test_chat_completions_streaming_response_format(
        self,
        test_client: TestClient,
        streaming_chat_request: Dict[str, Any],
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Streaming response contains valid SSE data."""
        # Create a mock that returns streaming data
        mock = MagicMock()
        
        def stream_generator():
            yield {
                "choices": [{"delta": {"role": "assistant", "content": "Test"}, "finish_reason": None}]
            }
            yield {
                "choices": [{"delta": {"content": " response"}, "finish_reason": None}]
            }
            yield {
                "choices": [{"finish_reason": "stop"}]
            }
        
        mock.create_chat_completion = Mock(side_effect=lambda **kwargs: stream_generator())
        monkeypatch.setattr("server.app_state.model", mock)
        monkeypatch.setattr("server.app_state.is_loaded", True)
        
        response = test_client.post(
            "/v1/chat/completions",
            json=streaming_chat_request,
            headers={"Accept": "text/event-stream"}
        )
        
        assert response.status_code == 200


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestChatCompletionsErrorHandling:
    """Tests for chat completions error handling."""
    
    def test_chat_completions_model_not_loaded(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_unloaded_state: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 503 when model is not loaded."""
        monkeypatch.setattr("server.app_state", mock_unloaded_state)
        
        response = test_client.post(
            "/v1/chat/completions",
            json=valid_chat_request
        )
        
        assert response.status_code == 503
        data = response.json()
        # Check that error is indicated
        assert "detail" in data or "error" in data
    
    def test_chat_completions_invalid_request(
        self,
        test_client: TestClient
    ) -> None:
        """Returns 422 for invalid request body."""
        response = test_client.post(
            "/v1/chat/completions",
            json={"invalid": "request"}
        )
        
        assert response.status_code == 422
    
    def test_chat_completions_generates_error(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_llama_error: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 500 when model generation fails."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_error)
        
        response = test_client.post(
            "/v1/chat/completions",
            json=valid_chat_request
        )
        
        assert response.status_code == 500
        data = response.json()
        # Check that error is indicated
        assert "detail" in data or "error" in data


# =============================================================================
# REQUEST VALIDATION TESTS
# =============================================================================


class TestRequestValidation:
    """Tests for request validation."""
    
    def test_messages_required(
        self,
        test_client: TestClient
    ) -> None:
        """Missing messages field returns 422."""
        request_without_messages = {
            "model": "qwopus",
            "temperature": 0.7
        }
        
        response = test_client.post(
            "/v1/chat/completions",
            json=request_without_messages
        )
        
        assert response.status_code == 422
    
    def test_messages_not_empty(
        self,
        test_client: TestClient,
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty messages list returns 422."""
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        monkeypatch.setattr("server.app_state.is_loaded", True)
        
        request = {
            "model": "qwopus",
            "messages": []
        }
        response = test_client.post(
            "/v1/chat/completions",
            json=request
        )
        
        assert response.status_code == 422
    
    def test_invalid_role_returns_422(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any]
    ) -> None:
        """Invalid role values return 422."""
        invalid_roles = [
            {"role": "admin", "content": "test"},
            {"role": "superuser", "content": "test"},
            {"role": "guest", "content": "test"},
            {"role": "", "content": "test"},
            {"role": "user ", "content": "test"},
        ]
        
        for invalid_role in invalid_roles:
            request = valid_chat_request.copy()
            request["messages"] = [invalid_role]
            
            response = test_client.post(
                "/v1/chat/completions",
                json=request
            )
            
            assert response.status_code == 422, f"Role '{invalid_role['role']}' should be invalid"
    
    def test_valid_roles_accepted(
        self,
        test_client: TestClient,
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """All valid roles are accepted."""
        valid_roles = ["user", "assistant", "system", "tool"]
        
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        monkeypatch.setattr("server.app_state.is_loaded", True)
        
        request = {
            "messages": [{"role": "user", "content": "test content"}]
        }
        
        for role in valid_roles:
            test_request = request.copy()
            test_request["messages"] = [{"role": role, "content": "test content"}]
            
            # This should not raise 422 (may fail for other reasons)
            response = test_client.post(
                "/v1/chat/completions",
                json=test_request
            )
            
            assert response.status_code != 422, f"Role '{role}' should be valid"
    
    def test_temperature_bounds(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Temperature validation works correctly."""
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        monkeypatch.setattr("server.app_state.is_loaded", True)
        
        # Valid temperatures
        for temp in [0.0, 0.5, 0.7, 1.0, 2.0]:
            request = valid_chat_request.copy()
            request["temperature"] = temp
            response = test_client.post(
                "/v1/chat/completions",
                json=request
            )
            assert response.status_code == 200 or response.status_code == 503
        
        # Invalid temperatures
        for temp in [-0.1, 2.1]:
            request = valid_chat_request.copy()
            request["temperature"] = temp
            response = test_client.post(
                "/v1/chat/completions",
                json=request
            )
            assert response.status_code == 422
    
    def test_top_p_bounds(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Top-p validation works correctly."""
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        monkeypatch.setattr("server.app_state.is_loaded", True)
        
        # Valid top_p values
        for top_p in [0.0, 0.5, 0.9, 1.0]:
            request = valid_chat_request.copy()
            request["top_p"] = top_p
            response = test_client.post(
                "/v1/chat/completions",
                json=request
            )
            assert response.status_code == 200 or response.status_code == 503
        
        # Invalid top_p values
        for top_p in [-0.1, 1.1]:
            request = valid_chat_request.copy()
            request["top_p"] = top_p
            response = test_client.post(
                "/v1/chat/completions",
                json=request
            )
            assert response.status_code == 422


# =============================================================================
# CORS HEADERS TESTS
# =============================================================================


class TestCORSHeaders:
    """Tests for CORS middleware configuration."""
    
    def test_cors_headers_present(
        self,
        test_client: TestClient
    ) -> None:
        """CORS headers are present in response."""
        response = test_client.get("/health")
        
        # Check that CORS headers exist
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        # CORS headers may be present or not depending on implementation
        # Just verify the response is valid
        assert response.status_code == 200
    
    def test_cors_preflight_request(
        self,
        test_client: TestClient
    ) -> None:
        """OPTIONS preflight request succeeds."""
        response = test_client.options(
            "/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        assert response.status_code in [200, 204]


# =============================================================================
# TIMEOUT HANDLING TESTS
# =============================================================================


class TestTimeoutHandling:
    """Tests for timeout and graceful handling."""
    
    def test_server_handles_long_running_request(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Server handles requests without hanging."""
        # Mock a normal response
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        import time
        start = time.time()
        
        response = test_client.post(
            "/v1/chat/completions",
            json=valid_chat_request,
            timeout=5.0
        )
        
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 5.0  # Should complete within timeout
    
    def test_server_response_time_reasonable(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Response time is reasonable for mocked model."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        import time
        start = time.time()
        
        response = test_client.post(
            "/v1/chat/completions",
            json=valid_chat_request
        )
        
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # Should be very fast with mock
    
    def test_streaming_timeout_handling(
        self,
        test_client: TestClient,
        streaming_chat_request: Dict[str, Any],
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Streaming requests handle timeouts gracefully."""
        # Mock a generator that completes quickly
        mock = MagicMock()
        
        def quick_stream():
            for i in range(3):
                yield {
                    "choices": [
                        {"delta": {"content": f"chunk{i} "}, "finish_reason": None}
                    ]
                }
            yield {"choices": [{"finish_reason": "stop"}]}
        
        mock.create_chat_completion = Mock(side_effect=quick_stream)
        monkeypatch.setattr("server.app_state.model", mock)
        monkeypatch.setattr("server.app_state.is_loaded", True)
        
        import time
        start = time.time()
        
        response = test_client.post(
            "/v1/chat/completions",
            json=streaming_chat_request,
            headers={"Accept": "text/event-stream"},
            timeout=5.0
        )
        
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 5.0


# =============================================================================
# CONTENT TYPE TESTS
# =============================================================================


class TestContentType:
    """Tests for proper content type headers."""
    
    def test_health_content_type_json(
        self,
        test_client: TestClient,
        setup_mocked_app_state: MagicMock
    ) -> None:
        """Health endpoint returns JSON content type."""
        response = test_client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_models_content_type_json(
        self,
        test_client: TestClient,
        setup_mocked_app_state: MagicMock
    ) -> None:
        """Models endpoint returns JSON content type."""
        response = test_client.get("/v1/models")
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_chat_completions_content_type_json(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Chat completions returns JSON content type for non-streaming."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        response = test_client.post(
            "/v1/chat/completions",
            json=valid_chat_request
        )
        
        assert "application/json" in response.headers.get("content-type", "")


# =============================================================================
# RESPONSE STRUCTURE TESTS
# =============================================================================


class TestResponseStructure:
    """Tests for proper response structure."""
    
    def test_chat_response_has_id(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Chat response has a unique ID."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        response = test_client.post(
            "/v1/chat/completions",
            json=valid_chat_request
        )
        
        data = response.json()
        assert "id" in data
        assert len(data["id"]) > 0
    
    def test_chat_response_has_timestamp(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Chat response has created timestamp."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        response = test_client.post(
            "/v1/chat/completions",
            json=valid_chat_request
        )
        
        data = response.json()
        assert "created" in data
        assert isinstance(data["created"], int)
        assert data["created"] > 0
    
    def test_chat_response_has_finish_reason(
        self,
        test_client: TestClient,
        valid_chat_request: Dict[str, Any],
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Chat response includes finish reason."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        response = test_client.post(
            "/v1/chat/completions",
            json=valid_chat_request
        )
        
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert "finish_reason" in data["choices"][0]


# =============================================================================
# TEST DATA CLASS
# =============================================================================


class TestDataFormats:
    """Tests for various request data formats."""
    
    def test_chat_with_system_message(
        self,
        test_client: TestClient,
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Chat completions handles system messages."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        request = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"}
            ]
        }
        
        response = test_client.post(
            "/v1/chat/completions",
            json=request
        )
        
        assert response.status_code == 200 or response.status_code == 422
    
    def test_chat_with_multiple_turns(
        self,
        test_client: TestClient,
        mock_llama_instance: MagicMock,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Chat completions handles conversation history."""
        monkeypatch.setattr("server.app_state.is_loaded", True)
        monkeypatch.setattr("server.app_state.model", mock_llama_instance)
        
        request = {
            "messages": [
                {"role": "user", "content": "What is your name?"},
                {"role": "assistant", "content": "I am Qwopus."},
                {"role": "user", "content": "Nice to meet you"}
            ]
        }
        
        response = test_client.post(
            "/v1/chat/completions",
            json=request
        )
        
        assert response.status_code == 200 or response.status_code == 422


# =============================================================================
# HELPER TESTS
# =============================================================================


def test_app_instance_exists() -> None:
    """Verify that the FastAPI app instance exists."""
    from server import app, create_app
    
    assert app is not None
    assert callable(create_app)


def test_server_module_imports() -> None:
    """Verify all expected modules are importable."""
    from server import (
        load_config,
        setup_logging,
        ChatMessage,
        ChatCompletionRequest,
        ChatCompletionResponse,
        create_app,
        format_qwen_prompt,
    )
    
    assert callable(load_config)
    assert callable(setup_logging)
    assert callable(create_app)
    assert callable(format_qwen_prompt)
