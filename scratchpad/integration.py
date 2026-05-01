"""
Scratch Pad Integration — Drop-in middleware for FastAPI server.

Adds the dual-model pipeline to the existing Kimikazee server
without modifying server.py core logic.

Usage in server.py:
    from scratchpad.integration import setup_scratchpad

    @app.on_event("startup")
    async def startup():
        scratchpad = setup_scratchpad(app, config)

    # Then in your chat completion endpoint:
    # result = await app.state.scratchpad.handle(messages, tools, main_fn)
"""

import logging
from typing import Callable, Dict, List, Optional

from fastapi import FastAPI

from scratchpad.helper import HelperLLM, HelperConfig
from scratchpad.router import ScratchPadRouter, TaskComplexity

logger = logging.getLogger("qwopus.scratchpad.integration")


def setup_scratchpad(
    app: FastAPI,
    config: Dict,
    main_completion_fn: Optional[Callable] = None,
) -> ScratchPadRouter:
    """
    Initialize and attach the scratch pad router to the FastAPI app.

    Args:
        app: FastAPI application instance
        config: Full config.yaml dict
        main_completion_fn: Async callable(messages, tools) -> dict
                           Wraps the main model's completion logic.

    Returns:
        Configured ScratchPadRouter instance
    """
    scratch_config = config.get("scratchpad", {})

    if not scratch_config.get("enabled", True):
        logger.info("Scratch pad disabled in config — skipping setup")
        return None

    helper_config = HelperConfig.from_config(config)
    helper = HelperLLM(helper_config)
    router = ScratchPadRouter(helper=helper, config=config)

    # Store on app state for access in endpoints
    app.state.scratchpad = router
    app.state.helper = helper
    app.state.main_completion_fn = main_completion_fn

    logger.info(
        f"Scratch pad initialized — helper at {helper_config.base_url}, "
        f"model: {helper_config.model_name}"
    )

    return router


def should_route_through_scratchpad(
    router: ScratchPadRouter,
    messages: List[Dict],
) -> bool:
    """
    Quick check: does this request benefit from scratch pad routing?

    Returns False if router is None or task is STANDARD (no benefit).
    """
    if router is None:
        return False

    decision = router.classify(messages)
    return decision.complexity != TaskComplexity.STANDARD


# ── Scratchpad-specific prompts for the helper ──────────────────────

CONTEXT_COMPRESS_PROMPT = """Compress this conversation history into a structured summary.
Keep ALL key facts, decisions, and findings. Remove filler.

Format:
## Completed
- [list of done steps]

## Key Findings
- [bullet points of important facts]

## Remaining
- [what's left to do]

## Blockers
- [any issues encountered]"""

OUTPUT_VERIFY_PROMPT = """You are a strict code/logic verifier. Check this output for:
1. Factual errors or hallucinated data
2. Code syntax errors
3. Contradictions with the stated task

Reply ONLY:
- "PASS" if everything looks correct
- "FAIL: <one-line reason>" if you find an issue

Do not explain. Do not add commentary."""

TASK_EXTRACT_PROMPT = """Extract the core request from this message.
Remove greetings, filler, context-setting.

Return ONLY the actionable task in 1-2 sentences.
If the message is already concise, return it unchanged."""
