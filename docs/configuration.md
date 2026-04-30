# ⚙️ Kimikazee Qwopus Configuration Guide

Complete configuration reference for Kimikazee Qwopus.

---

## Table of Contents

- [Overview](#overview)
- [Configuration File](#configuration-file)
  - [Location](#location)
  - [Loading Configuration](#loading-configuration)
  - [Environment Variable Substitution](#environment-variable-substitution)
- [Configuration Options](#configuration-options)
  - [Model Provider Settings](#model-provider-settings)
  - [Context & Inference](#context--inference)
  - [llama.cpp Optimizations](#llama-cpp-optimizations)
  - [Discord Integration](#discord-integration)
  - [Telegram Integration](#telegram-integration)
  - [Logging](#logging)
  - [Agent Swarm Settings](#agent-swarm-settings)
- [Environment Variables](#environment-variables)
- [Performance Tuning](#performance-tuning)
- [Example Configurations](#example-configurations)
- [Troubleshooting](#troubleshooting)

---

## Overview

Kimikazee Qwopus uses a YAML configuration file to manage server settings, model parameters, and integration options. The configuration is loaded at startup and can be overridden with environment variables.

### File Location

Default location: `config.yaml` in the project root.

Custom location via environment variable:
```bash
export QWOPUS_CONFIG=/path/to/config.yaml
python -m server
```

---

## Configuration File

### Loading Configuration

The configuration loader supports:

1. **YAML syntax** with standard YAML features
2. **Environment variable substitution** using `${VAR_NAME}` syntax
3. **Default values** for optional settings

### Example config.yaml

```yaml
# Kimikazee Qwopus Configuration
# ===============================

# Model Provider Settings
provider: custom  # Options: 'custom', 'qwopus', 'openrouter', 'kimi'
model: Qwen3.5-9B-Uncensored-Q8_0.gguf

# Context & Inference
context_window: 128000
parallel: 4
n_predict: -1  # Generate until max context or stop token
temp: 0.7  # Temperature (0.0 - 2.0)
top_p: 0.9
top_k: 40

# llama.cpp Optimizations (DO NOT CHANGE these!)
flash_attn: true  # Use -ngl when starting llama.cpp
n_threads: 8  # Auto-detect based on hardware
n_gpu_layers: 0  # GPU offload, set to -1 for all layers

# Discord Integration (when deployed as bot)
discord:
  require_mention: false  # NEVER change to true
  free_response_channels: "*"  # Respond to ALL channels

# Telegram Integration
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"  # Set via .env
  allow_groups: true

# Logging
log_level: INFO
log_file: ~/.hermes-beta/logs/agent.log

# Agent Swarm Settings (future feature)
max_parallel_agents: 4
agent_timeout: 300  # seconds
```

---

## Configuration Options

### Model Provider Settings

Configure which model provider to use.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `provider` | string | `custom` | Provider type: `custom`, `qwopus`, `openrouter`, `kimi` |
| `model` | string | `Qwen3.5-9B-Uncensored-Q8_0.gguf` | Model file name or identifier |

**Valid Providers:**

- `custom`: Use local model files (default)
- `qwopus`: Use Kimikazee Qwopus cloud provider
- `openrouter`: Route through OpenRouter API
- `kimi`: Use Moonshot AI's Kimi model

**Example:**
```yaml
provider: openrouter
model: meta-llama/llama-3-70b-instruct
```

---

### Context & Inference

Control the model's context window and inference behavior.

| Key | Type | Default | Range | Description |
|-----|------|---------|-------|-------------|
| `context_window` | int | `128000` | 1-128000 | Maximum context length in tokens |
| `parallel` | int | `4` | 1-32 | Number of parallel sequences |
| `n_predict` | int | `-1` | -1, 1-∞ | Max tokens to generate (-1 = unlimited) |
| `temp` | float | `0.7` | 0.0-2.0 | Sampling temperature |
| `top_p` | float | `0.9` | 0.0-1.0 | Nucleus sampling threshold |
| `top_k` | int | `40` | 1-100 | Limit to top-k tokens |

#### Temperature (`temp`)

Controls output randomness:

- `0.0`: Deterministic (greedy decoding)
- `0.1-0.5`: Highly focused, factual
- `0.5-0.7`: Balanced, recommended default
- `0.7-1.0`: Creative, varied
- `1.0-2.0`: Very creative, unpredictable

**Example:**
```yaml
temp: 0.8  # Slightly more creative
```

#### Top-P (`top_p`)

Nucleus sampling: includes tokens with cumulative probability ≤ `top_p`.

- `0.5`: Very selective
- `0.7-0.9`: Balanced (recommended)
- `1.0`: Include all tokens

**Example:**
```yaml
top_p: 0.95  # Include 95% probability mass
```

#### Top-K (`top_k`)

Limits sampling to top-k most probable tokens.

- `1-10`: Very focused
- `20-50`: Balanced (recommended)
- `50-100`: More varied

**Example:**
```yaml
top_k: 30  # Limit to top 30 tokens
```

**Combined Settings Example:**
```yaml
temp: 0.7
top_p: 0.9
top_k: 40
```

---

### llama.cpp Optimizations

These parameters control llama-cpp-python backend performance.

⚠️ **WARNING:** These settings are optimized for production. Changing them may degrade performance or cause issues.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `flash_attn` | boolean | `true` | Enable flash attention (requires CUDA 11+) |
| `n_threads` | int | `8` | CPU threads for inference |
| `n_gpu_layers` | int | `0` | GPU layers to offload (-1 for all) |

#### Flash Attention (`flash_attn`)

Enables flash attention optimization for faster inference.

- `true`: Use flash attention (recommended if supported)
- `false`: Standard attention

**Requirements:**
- CUDA 11.0+
- Compatible GPU (RTX 20-series or newer recommended)

**Example:**
```yaml
flash_attn: true  # Enable if your GPU supports it
```

#### GPU Layers (`n_gpu_layers`)

Controls GPU memory offloading:

- `0`: CPU only
- `N`: Offload N layers to GPU
- `-1`: Offload ALL layers to GPU

**Recommended GPU Settings:**

| GPU VRAM | n_gpu_layers |
|----------|--------------|
| 4GB | 20-30 |
| 8GB | 40-50 |
| 12GB | 60-70 |
| 16GB | 80-90 |
| 24GB+ | -1 (all layers) |

**Example:**
```yaml
n_gpu_layers: -1  # Full GPU offload (requires 16GB+ VRAM)
```

#### Threads (`n_threads`)

Number of CPU threads:

- **Auto-detect:** Set to number of physical cores
- **Hybrid systems:** Match physical cores (not hyperthreads)
- **Overclocking:** Set to 1-2 less than max for headroom

**Example:**
```yaml
n_threads: 16  # For 16-core CPU
```

**Complete llama.cpp Configuration:**
```yaml
flash_attn: true
n_threads: 12
n_gpu_layers: -1
```

---

### Discord Integration

Configure Discord bot behavior (if deployed as bot).

⚠️ **IMPORTANT:** `require_mention` should remain `false` for public deployments.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `discord.require_mention` | boolean | `false` | Require @mention to respond |
| `discord.free_response_channels` | string | `"*"` | Channel patterns to respond to |

**Channel Patterns:**

- `"*"`: All channels
- `"general"`: Specific channel
- `"general,random"`: Multiple channels
- `["general", "random"]`: Array format

**Example:**
```yaml
discord:
  require_mention: false
  free_response_channels: ["general", "random", "tech"]
```

---

### Telegram Integration

Configure Telegram bot settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `telegram.bot_token` | string | - | Bot token from @BotFather |
| `telegram.allow_groups` | boolean | `true` | Allow responses in groups |

**Getting Telegram Bot Token:**

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow prompts to create bot
4. Copy the API token

**Example:**
```yaml
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  allow_groups: true
```

---

### Logging

Configure logging levels and output.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `log_level` | string | `"INFO"` | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `log_file` | string | `"~/.hermes-beta/logs/agent.log"` | Log file path |

**Log Levels:**

- `DEBUG`: Detailed debugging information
- `INFO`: General operation (default)
- `WARNING`: Potential issues
- `ERROR`: Errors that don't stop operation
- `CRITICAL`: Critical errors requiring attention

**Example:**
```yaml
log_level: DEBUG  # Enable debug logging
log_file: /var/log/qwopus/agent.log
```

**Log Format:**
```
2026-04-30 10:30:45 | INFO     | qwopus.server:684 | Kimikazee Qwopus Server Starting Up
```

---

### Agent Swarm Settings

Future multi-agent orchestration settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_parallel_agents` | int | `4` | Maximum concurrent agents |
| `agent_timeout` | int | `300` | Timeout in seconds |

**Example:**
```yaml
max_parallel_agents: 8
agent_timeout: 600
```

---

## Environment Variables

All configuration can be overridden with environment variables.

### Server Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QWOPUS_HOST` | `0.0.0.0` | Bind address |
| `QWOPUS_PORT` | `8080` | Port to listen on |
| `QWOPUS_CONFIG` | `config.yaml` | Path to config file |
| `QWOPUS_EXTERNAL` | - | Set to `true` for external access |

### Model Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | - | Custom model path |
| `LLAMA_CPP_PATH` | - | Custom llama.cpp binary |

### Integration Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | - | Telegram bot API token |
| `DISCORD_BOT_TOKEN` | - | Discord bot token |

### Usage Examples

**Shell:**
```bash
export QWOPUS_PORT=9000
export QWOPUS_HOST=127.0.0.1
python -m server
```

**Docker:**
```bash
docker run -p 9000:9000 \
  -e QWOPUS_PORT=9000 \
  -e QWOPUS_HOST=0.0.0.0 \
  -e TELEGRAM_BOT_TOKEN=your_token \
  kimikazee/qwopus
```

**Compose:**
```yaml
version: '3.8'
services:
  qwopus:
    image: kimikazee/qwopus
    ports:
      - "8080:8080"
    environment:
      - QWOPUS_PORT=8080
      - QWOPUS_HOST=0.0.0.0
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./models:/models
```

---

## Performance Tuning

### Hardware Recommendations

| Component | Minimum | Recommended | Ideal |
|-----------|---------|-------------|-------|
| CPU | 4 cores | 8 cores | 16+ cores |
| RAM | 8GB | 16GB | 32GB+ |
| GPU | Integrated | RTX 3060 (12GB) | RTX 4090 (24GB) |
| Storage | 10GB SSD | 50GB NVMe | 100GB+ NVMe |

### Optimal Settings for Different Hardware

**CPU Only (8 cores, 16GB RAM):**
```yaml
n_threads: 8
n_gpu_layers: 0
context_window: 32000
temp: 0.7
top_p: 0.9
```

**RTX 3060 (12GB VRAM):**
```yaml
n_threads: 8
n_gpu_layers: 40
flash_attn: true
context_window: 64000
temp: 0.7
top_p: 0.9
```

**RTX 4090 (24GB VRAM):**
```yaml
n_threads: 16
n_gpu_layers: -1
flash_attn: true
context_window: 128000
temp: 0.7
top_p: 0.9
top_k: 40
```

### Inference Optimization Tips

1. **Enable Flash Attention:**
   - Reduces memory usage by ~40%
   - Speeds up generation by 20-30%
   - Requires CUDA 11.0+

2. **GPU Offloading:**
   - Move as many layers as VRAM allows
   - `-1` for full offload (most VRAM)
   - Balance between speed and VRAM

3. **Context Window:**
   - Smaller windows = faster inference
   - Set to actual needs, not maximum
   - 32K for most use cases is sufficient

4. **Parallel Processing:**
   - Higher parallel = faster batch processing
   - 4-8 is typically optimal
   - Don't exceed available VRAM

5. **Thread Count:**
   - Match physical cores
   - Don't exceed 80% of total cores
   - Leave headroom for system tasks

---

## Example Configurations

### Minimal Configuration

```yaml
model: Qwen3.5-9B-Uncensored-Q8_0.gguf
context_window: 32000
temp: 0.7
log_level: INFO
```

### Production Configuration

```yaml
provider: custom
model: Qwen3.5-9B-Uncensored-Q8_0.gguf
context_window: 64000
parallel: 8
n_predict: -1
temp: 0.7
top_p: 0.9
top_k: 40
flash_attn: true
n_threads: 16
n_gpu_layers: -1
log_level: INFO
log_file: /var/log/qwopus/agent.log
```

### Development Configuration

```yaml
provider: custom
model: Qwen3.5-9B-Uncensored-Q4_K_M.gguf
context_window: 32000
parallel: 4
n_predict: 2048
temp: 0.8
top_p: 0.95
top_k: 50
flash_attn: true
n_threads: 8
n_gpu_layers: 20
log_level: DEBUG
log_file: ~/.qwopus/logs/agent.log
```

### Multi-GPU Configuration

```yaml
model: Qwen3.5-9B-Uncensored-Q8_0.gguf
context_window: 128000
parallel: 4
n_predict: -1
temp: 0.7
top_p: 0.9
top_k: 40
flash_attn: true
n_threads: 16
n_gpu_layers: -1
```

---

## Troubleshooting

### Model Not Loading

**Symptoms:** Server starts but `/health` shows `model_loaded: false`

**Solutions:**
1. Check model path exists:
   ```bash
   ls -la Qwen3.5-9B-Uncensored-Q8_0.gguf
   ```

2. Verify model file is valid:
   ```bash
   file Qwen3.5-9B-Uncensored-Q8_0.gguf
   ```

3. Check permissions:
   ```bash
   chmod +r Qwen3.5-9B-Uncensored-Q8_0.gguf
   ```

4. Increase context window if OOM:
   ```yaml
   context_window: 32000
   ```

### Out of Memory (OOM)

**Symptoms:** Server crashes with CUDA out of memory

**Solutions:**
1. Reduce `n_gpu_layers`:
   ```yaml
   n_gpu_layers: -1  # Change to: 40, 50, 60
   ```

2. Reduce `context_window`:
   ```yaml
   context_window: 32000  # or 64000
   ```

3. Use quantized model:
   - `Q8_0` → `Q5_K_M` → `Q4_K_M`

### Slow Inference

**Symptoms:** Low tokens/second generation

**Solutions:**
1. Enable flash attention:
   ```yaml
   flash_attn: true
   ```

2. Increase GPU layers:
   ```yaml
   n_gpu_layers: -1
   ```

3. Reduce context window:
   ```yaml
   context_window: 32000
   ```

### High CPU Usage

**Symptoms:** System slows, CPU at 100%

**Solutions:**
1. Enable GPU offloading:
   ```yaml
   n_gpu_layers: 50
   ```

2. Reduce thread count:
   ```yaml
   n_threads: 8  # Instead of 16
   ```

3. Lower parallel count:
   ```yaml
   parallel: 2  # Instead of 4
   ```

### CORS Errors

**Symptoms:** Browser console shows CORS errors

**Solutions:**
1. Check CORS middleware enabled:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # Configure for your needs
       ...
   )
   ```

2. Verify origin in request headers

---

## Related Documentation

- [API Reference](/root/repos/kimikazee-qwopus/docs/api.md)
- [Deployment Guide](/root/repos/kimikazee-qwopus/docs/deployment.md)
- [Usage Examples](/root/repos/kimikazee-qwopus/examples/)

---

## Support

- **GitHub Issues:** [kimikazee/kimikazee-qwopus/issues](https://github.com/kimikazee/kimikazee-qwopus/issues)
- **Documentation:** [Kimikazee Qwopus Docs](https://kimikazee.github.io/kimikazee-qwopus)

---

*Last updated: 2026-04-30 | Version: 1.0.0*
