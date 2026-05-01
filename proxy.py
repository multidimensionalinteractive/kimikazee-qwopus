#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kimikazee Qwopus — Dual-Model Proxy

Lightweight proxy that routes requests between:
  • SmolLM2 1.7B (port 8081) — scratch pad for routing, classification, short answers
  • Qwopus 9B   (port 8080) — main model for reasoning, generation, complex tasks

Runs standalone alongside the two llama-server instances.
OpenAI-compatible API: POST /v1/chat/completions, GET /v1/models, GET /health

Usage:
    python proxy.py                          # defaults: port 3000, config.yaml
    python proxy.py --port 8888              # custom port
    python proxy.py --config custom.yaml     # custom config
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

def load_config(path: str = "config.yaml") -> Dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(p, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def get_scratchpad_cfg(cfg: Dict) -> Dict:
    sp = cfg.get("scratchpad", {})
    if not sp.get("enabled", False):
        return {
            "helper_endpoint": "http://localhost:8081",
            "main_endpoint": "http://localhost:8080",
            "helper_model": "helper",
            "main_model": "main",
            "complexity_threshold": 3,
            "helper_always": [],
            "main_always": [],
        }
    return sp


# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("qwopus.proxy")

# ─────────────────────────────────────────────────────────────────────────────
# ROUTING HEURISTICS
# ─────────────────────────────────────────────────────────────────────────────

HELPER_PATTERNS = [
    (r"\b(classify|categorize|label|tag)\b", "classify"),
    (r"\b(yes\s*or\s*no|true\s*or\s*false|is\s+it)\b", "yes_no"),
    (r"\b(sentiment|tone|mood)\b", "sentiment"),
    (r"\b(extract|pull\s+out|find\s+in)\b", "extract"),
    (r"\b(format|reformat|restructure)\b", "format"),
    (r"\b(summarize\s+(?:in\s+)?(?:one|1|a)\s+(?:word|sentence|line))\b", "extract"),
]

MAIN_PATTERNS = [
    (r"\b(write|code|implement|debug|fix|refactor|function|class|api)\b", "code"),
    (r"\b(reason|explain|why|analyze|compare|evaluate|step\s+by\s+step)\b", "reasoning"),
    (r"\b(deep\s+analysis|research|investigate|breakdown)\b", "analysis"),
    (r"\b(write\s+(?:a\s+)?(?:story|poem|essay|article|creative))\b", "creative"),
    (r"\b(plan|strategy|architecture|design|multi.step)\b", "multi_step"),
]


def classify_request(user_msg: str) -> str:
    """
    Classify the latest user message and return:
      'helper' — route to small model
      'main'   — route to big model
    """
    msg_lower = user_msg.lower().strip()

    # Short messages (< 30 chars) → helper
    if len(msg_lower) < 30:
        return "helper"

    # Check helper patterns first (fast tasks)
    for pattern, _ in HELPER_PATTERNS:
        if re.search(pattern, msg_lower):
            return "helper"

    # Check main patterns (complex tasks)
    for pattern, _ in MAIN_PATTERNS:
        if re.search(pattern, msg_lower):
            return "main"

    # Token count heuristic — long prompts → main
    word_count = len(msg_lower.split())
    if word_count > 50:
        return "main"

    # Default: helper for simple, main for anything else
    if word_count <= 10:
        return "helper"

    return "main"


def route_for_request(
    messages: List[Dict],
    model_override: Optional[str] = None,
    sp_cfg: Optional[Dict] = None,
) -> str:
    """
    Decide which endpoint to use based on message content and config.
    Returns the endpoint URL.
    """
    if sp_cfg is None:
        sp_cfg = {}

    main_ep = sp_cfg.get("main_endpoint", "http://localhost:8080")
    helper_ep = sp_cfg.get("helper_endpoint", "http://localhost:8081")

    # Explicit model override
    if model_override:
        mu = model_override.lower()
        if "helper" in mu or "smol" in mu:
            return helper_ep
        if "main" in mu or "qwopus" in mu or "qwen" in mu:
            return main_ep

    # Find last user message
    user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_msg = m.get("content", "")
            if isinstance(user_msg, list):
                user_msg = " ".join(
                    c.get("text", "") for c in user_msg if isinstance(c, dict)
                )
            break

    if not user_msg:
        return main_ep

    target = classify_request(user_msg)
    return helper_ep if target == "helper" else main_ep


# ─────────────────────────────────────────────────────────────────────────────
# PROXY LOGIC
# ─────────────────────────────────────────────────────────────────────────────

async def proxy_request(
    endpoint: str,
    model_name: str,
    messages: List[Dict],
    params: Dict,
    stream: bool = False,
) -> httpx.Response:
    """Forward request to the chosen llama-server endpoint."""
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": params.get("temperature", 0.5),
        "top_p": params.get("top_p", 0.92),
        "top_k": params.get("top_k", 40),
        "max_tokens": params.get("max_tokens", -1),
        "stream": stream,
    }
    if params.get("stop"):
        payload["stop"] = params["stop"]

    url = f"{endpoint}/v1/chat/completions"
    timeout = httpx.Timeout(connect=5, read=300, write=10, pool=10)

    async with httpx.AsyncClient(timeout=timeout) as client:
        if stream:
            # Return the raw response for streaming
            req = client.build_request("POST", url, json=payload)
            resp = await client.send(req, stream=True)
            return resp
        else:
            resp = await client.post(url, json=payload)
            return resp


# ─────────────────────────────────────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────────────────────────────────────

def create_app(config_path: str = "config.yaml") -> FastAPI:
    cfg = load_config(config_path)
    sp_cfg = get_scratchpad_cfg(cfg)

    app = FastAPI(
        title="Kimikazee Qwopus — Dual-Model Proxy",
        version="2.0.0",
        description=(
            "OpenAI-compatible proxy that routes between "
            "SmolLM2 1.7B (scratch pad) and Qwopus 9B (main)."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── health ───────────────────────────────────────────────────────────

    @app.get("/health")
    async def health():
        results = {}
        async with httpx.AsyncClient(timeout=httpx.Timeout(5)) as client:
            for name, ep in [
                ("helper", sp_cfg["helper_endpoint"]),
                ("main", sp_cfg["main_endpoint"]),
            ]:
                try:
                    r = await client.get(f"{ep}/health")
                    results[name] = {"status": "up", "code": r.status_code}
                except Exception as e:
                    results[name] = {"status": "down", "error": str(e)}
        return {"proxy": "healthy", "backends": results}

    # ── models ───────────────────────────────────────────────────────────

    @app.get("/v1/models")
    async def list_models():
        return {
            "object": "list",
            "data": [
                {
                    "id": sp_cfg["main_model"],
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "qwopus",
                },
                {
                    "id": sp_cfg["helper_model"],
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "qwopus",
                },
                {
                    "id": "auto",
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "qwopus",
                    "description": "Auto-routes to best model based on complexity",
                },
            ],
        }

    # ── chat completions ─────────────────────────────────────────────────

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        body = await request.json()
        messages = body.get("messages", [])
        model = body.get("model", "auto")
        stream = body.get("stream", False)
        temperature = body.get("temperature", cfg.get("temp", 0.5))
        top_p = body.get("top_p", cfg.get("top_p", 0.92))
        top_k = body.get("top_k", cfg.get("top_k", 40))
        max_tokens = body.get("max_tokens", -1)
        stop = body.get("stop")

        params = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_tokens": max_tokens,
            "stop": stop,
        }

        # Route
        endpoint = route_for_request(messages, model, sp_cfg)
        is_helper = endpoint == sp_cfg["helper_endpoint"]
        model_name = sp_cfg["helper_model"] if is_helper else sp_cfg["main_model"]

        log.info(
            "→ %s [%s] tokens≈%d",
            "HELPER" if is_helper else "MAIN  ",
            model,
            sum(len(m.get("content", "").split()) for m in messages),
        )

        start = time.time()

        try:
            resp = await proxy_request(
                endpoint, model_name, messages, params, stream=stream
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"Backend {endpoint} unreachable",
            )

        elapsed = time.time() - start

        if stream:
            # Pass through SSE stream
            async def stream_generator():
                async for chunk in resp.aiter_text():
                    yield chunk

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Model-Routed": "helper" if is_helper else "main",
                    "X-Proxy-Latency": f"{elapsed:.3f}s",
                },
            )

        # Non-streaming: enrich response with routing metadata
        data = resp.json()
        data["_route"] = {
            "backend": "helper" if is_helper else "main",
            "endpoint": endpoint,
            "model": model_name,
            "latency_s": round(elapsed, 3),
        }
        return data

    return app


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Kimikazee Qwopus Dual-Model Proxy")
    parser.add_argument("--port", type=int, default=3000, help="Listen port")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument("--config", default="config.yaml", help="Config file")
    args = parser.parse_args()

    import uvicorn

    app = create_app(args.config)
    log.info("Starting Kimikazee Qwopus proxy on %s:%d", args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
