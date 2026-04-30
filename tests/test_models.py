"""
Pydantic model validation tests for Kimikazee Qwopus.

This test module covers:
- ChatMessage model validation
- ChatCompletionRequest validation
- Response model validation
- Edge cases and error conditions
- Field constraints and validators
- Serialization/deserialization

Usage:
    pytest tests/test_models.py -v
"""

import pytest
from pydantic import ValidationError

# Mock llama_cpp before importing server
from unittest.mock import MagicMock
import sys

mock_llama_cpp = MagicMock()
sys.modules['llama_cpp'] = mock_llama_cpp

from server import (
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatUsage,
    Choice,
    HealthResponse,
    ModelResponse,
    ChatCompletionStreamResponse,
    ChatCompletionStreamChoice,
)


# =============================================================================
# CHAT MESSAGE TESTS
# =============================================================================


class TestChatMessage:
    """Tests for ChatMessage model."""
    
    def test_chat_message_valid_user(self) -> None:
        """Valid user message is created."""
        message = ChatMessage(role="user", content="Hello")
        
        assert message.role == "user"
        assert message.content == "Hello"
    
    def test_chat_message_valid_assistant(self) -> None:
        """Valid assistant message is created."""
        message = ChatMessage(role="assistant", content="Hi there!")
        
        assert message.role == "assistant"
        assert message.content == "Hi there!"
    
    def test_chat_message_valid_system(self) -> None:
        """Valid system message is created."""
        message = ChatMessage(role="system", content="You are an AI.")
        
        assert message.role == "system"
        assert message.content == "You are an AI."
    
    def test_chat_message_valid_tool(self) -> None:
        """Valid tool message is created."""
        message = ChatMessage(role="tool", content="Tool response")
        
        assert message.role == "tool"
        assert message.content == "Tool response"
    
    def test_chat_message_invalid_role(self) -> None:
        """Invalid role raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ChatMessage(role="invalid_role", content="test")
        
        assert exc_info.value.error_count() > 0
    
    def test_chat_message_empty_role(self) -> None:
        """Empty role raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatMessage(role="", content="test")
    
    def test_chat_message_role_with_space(self) -> None:
        """Role with trailing space raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatMessage(role="user ", content="test")
    
    def test_chat_message_empty_content(self) -> None:
        """Empty content is allowed (edge case)."""
        # Empty string content should be valid
        message = ChatMessage(role="user", content="")
        assert message.content == ""
    
    def test_chat_message_multiline_content(self) -> None:
        """Multiline content is handled correctly."""
        content = """Line 1
Line 2
Line 3"""
        message = ChatMessage(role="user", content=content)
        assert message.content == content
    
    def test_chat_message_unicode_content(self) -> None:
        """Unicode content is handled correctly."""
        content = "Hello 世界 🌍"
        message = ChatMessage(role="user", content=content)
        assert message.content == content
    
    def test_chat_message_dict_serialization(self) -> None:
        """ChatMessage serializes to dict correctly."""
        message = ChatMessage(role="user", content="Hello")
        
        data = message.model_dump()
        
        assert "role" in data
        assert "content" in data
        assert data["role"] == "user"
        assert data["content"] == "Hello"
    
    def test_chat_message_json_serialization(self) -> None:
        """ChatMessage serializes to JSON correctly."""
        import json
        message = ChatMessage(role="user", content="Hello")
        
        json_str = message.model_dump_json()
        data = json.loads(json_str)
        
        assert data["role"] == "user"
        assert data["content"] == "Hello"


# =============================================================================
# CHAT COMPLETION REQUEST TESTS
# =============================================================================


class TestChatCompletionRequest:
    """Tests for ChatCompletionRequest model."""
    
    def test_request_minimum_valid(self) -> None:
        """Minimum valid request is created."""
        request = ChatCompletionRequest(
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        assert request.model == "qwopus"
        assert len(request.messages) == 1
        assert request.messages[0].role == "user"
    
    def test_request_with_all_fields(self) -> None:
        """Request with all fields is created."""
        request = ChatCompletionRequest(
            model="custom-model",
            messages=[{"role": "user", "content": "Test"}],
            temperature=0.8,
            top_p=0.95,
            top_k=50,
            max_tokens=200,
            stop=["\n", "END"],
            stream=False,
            frequency_penalty=0.5,
            presence_penalty=0.3,
            seed=42,
            user="test_user"
        )
        
        assert request.model == "custom-model"
        assert request.temperature == 0.8
        assert request.top_p == 0.95
        assert request.top_k == 50
        assert request.max_tokens == 200
        assert request.stop == ["\n", "END"]
        assert request.stream is False
        assert request.seed == 42
    
    def test_request_missing_messages(self) -> None:
        """Missing messages field raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatCompletionRequest(model="test")
    
    def test_request_empty_messages(self) -> None:
        """Empty messages list raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatCompletionRequest(messages=[])
    
    def test_request_invalid_message_role(self) -> None:
        """Invalid message role raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[{"role": "admin", "content": "test"}]
            )
    
    def test_request_temperature_bounds(self) -> None:
        """Temperature validation works."""
        # Valid temperatures
        for temp in [0.0, 0.5, 1.0, 2.0]:
            request = ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                temperature=temp
            )
            assert request.temperature == temp
        
        # Invalid temperatures
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                temperature=-0.1
            )
        
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                temperature=2.1
            )
    
    def test_request_top_p_bounds(self) -> None:
        """Top-p validation works."""
        # Valid top_p values
        for top_p in [0.0, 0.5, 1.0]:
            request = ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                top_p=top_p
            )
            assert request.top_p == top_p
        
        # Invalid top_p values
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                top_p=-0.1
            )
        
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                top_p=1.1
            )
    
    def test_request_top_k_bounds(self) -> None:
        """Top-k validation works."""
        # Valid top_k values
        for top_k in [1, 10, 40, 100]:
            request = ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                top_k=top_k
            )
            assert request.top_k == top_k
        
        # Invalid top_k values
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                top_k=0
            )
        
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                top_k=101
            )
    
    def test_request_max_tokens_min(self) -> None:
        """Max tokens minimum value works."""
        request = ChatCompletionRequest(
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=1
        )
        assert request.max_tokens == 1
        
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=0
            )
    
    def test_request_frequency_penalty_bounds(self) -> None:
        """Frequency penalty bounds validation works."""
        # Valid values
        for freq in [-2.0, -1.0, 0.0, 1.0, 2.0]:
            request = ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                frequency_penalty=freq
            )
            assert request.frequency_penalty == freq
        
        # Invalid values
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                frequency_penalty=-2.1
            )
        
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                frequency_penalty=2.1
            )
    
    def test_request_presence_penalty_bounds(self) -> None:
        """Presence penalty bounds validation works."""
        # Valid values
        for pres in [-2.0, -1.0, 0.0, 1.0, 2.0]:
            request = ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                presence_penalty=pres
            )
            assert request.presence_penalty == pres
        
        # Invalid values
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                presence_penalty=-2.1
            )
        
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[{"role": "user", "content": "Test"}],
                presence_penalty=2.1
            )
    
    def test_request_multiple_messages(self) -> None:
        """Multiple messages are accepted."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant response"},
            {"role": "user", "content": "Another user message"}
        ]
        
        request = ChatCompletionRequest(messages=messages)
        assert len(request.messages) == 4
    
    def test_request_dict_serialization(self) -> None:
        """Request serializes to dict correctly."""
        request = ChatCompletionRequest(
            model="test",
            messages=[{"role": "user", "content": "Hi"}],
            temperature=0.7
        )
        
        data = request.model_dump()
        
        assert "model" in data
        assert "messages" in data
        assert "temperature" in data
    
    def test_request_json_serialization(self) -> None:
        """Request serializes to JSON correctly."""
        import json
        request = ChatCompletionRequest(
            messages=[{"role": "user", "content": "Hi"}]
        )
        
        json_str = request.model_dump_json()
        data = json.loads(json_str)
        
        assert data["model"] == "qwopus"
        assert len(data["messages"]) == 1


# =============================================================================
# CHAT COMPLETION RESPONSE TESTS
# =============================================================================


class TestChatCompletionResponse:
    """Tests for ChatCompletionResponse model."""
    
    def test_response_minimum_valid(self) -> None:
        """Minimum valid response is created."""
        import time
        import uuid
        
        response = ChatCompletionResponse(
            id=str(uuid.uuid4()),
            choices=[{
                "index": 0,
                "message": {"role": "assistant", "content": "Test"},
                "finish_reason": "stop"
            }],
            created=int(time.time()),
            model="qwopus",
            usage={
                "prompt_tokens": 5,
                "completion_tokens": 10,
                "total_tokens": 15
            }
        )
        
        assert response.object == "chat.completion"
        assert len(response.choices) == 1
    
    def test_response_with_multiple_choices(self) -> None:
        """Response with multiple choices is valid."""
        import time
        import uuid
        
        response = ChatCompletionResponse(
            id=str(uuid.uuid4()),
            choices=[
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Choice 1"},
                    "finish_reason": "stop"
                },
                {
                    "index": 1,
                    "message": {"role": "assistant", "content": "Choice 2"},
                    "finish_reason": "length"
                }
            ],
            created=int(time.time()),
            model="qwopus",
            usage={
                "prompt_tokens": 5,
                "completion_tokens": 20,
                "total_tokens": 25
            }
        )
        
        assert len(response.choices) == 2
    
    def test_response_usage_calculation(self) -> None:
        """Usage total_tokens is calculated correctly."""
        import time
        import uuid
        
        response = ChatCompletionResponse(
            id=str(uuid.uuid4()),
            choices=[{
                "index": 0,
                "message": {"role": "assistant", "content": "Test"},
                "finish_reason": "stop"
            }],
            created=int(time.time()),
            model="qwopus",
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        )
        
        assert response.usage.total_tokens == 15
    
    def test_response_serialization(self) -> None:
        """Response serializes to dict correctly."""
        import time
        import uuid
        
        response = ChatCompletionResponse(
            id=str(uuid.uuid4()),
            choices=[{
                "index": 0,
                "message": {"role": "assistant", "content": "Test"},
                "finish_reason": "stop"
            }],
            created=int(time.time()),
            model="qwopus",
            usage={
                "prompt_tokens": 5,
                "completion_tokens": 10,
                "total_tokens": 15
            }
        )
        
        data = response.model_dump()
        
        assert "id" in data
        assert "choices" in data
        assert "created" in data
        assert "model" in data
        assert "object" in data
        assert "usage" in data
    
    def test_response_finish_reasons(self) -> None:
        """Valid finish reasons are accepted."""
        import time
        import uuid
        
        valid_finish_reasons = ["stop", "length", "tool_calls", None]
        
        for reason in valid_finish_reasons:
            response = ChatCompletionResponse(
                id=str(uuid.uuid4()),
                choices=[{
                    "index": 0,
                    "message": {"role": "assistant", "content": "Test"},
                    "finish_reason": reason
                }],
                created=int(time.time()),
                model="qwopus",
                usage={
                    "prompt_tokens": 5,
                    "completion_tokens": 10,
                    "total_tokens": 15
                }
            )
            assert response.choices[0].finish_reason == reason


# =============================================================================
# USAGE MODEL TESTS
# =============================================================================


class TestChatUsage:
    """Tests for ChatUsage model."""
    
    def test_usage_defaults(self) -> None:
        """Usage model has correct defaults."""
        usage = ChatUsage()
        
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0
    
    def test_usage_with_values(self) -> None:
        """Usage model with explicit values works."""
        usage = ChatUsage(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15
        )
        
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 15
    
    def test_usage_total_calculation(self) -> None:
        """Total tokens equals sum of prompt and completion."""
        usage = ChatUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        
        assert usage.total_tokens == (
            usage.prompt_tokens + usage.completion_tokens
        )


# =============================================================================
# CHOICE MODEL TESTS
# =============================================================================


class TestChoice:
    """Tests for Choice model."""
    
    def test_choice_minimum_valid(self) -> None:
        """Minimum valid choice is created."""
        choice = Choice(
            index=0,
            message={"role": "assistant", "content": "Test"},
            finish_reason="stop"
        )
        
        assert choice.index == 0
        assert choice.message.role == "assistant"
        assert choice.finish_reason == "stop"
    
    def test_choice_with_logprobs(self) -> None:
        """Choice with logprobs is valid."""
        choice = Choice(
            index=0,
            message={"role": "assistant", "content": "Test"},
            finish_reason="stop",
            logprobs={
                "tokens": ["test", "token"],
                "token_logprobs": [-0.1, -0.2]
            }
        )
        
        assert choice.logprobs is not None
    
    def test_choice_serialization(self) -> None:
        """Choice serializes to dict correctly."""
        choice = Choice(
            index=0,
            message={"role": "assistant", "content": "Test"}
        )
        
        data = choice.model_dump()
        
        assert "index" in data
        assert "message" in data
        assert "finish_reason" in data


# =============================================================================
# MODEL RESPONSE TESTS
# =============================================================================


class TestModelResponse:
    """Tests for ModelResponse model."""
    
    def test_model_response_minimum_valid(self) -> None:
        """Minimum valid model response is created."""
        import time
        
        response = ModelResponse(
            id="qwopus",
            created=int(time.time()),
            owned_by="qwopus"
        )
        
        assert response.id == "qwopus"
        assert response.object == "model"
        assert response.owned_by == "qwopus"
    
    def test_model_response_with_custom_id(self) -> None:
        """Model response with custom ID is valid."""
        import time
        
        response = ModelResponse(
            id="custom-model-id",
            created=int(time.time()),
            owned_by="kimikazee"
        )
        
        assert response.id == "custom-model-id"
        assert response.owned_by == "kimikazee"


# =============================================================================
# HEALTH RESPONSE TESTS
# =============================================================================


class TestHealthResponse:
    """Tests for HealthResponse model."""
    
    def test_health_response_healthy(self) -> None:
        """Healthy status is default."""
        response = HealthResponse(model_loaded=True)
        
        assert response.status == "healthy"
        assert response.model_loaded is True
    
    def test_health_response_degraded(self) -> None:
        """Degraded status works."""
        response = HealthResponse(model_loaded=False, status="degraded")
        
        assert response.status == "degraded"
        assert response.model_loaded is False
    
    def test_health_response_serialization(self) -> None:
        """Health response serializes correctly."""
        import json
        response = HealthResponse(model_loaded=True)
        
        json_str = response.model_dump_json()
        data = json.loads(json_str)
        
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True
        assert data["version"] == "1.0.0"


# =============================================================================
# STREAM RESPONSE TESTS
# =============================================================================


class TestChatCompletionStreamResponse:
    """Tests for streaming response models."""
    
    def test_stream_response_valid(self) -> None:
        """Valid streaming response is created."""
        import time
        import uuid
        
        response = ChatCompletionStreamResponse(
            id=str(uuid.uuid4()),
            choices=[{
                "index": 0,
                "delta": {"role": "assistant", "content": "Test"}
            }],
            created=int(time.time()),
            model="qwopus"
        )
        
        assert response.object == "chat.completion.chunk"
        assert len(response.choices) == 1
    
    def test_stream_response_multiple_choices(self) -> None:
        """Streaming response with multiple choices is valid."""
        import time
        import uuid
        
        response = ChatCompletionStreamResponse(
            id=str(uuid.uuid4()),
            choices=[
                ChatCompletionStreamChoice(
                    index=0,
                    delta=ChatMessage(role="assistant", content="Choice 1")
                ),
                ChatCompletionStreamChoice(
                    index=1,
                    delta=ChatMessage(role="assistant", content="Choice 2")
                )
            ],
            created=int(time.time()),
            model="qwopus"
        )
        
        assert len(response.choices) == 2
    
    def test_stream_response_empty_content(self) -> None:
        """Streaming response with empty content is valid."""
        import time
        import uuid
        
        response = ChatCompletionStreamResponse(
            id=str(uuid.uuid4()),
            choices=[{
                "index": 0,
                "delta": ChatMessage(role="assistant", content="")
            }],
            created=int(time.time()),
            model="qwopus"
        )
        
        assert response.choices[0].delta.content == ""


class TestChatCompletionStreamChoice:
    """Tests for streaming choice model."""
    
    def test_stream_choice_valid(self) -> None:
        """Valid streaming choice is created."""
        choice = ChatCompletionStreamChoice(
            index=0,
            delta=ChatMessage(role="assistant", content="Test"),
            finish_reason=None
        )
        
        data = choice.model_dump(exclude_none=True)
        assert data["index"] == 0
        assert choice.delta.role == "assistant"
        assert choice.delta.content == "Test"
    
    def test_stream_choice_with_finish_reason(self) -> None:
        """Streaming choice with finish reason is valid."""
        choice = ChatCompletionStreamChoice(
            index=0,
            delta=ChatMessage(role="assistant", content=""),
            finish_reason="stop"
        )
        
        assert choice.finish_reason == "stop"


# =============================================================================
# EDGE CASES AND BOUNDARY VALUES
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary values."""
    
    def test_empty_string_content(self) -> None:
        """Empty string content is valid."""
        message = ChatMessage(role="user", content="")
        assert message.content == ""
    
    def test_very_long_content(self) -> None:
        """Very long content is handled."""
        long_content = "x" * 10000
        message = ChatMessage(role="user", content=long_content)
        assert len(message.content) == 10000
    
    def test_special_characters_in_content(self) -> None:
        """Special characters in content are handled."""
        special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        message = ChatMessage(role="user", content=special)
        assert message.content == special
    
    def test_json_in_content(self) -> None:
        """JSON string in content is valid."""
        import json
        json_str = json.dumps({"key": "value", "number": 123})
        message = ChatMessage(role="user", content=json_str)
        assert message.content == json_str
    
    def test_request_with_none_values(self) -> None:
        """Request with None optional values works."""
        request = ChatCompletionRequest(
            messages=[{"role": "user", "content": "Test"}],
            temperature=None,
            top_p=None,
            max_tokens=None,
            stop=None,
            stream=None,
            user=None
        )
        
        assert request.temperature is None
        assert request.top_p is None
    
    def test_response_serialization_exclude_none(self) -> None:
        """Response can exclude None values."""
        import time
        import uuid
        
        response = ChatCompletionResponse(
            id=str(uuid.uuid4()),
            choices=[{
                "index": 0,
                "message": {"role": "assistant", "content": "Test"},
                "finish_reason": None
            }],
            created=int(time.time()),
            model="qwopus",
            usage={
                "prompt_tokens": 5,
                "completion_tokens": 10,
                "total_tokens": 15
            }
        )
        
        data = response.model_dump(exclude_none=True)
        assert "finish_reason" not in data["choices"][0]


# =============================================================================
# MODEL COMPARISON TESTS
# =============================================================================


class TestModelComparison:
    """Tests for model comparison operations."""
    
    def test_messages_equal(self) -> None:
        """Equal messages are equal."""
        msg1 = ChatMessage(role="user", content="Hello")
        msg2 = ChatMessage(role="user", content="Hello")
        
        assert msg1 == msg2
    
    def test_messages_not_equal(self) -> None:
        """Different messages are not equal."""
        msg1 = ChatMessage(role="user", content="Hello")
        msg2 = ChatMessage(role="user", content="World")
        
        assert msg1 != msg2
    
    def test_request_deep_copy(self) -> None:
        """Request model supports deep operations."""
        import copy
        request1 = ChatCompletionRequest(
            messages=[{"role": "user", "content": "Test"}]
        )
        
        request2 = copy.deepcopy(request1)
        
        assert request1.messages[0].content == request2.messages[0].content
        request2.messages[0].content = "Modified"
        assert request1.messages[0].content == "Test"


# =============================================================================
# HELPERS
# =============================================================================


def test_pydantic_version_compatible():
    """Verify Pydantic version is compatible."""
    import pydantic
    from packaging import version
    
    # Should work with Pydantic v2.x
    assert version.parse(pydantic.__version__) >= version.parse("2.0.0")
