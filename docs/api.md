# 📚 Kimikazee Qwopus API Reference

API documentation for the Kimikazee Qwopus OpenAI-compatible server.

---

## Table of Contents

- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [List Models](#list-models)
  - [Chat Completions](#chat-completions)
- [Request/Response Schemas](#requestresponse-schemas)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)
- [Streaming Guide](#streaming-guide)

---

## Overview

Kimikazee Qwopus provides an OpenAI-compatible REST API for interacting with the Qwen3.5-9B-Uncensored model. The API supports both standard and streaming responses, with full control over generation parameters.

### Features

- ✅ OpenAI-compatible `/v1/chat/completions` endpoint
- ✅ Server-Sent Events (SSE) streaming
- ✅ CORS support for cross-origin requests
- ✅ Structured logging and monitoring
- ✅ Graceful shutdown handling
- ✅ Model loading with lazy initialization

---

## Base URL

The default server URL is:

```
http://localhost:8080
```

### Configuration

The base URL can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `QWOPUS_HOST` | `0.0.0.0` | Host to bind to |
| `QWOPUS_PORT` | `8080` | Port to listen on |
| `QWOPUS_CONFIG` | `config.yaml` | Path to config file |

Example with Docker:
```bash
docker run -p 8080:8080 -e QWOPUS_HOST=0.0.0.0 -e QWOPUS_PORT=8080 kimikazee/qwopus
```

---

## Authentication

**Currently, Kimikazee Qwopus does not require authentication.** The API is designed for local/private deployments where network security provides access control.

For production deployments, we recommend:

1. Running behind a reverse proxy with authentication (nginx, Traefik)
2. Using API keys via middleware
3. Restricting access via firewall rules
4. Using TLS/HTTPS encryption

### Adding Authentication (Advanced)

To add API key authentication, you can create a middleware:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    expected_key = os.environ.get("API_KEY")
    if credentials.credentials != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials

@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
```

---

## Endpoints

### Health Check

Check the server's health status and model availability.

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Server is healthy |
| 200 (with `model_loaded: false`) | Server is running but model is loading |

**cURL Example:**
```bash
curl http://localhost:8080/health
```

---

### List Models

List available models for chat completions.

**Endpoint:** `GET /v1/models`

**Response:**

```json
[
  {
    "id": "Qwen3.5-9B-Uncensored-Q8_0.gguf",
    "object": "model",
    "created": 1714387200,
    "owned_by": "qwopus"
  }
]
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |

**cURL Example:**
```bash
curl http://localhost:8080/v1/models
```

---

### Chat Completions

Generate chat completions using the Qwen3.5-9B-Uncensored model.

**Endpoint:** `POST /v1/chat/completions`

**Request Body:**

```json
{
  "model": "qwopus",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 40,
  "max_tokens": null,
  "stop": null,
  "stream": false
}
```

**Response (non-streaming):**

```json
{
  "id": "chatcmpl-abc123",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking."
      },
      "finish_reason": "stop"
    }
  ],
  "created": 1714387200,
  "model": "qwopus",
  "object": "chat.completion",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 12,
    "total_tokens": 27
  }
}
```

**Response (streaming):**

```
data: {"id":"chatcmpl-abc123","choices":[{"delta":{"role":"assistant","content":"Hello"},"finish_reason":null}],"created":1714387200,"model":"qwopus","object":"chat.completion.chunk"}

data: {"id":"chatcmpl-abc123","choices":[{"delta":{"content":"!"},"finish_reason":null}],"created":1714387200,"model":"qwopus","object":"chat.completion.chunk"}

data: {"id":"chatcmpl-abc123","choices":[{"delta":{"content":" I'm"},"finish_reason":null}],"created":1714387200,"model":"qwopus","object":"chat.completion.chunk"}

data: {"id":"chatcmpl-abc123","choices":[{"delta":{"content":" doing"},"finish_reason":null}],"created":1714387200,"model":"qwopus","object":"chat.completion.chunk"}

data: {"id":"chatcmpl-abc123","choices":[{"delta":{"content":" well"},"finish_reason":null}],"created":1714387200,"model":"qwopus","object":"chat.completion.chunk"}

data: {"id":"chatcmpl-abc123","choices":[{"delta":{"content":"."},"finish_reason":"stop"}],"created":1714387200,"model":"qwopus","object":"chat.completion.chunk"}

data: {"choices":[{"finish_reason":"stop","index":0}],"id":"chatcmpl-abc123","model":"qwopus","created":1714387200,"object":"chat.completion.chunk"}

[DONE]
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Invalid request parameters |
| 422 | Validation error (Pydantic) |
| 503 | Model not loaded |
| 500 | Server error during generation |

**cURL Example (non-streaming):**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwopus",
    "messages": [
      {"role": "user", "content": "What is deep learning?"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

**cURL Example (streaming):**
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwopus",
    "messages": [
      {"role": "user", "content": "What is deep learning?"}
    ],
    "temperature": 0.7,
    "stream": true
  }'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8080/v1/chat/completions",
    json={
        "model": "qwopus",
        "messages": [
            {"role": "user", "content": "Explain quantum computing"}
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }
)

result = response.json()
print(result["choices"][0]["message"]["content"])
```

---

## Request/Response Schemas

### ChatMessage

Represents a message in the conversation.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `role` | string | Yes | - | One of: `user`, `assistant`, `system`, `tool` |
| `content` | string or array | Yes | - | Message content (text or multimodal) |

### ChatCompletionRequest

| Field | Type | Required | Default | Min | Max | Description |
|-------|------|----------|---------|-----|-----|-------------|
| `model` | string | No | `"qwopus"` | - | - | Model identifier |
| `messages` | array | Yes | - | 1 item | - | List of conversation messages |
| `temperature` | float | No | `0.7` | `0.0` | `2.0` | Controls randomness |
| `top_p` | float | No | `0.9` | `0.0` | `1.0` | Nucleus sampling threshold |
| `top_k` | int | No | `40` | `1` | `100` | Limit to top-k tokens |
| `max_tokens` | int | No | `null` | `1` | - | Max tokens to generate (-1 for unlimited) |
| `stop` | array of string | No | `null` | - | - | Stop sequences |
| `stream` | boolean | No | `false` | - | - | Enable streaming |
| `stream_options` | object | No | `null` | - | - | Streaming options |
| `frequency_penalty` | float | No | `0.0` | `-2.0` | `2.0` | Token frequency penalty |
| `presence_penalty` | float | No | `0.0` | `-2.0` | `2.0` | Token presence penalty |
| `response_format` | object | No | `null` | - | - | JSON mode specification |
| `seed` | int | No | `null` | - | - | Random seed for reproducibility |
| `logit_bias` | object | No | `null` | - | - | Token logit bias |
| `user` | string | No | `null` | - | - | End-user identifier |

### ChatCompletionResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique completion identifier |
| `choices` | array | List of response choices |
| `created` | int | Unix timestamp |
| `model` | string | Model identifier |
| `object` | string | Object type (`"chat.completion"`) |
| `usage` | object | Token usage statistics |

### ChatUsage

| Field | Type | Description |
|-------|------|-------------|
| `prompt_tokens` | int | Tokens in input |
| `completion_tokens` | int | Tokens generated |
| `total_tokens` | int | Total tokens used |

### Choice

| Field | Type | Description |
|-------|------|-------------|
| `index` | int | Choice index |
| `message` | object | Assistant response |
| `finish_reason` | string | One of: `stop`, `length`, `tool_calls`, `content_filter` |
| `logprobs` | object | Token log probabilities (optional) |

---

## Error Codes

All errors follow the OpenAI error format:

```json
{
  "error": {
    "type": "error_type",
    "message": "Human-readable error message",
    "code": 400
  }
}
```

| Type | HTTP Code | Description |
|------|-----------|-------------|
| `invalid_request_error` | 400 | Invalid request parameters |
| `validation_error` | 422 | Pydantic validation failed |
| `service_unavailable` | 503 | Model not loaded, server starting |
| `internal_error` | 500 | Server-side generation error |
| `authentication_error` | 401 | Missing or invalid authentication |

**Error Response Example:**
```json
{
  "error": {
    "type": "service_unavailable",
    "message": "Model not loaded. Server is starting up.",
    "code": 503
  }
}
```

---

## Rate Limiting

**By default, Kimikazee Qwopus does not implement rate limiting.** This is intentional for local/private deployments.

### Recommended Rate Limiting Setup

For production deployments, implement rate limiting at the reverse proxy level:

**Nginx Example:**
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /v1/ {
    limit_req zone=api burst=20 nodelay;
    
    proxy_pass http://localhost:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

**Uvicorn with rate limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter

@app.post("/v1/chat/completions", dependencies=[Depends(limiter.limit("10/minute"))])
```

### Recommended Limits

| Metric | Recommended Value | Notes |
|--------|-------------------|-------|
| Requests per minute | 10-60 | Depends on hardware |
| Tokens per minute | 1000-10000 | Depends on context |
| Concurrent connections | 5-20 | Depends on VRAM |

---

## Streaming Guide

### SSE (Server-Sent Events)

Streaming enables real-time token display, reducing perceived latency.

#### Enable Streaming

Set `stream: true` in the request:

```json
{
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": true
}
```

#### SSE Format

Each chunk is sent as a Server-Sent Event:

```
data: {...}\n\n
```

The final event includes `[DONE]` signal.

#### Python Streaming Client

```python
import requests

response = requests.post(
    "http://localhost:8080/v1/chat/completions",
    json={
        "model": "qwopus",
        "messages": [{"role": "user", "content": "Tell me a story"}],
        "stream": true
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = line.decode("utf-8")[6:]  # Remove "data: " prefix
        if data == "[DONE]":
            break
        
        chunk = json.loads(data)
        content = chunk["choices"][0]["delta"].get("content", "")
        print(content, end="", flush=True)
```

#### Node.js Streaming Client

```javascript
const response = await fetch('http://localhost:8080/v1/chat/completions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'qwopus',
    messages: [{ role: 'user', content: 'Tell me a story' }],
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ') && line !== 'data: [DONE]') {
      const data = JSON.parse(line.slice(6));
      const content = data.choices[0]?.delta?.content || '';
      process.stdout.write(content);
    }
  }
}
```

---

## Performance Tips

1. **Streaming:** Use streaming for better UX on long responses
2. **Max Tokens:** Set reasonable `max_tokens` to control output length
3. **Temperature:** Lower values (0.2-0.5) for more deterministic output
4. **Context Window:** 128K max, but smaller windows are faster
5. **GPU Offload:** Set `n_gpu_layers: -1` for full GPU utilization

---

## Related Documentation

- [Configuration Guide](/root/repos/kimikazee-qwopus/docs/configuration.md)
- [Deployment Guide](/root/repos/kimikazee-qwopus/docs/deployment.md)
- [Usage Examples](/root/repos/kimikazee-qwopus/examples/)

---

## Support

- **GitHub Issues:** [kimikazee/kimikazee-qwopus/issues](https://github.com/kimikazee/kimikazee-qwopus/issues)
- **Documentation:** [Kimikazee Qwopus Docs](https://kimikazee.github.io/kimikazee-qwopus)

---

*Last updated: 2026-04-30 | Version: 1.0.0*
