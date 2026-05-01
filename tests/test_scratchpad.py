"""Tests for the Scratch Pad LLM module."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from scratchpad.helper import HelperLLM, HelperConfig, HelperResult
from scratchpad.router import ScratchPadRouter, TaskComplexity


# ── HelperConfig ─────────────────────────────────────────────────────

class TestHelperConfig:
    def test_defaults(self):
        cfg = HelperConfig()
        assert cfg.base_url == "http://localhost:8081"
        assert cfg.max_tokens_classify == 64
        assert cfg.temperature == 0.1
        assert cfg.request_timeout == 5.0

    def test_from_config(self):
        config = {
            "scratchpad": {
                "helper_url": "http://192.168.1.50:8081",
                "helper_model": "gemma-3-2b",
                "max_tokens_classify": 32,
                "helper_temperature": 0.0,
                "helper_timeout": 3.0,
            }
        }
        cfg = HelperConfig.from_config(config)
        assert cfg.base_url == "http://192.168.1.50:8081"
        assert cfg.model_name == "gemma-3-2b"
        assert cfg.max_tokens_classify == 32
        assert cfg.temperature == 0.0
        assert cfg.request_timeout == 3.0

    def test_from_config_missing_scratchpad(self):
        cfg = HelperConfig.from_config({"other": "stuff"})
        assert cfg.base_url == "http://localhost:8081"  # default


# ── HelperResult ─────────────────────────────────────────────────────

class TestHelperResult:
    def test_tok_per_sec(self):
        r = HelperResult(text="hello", tokens_out=100, elapsed_ms=1000)
        assert r.tok_per_sec == 100.0

    def test_tok_per_sec_zero_elapsed(self):
        r = HelperResult(text="hello", tokens_out=100, elapsed_ms=0)
        assert r.tok_per_sec == 0.0

    def test_ok_no_error(self):
        r = HelperResult(text="good")
        assert r.ok is True

    def test_ok_with_error(self):
        r = HelperResult(text="", error="timeout")
        assert r.ok is False


# ── ScratchPadRouter ─────────────────────────────────────────────────

class TestScratchPadRouter:
    @pytest.fixture
    def router(self):
        helper = MagicMock(spec=HelperLLM)
        return ScratchPadRouter(helper=helper)

    def test_classify_greeting(self, router):
        messages = [{"role": "user", "content": "hello"}]
        decision = router.classify(messages)
        assert decision.complexity == TaskComplexity.TRIVIAL
        assert decision.route == "helper_only"

    def test_classify_simple_math(self, router):
        messages = [{"role": "user", "content": "42 * 7"}]
        decision = router.classify(messages)
        assert decision.complexity == TaskComplexity.TRIVIAL

    def test_classify_ping(self, router):
        messages = [{"role": "user", "content": "ping"}]
        decision = router.classify(messages)
        assert decision.complexity == TaskComplexity.TRIVIAL

    def test_classify_complex_code(self, router):
        messages = [{"role": "user", "content": "write a Python function that implements a binary search tree with insert, delete, and find operations"}]
        decision = router.classify(messages)
        assert decision.complexity == TaskComplexity.COMPLEX
        assert decision.verify_output is True

    def test_classify_tool_chain(self, router):
        messages = [{"role": "user", "content": "read the config file and update the port setting to 8080"}]
        decision = router.classify(messages)
        assert decision.complexity == TaskComplexity.TOOL_CHAIN

    def test_classify_simple_default(self, router):
        messages = [{"role": "user", "content": "what is the weather like today in san diego"}]
        decision = router.classify(messages)
        assert decision.complexity == TaskComplexity.SIMPLE

    def test_classify_empty_messages(self, router):
        decision = router.classify([])
        assert decision.complexity == TaskComplexity.STANDARD

    def test_classify_long_message(self, router):
        messages = [{"role": "user", "content": "x" * 250}]
        decision = router.classify(messages)
        assert decision.complexity == TaskComplexity.COMPLEX  # length triggers it

    def test_routing_stats_accumulate(self, router):
        router.classify([{"role": "user", "content": "hello"}])
        router.classify([{"role": "user", "content": "write a parser"}])
        router.classify([{"role": "user", "content": "how's it going"}])
        stats = router.stats["routing"]
        assert stats["trivial"] == 2
        assert stats["complex"] == 1


# ── HelperLLM ────────────────────────────────────────────────────────

class TestHelperLLM:
    def test_init_default_config(self):
        h = HelperLLM()
        assert h.config.base_url == "http://localhost:8081"

    def test_init_custom_config(self):
        cfg = HelperConfig(base_url="http://localhost:9999")
        h = HelperLLM(config=cfg)
        assert h.config.base_url == "http://localhost:9999"

    def test_stats(self):
        h = HelperLLM()
        assert h.stats == {"calls": 0, "failures": 0, "total_tokens": 0}
