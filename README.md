# 🐙 Kimikazee Qwopus

### A NEW BREED OF INTELLIGENCE

<div align="center">

![Kimikazee Qwopus](./assets/qwopus-branding.png)

</div>

---

<div align="center">

**Hyper Agents. Super Fast. Red Team Ready.**
<br/>
**Abliterated. Uncensored.**
<br/>
**Blazing Fast Hyper Agent Swarms**

</div>

---

## 🔧 Quick Stats

<div align="center">

| Metric | Value |
|--------|-------|
| **Model** | Qwen3.5-9B-Uncensored |
| **Context Window** | 128K tokens |
| **API** | OpenAI-compatible |
| **License** | MIT |
| **Python** | 3.10+ |
| **Status** | 🟢 Stable |

</div>

---

## 📦 Installation & Quick Start

### Prerequisites

- Python 3.10 or higher
- pip or conda
- Git
- Optional: NVIDIA GPU (RTX 3060+ recommended)

### Install from pip

```bash
# Install the package
pip install kimikazee-qwopus

# Run the server
qwopus
```

### Install from source

```bash
# Clone repository
git clone https://github.com/kimikazee/kimikazee-qwopus.git
cd kimikazee-qwopus

# Install dependencies
pip install -r requirements.txt

# Download model (optional - will load on first request)
# Place Qwen3.5-9B-Uncensored-Q8_0.gguf in project root or ~/.models/

# Run server
python -m server
```

### Docker Deployment

```bash
# Run with Docker
docker run -d \
  --name qwopus \
  -p 8080:8080 \
  kimikazee/qwopus:latest

# Or with model volume
docker run -d \
  --name qwopus \
  -p 8080:8080 \
  -v $(pwd)/models:/models \
  -e MODEL_PATH=/models/Qwen3.5-9B-Uncensored-Q8_0.gguf \
  kimikazee/qwopus:latest
```

### Verification

```bash
# Health check
curl http://localhost:8080/health

# Expected response:
# {"status":"healthy","model_loaded":true,"version":"1.0.0"}
```

---

## 🚀 Features

| Icon | Feature | Description |
|------|---------|-------------|
| 💬 | **Chat & Communication** | Natural conversation, multi-turn dialog |
| 💻 | **Code & Development** | Programming assistance, code generation |
| 📚 | **Knowledge Base** | Extensive reasoning over large contexts |
| 📊 | **Analytics & Performance** | Optimized for speed and efficiency |
| 🎨 | **Creativity & Design** | Creative writing, brainstorming, ideas |
| 🌐 | **Global Reach** | Web-enabled, information synthesis |
| ⚡ | **Streaming** | Real-time token generation via SSE |
| 🔧 | **Flexible API** | OpenAI-compatible endpoints |

---

## 🤖 Model Information

This project runs on **Qwen3.5-9B-Uncensored-Q8_0.gguf**, a highly optimized quantized model designed for local inference with maximum capability and zero restrictions.

### VRAM Optimizations

- ✅ Optimized for RTX 4080 Super (16GB)
- ✅ llama.cpp backend with flash attention
- ✅ Parallel inference support
- ✅ Adaptive context window management
- ✅ GPU offloading (configurable layers)
- ✅ CPU fallback mode

### Performance Benchmarks

| Hardware | Tokens/sec | Memory Usage |
|----------|------------|--------------|
| RTX 4090 (24GB) | 80-120 | ~12GB VRAM |
| RTX 3060 (12GB) | 40-60 | ~10GB VRAM |
| M2 Max (32GB) | 30-50 | ~8GB RAM |
| CPU Only (16-core) | 10-20 | ~18GB RAM |

---

## 🛠️ Usage Examples

### Python Client

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

print(response.json()["choices"][0]["message"]["content"])
```

### Streaming Response

```python
response = requests.post(
    "http://localhost:8080/v1/chat/completions",
    json={
        "model": "qwopus",
        "messages": [{"role": "user", "content": "Tell a story"}],
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8')[6:])
        content = data["choices"][0]["delta"].get("content", "")
        print(content, end="", flush=True)
```

### cURL

```bash
# Simple chat
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwopus",
    "messages": [{"role": "user", "content": "What is AI?"}],
    "temperature": 0.7
  }'
```

### Node.js Client

```javascript
const response = await fetch('http://localhost:8080/v1/chat/completions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'qwopus',
    messages: [{ role: 'user', content: 'Hello!' }]
  })
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

---

## 📚 Configuration

### Quick Config

```yaml
# config.yaml
model: Qwen3.5-9B-Uncensored-Q8_0.gguf
context_window: 128000
parallel: 4
temp: 0.7
top_p: 0.9
top_k: 40
n_gpu_layers: -1  # Full GPU offload (requires 16GB+ VRAM)
log_level: INFO
```

### Environment Variables

```bash
export QWOPUS_PORT=8080
export QWOPUS_HOST=0.0.0.0
export LOG_LEVEL=INFO
export MODEL_PATH=/path/to/model.gguf
```

For full configuration reference, see [Configuration Guide](docs/configuration.md).

---

## 📖 Documentation

Complete documentation is available in the `/docs` directory:

| Documentation | Description |
|---------------|-------------|
| [API Reference](docs/api.md) | Complete API endpoint documentation |
| [Configuration Guide](docs/configuration.md) | Full config options explained |
| [Deployment Guide](docs/deployment.md) | Docker, Kubernetes, production setup |
| [Usage Examples](examples/) | Python, Node.js, cURL examples |

### API Endpoints

- `GET /health` - Health check and model status
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completions (streaming & non-streaming)
- `GET /docs` - OpenAPI/Swagger documentation
- `GET /redoc` - ReDoc documentation

---

## 🔧 Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
make test
make coverage

# Format code
make format
```

### Makefile Commands

```bash
make run      # Quick start server
make server   # Production server
make dev      # Development mode with auto-reload
make test     # Run all tests
make coverage # Run tests with coverage report
make clean    # Clean build artifacts
```

---

## 🛡️ Security

### Security Best Practices

- Run behind reverse proxy with TLS
- Implement API key authentication
- Configure rate limiting
- Use firewall rules to restrict access
- Keep dependencies updated
- Monitor logs for suspicious activity

For detailed security guidelines, see [Security Policy](SECURITY.md).

---

## 🐛 Troubleshooting

### Common Issues

#### Model Not Loading

**Symptoms:** `/health` returns `model_loaded: false`

**Solutions:**
1. Check model file exists: `ls -la Qwen3.5-9B-Uncensored-Q8_0.gguf`
2. Verify file permissions: `chmod +r model.gguf`
3. Check model path in config
4. Increase context window if OOM

#### Out of Memory

**Symptoms:** Server crashes with CUDA OOM error

**Solutions:**
```yaml
# Reduce GPU layers
n_gpu_layers: 40  # Instead of -1

# Reduce context window
context_window: 32000

# Use smaller quantization
model: Qwen3.5-9B-Uncensored-Q4_K_M.gguf
```

#### Slow Performance

**Solutions:**
```yaml
# Enable flash attention
flash_attn: true

# Full GPU offload
n_gpu_layers: -1

# Increase parallel threads
n_threads: 16
```

For more troubleshooting tips, see [Deployment Guide](docs/deployment.md#troubleshooting).

---

## ❓ FAQ

### What is Kimikazee Qwopus?

Kimikazee Qwopus is a production-ready FastAPI server for running Qwen3.5-9B-Uncensored models via llama-cpp-python. It provides OpenAI-compatible endpoints with SSE streaming support.

### Is authentication required?

No, Qwopus does not require authentication by default. For production use, we recommend implementing authentication via reverse proxy or middleware.

### What models are supported?

Primary model: **Qwen3.5-9B-Uncensored-Q8_0.gguf**

Other quantized versions of Qwen3.5-9B are also supported.

### Can I use this in production?

Yes, Qwopus is production-ready but requires proper security configuration:
- Use HTTPS/TLS
- Implement rate limiting
- Add authentication
- Monitor resource usage
- Set up logging and alerts

### Does it support streaming?

Yes! Qwopus supports Server-Sent Events (SSE) for real-time token streaming.

### What are the system requirements?

**Minimum:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 10GB

**Recommended:**
- CPU: 8+ cores
- RAM: 16GB
- GPU: RTX 3060 (12GB) or better
- Storage: 50GB SSD

### How do I contribute?

See [Contributing Guide](CONTRIBUTING.md) for details on how to contribute.

---

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- How to submit bugs and feature requests
- Development workflow
- Code style guidelines
- Pull request process

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- **Qwen Team** for the Qwen3.5-9B-Uncensored model
- **llama-cpp-python** team for the inference backend
- **FastAPI** team for the web framework
- **Kimikazee Team** for the development and maintenance

---

## 🔗 Links

- **GitHub:** [kimikazee/kimikazee-qwopus](https://github.com/kimikazee/kimikazee-qwopus)
- **API Docs:** http://localhost:8080/docs (when running locally)
- **Issues:** [Report a bug](https://github.com/kimikazee/kimikazee-qwopus/issues)
- **Documentation:** [kimikazee.github.io/kimikazee-qwopus](https://kimikazee.github.io/kimikazee-qwopus)

---

<div align="center">

**Made with 💜 by the Kimikazee Team**
<br/>
*Powered by Qwen • Built for Speed • Unleashed Intelligence*

</div>
