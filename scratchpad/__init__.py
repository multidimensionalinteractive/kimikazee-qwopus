"""
Kimikazee Qwopus — Scratch Pad LLM Module
==========================================

Dual-model architecture for maximizing throughput on consumer GPUs.

The Scratch Pad runs a small, fast helper model alongside the main
Qwen 3.5 9B to:
  - Classify & route simple tasks to the helper (100+ tok/s on tiny models)
  - Pre-process user input → reduce main model prompt tokens
  - Post-verify main model output → catch hallucinations cheaply
  - Compress conversation context → fit more turns per context window

Usage:
    from scratchpad import ScratchPadRouter, HelperLLM

    helper = HelperLLM(base_url="http://localhost:8081")
    router = ScratchPadRouter(helper=helper)

    result = await router.handle(messages, tools)
"""

from scratchpad.router import ScratchPadRouter, TaskComplexity
from scratchpad.helper import HelperLLM, HelperConfig

__all__ = [
    "ScratchPadRouter",
    "TaskComplexity",
    "HelperLLM",
    "HelperConfig",
]

__version__ = "0.1.0"
