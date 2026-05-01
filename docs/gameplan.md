# Kimikazee Qwopus — Gameplan

## Fixes Applied (2026-04-30)

### 1. WSL PID Exhaustion Fix
**Problem:** `bash: fork: retry: Resource temporarily unavailable` — WSL instance hitting process limits.

**Root cause:** `beta-inbox.service` stuck in auto-restart loop + nvm initializing on every non-interactive shell invocation (every SSH command).

**Fixes:**
- `systemctl --user stop beta-inbox.service` + `systemctl --user disable beta-inbox.service`
- Wrapped nvm init in `.bashrc` with interactive shell check (`[[ $- == *i* ]]`)
- Verified with fork stress test — 5 rapid forks succeed cleanly

### 2. Forbidden Model Swap
**Problem:** llama-server was running `Qwen3.5-9B-Uncensored-HauhauCS-Aggressive-Q4_K_M.gguf` — **forbidden per user policy** (no uncensored models).

**Fix:**
- Updated both systemd service files to use `Qwen3.5-9B-DeepSeek-V4-Flash-Q4_K_M.gguf`
- Fixed model path: `/home/boh/llama.cpp/models/` → `/home/boh/models/` (correct location)
- Files updated:
  - `~/.config/systemd/user/llama-server.service`
  - `~/.config/systemd/user/default.target.wants/llama-server.service`
- Server healthy: `status=ok`, 1 slot idle, 21 tasks, ~905MB memory

### 3. SCP / File Transfer Issues
**Status:** Not yet encountered in this session. Using `cat | ssh ... 'bash -c ...'` pattern for reliable script transfer to WSL.

---

## Pending: Unsloth Merge (Phase 3 Option A)

### Goal
Merge `Qwopus3.5-9B-v3` (agent/tools specialist) + `Qwen3.5-9B-DeepSeek-V4-Flash` (reasoning) into a single GGUF Q4_K_M.

### Safetensor Locations
- **Qwopus-v3**: `/home/boh/models/Qwopus3.5-9B-v3` (18GB, downloaded)
- **DeepSeek-V4-Flash**: `/home/boh/models/DeepSeek-V4-Flash` (17GB, downloaded)

### Merge Approach
1. Install/verify Unsloth (`pip install unsloth` — already installed v2026.4.8)
2. Load both models as LoRA adapters or direct weight merge
3. Export merged model to GGUF Q4_K_M quantization
4. Verify output at `/home/boh/models/Kimikazee-Qwopus-DeepSeek-Q4_K_M.gguf`

### Verification
- Load merged model in llama-server
- Benchmark: tool call accuracy, reasoning quality, context retention
- Compare against baseline DeepSeek-V4-Flash alone

### Fallback: Option C (Layer Blend)
If merged model underperforms on context (GLM distill weakness):
- Use `mergekit` for DARE-TIES layer blending
- Weight Qwopus layers for agent tasks, DeepSeek layers for reasoning
- Blend GLM context layers for long-context preservation
