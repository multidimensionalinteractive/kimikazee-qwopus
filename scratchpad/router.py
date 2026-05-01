"""
Scratch Pad Router — Task classification & dual-model orchestration.

This is the intelligence layer that decides:
  1. Can the helper handle this alone? (simple tasks → fast path)
  2. Should we pre-process with the helper first? (reduce main model tokens)
  3. Should we verify the main model's output? (catch hallucinations)
  4. Can we compress old context with the helper? (save context window)

The goal: maximize effective tok/s by offloading work from the slow
main model to the fast helper wherever possible.
"""

import re
import logging
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from scratchpad.helper import HelperLLM, HelperResult

logger = logging.getLogger("qwopus.scratchpad.router")


class TaskComplexity(Enum):
    """Task routing decision."""
    TRIVIAL = "trivial"        # Helper handles alone
    SIMPLE = "simple"          # Helper pre-processes, main generates
    STANDARD = "standard"      # Main model only
    COMPLEX = "complex"        # Main model + helper verification
    TOOL_CHAIN = "tool_chain"  # Main model + scratchpad protocol


class RoutingDecision:
    """What the router decided to do."""

    def __init__(
        self,
        complexity: TaskComplexity,
        route: str,
        preprocessed_messages: Optional[List[Dict]] = None,
        helper_system_prefix: str = "",
        max_tokens_helper: int = 256,
        verify_output: bool = False,
        compress_context: bool = False,
        reasoning: str = "",
    ):
        self.complexity = complexity
        self.route = route  # "helper_only" | "main" | "helper_then_main"
        self.preprocessed_messages = preprocessed_messages
        self.helper_system_prefix = helper_system_prefix
        self.max_tokens_helper = max_tokens_helper
        self.verify_output = verify_output
        self.compress_context = compress_context
        self.reasoning = reasoning

    def __repr__(self):
        return f"RoutingDecision({self.complexity.value} → {self.route}: {self.reasoning})"


# ── Classification Patterns ──────────────────────────────────────────

TRIVIAL_PATTERNS = [
    # Greetings
    r"^(hi|hello|hey|yo|sup|howdy|greetings)[\s!.?]*$",
    # Simple math
    r"^\d+\s*[\+\-\*\/\%]\s*\d+[\s=.?]*$",
    # What time / date
    r"^(what\s+time|what'?s?\s+the\s+time|current\s+time|date|what\s+day)",
    # Yes/no questions
    r"^(is|are|do|does|can|will|should|would)\s+(it|this|that|there)",
    # Ping / test
    r"^(ping|test|alive|status|version)$",
    # Simple translations of short phrases
    r"^(translate|say|how do you say)\s+.+\s+in\s+\w+$",
]

COMPLEX_PATTERNS = [
    # Code generation
    r"(write|create|build|implement|develop|code|program|script|function)\s+.{20,}",
    # Architecture / design
    r"(architect|design|plan|structure|organize|refactor)\s+.{10,}",
    # Analysis
    r"(analyze|compare|evaluate|assess|review|audit)\s+.{10,}",
    # Debugging
    r"(debug|fix|error|bug|issue|problem|crash|traceback)\s+.{5,}",
    # Multi-step instructions
    r"(step by step|walk through|explain in detail|comprehensive)",
]

TOOL_CHAIN_PATTERNS = [
    r"(search for|read the|write to|check if|verify that|list all|find)",
    r"(use the tool|call the function|run the command|execute)",
    r"(update|delete|create|modify|patch)\s+(the\s+)?(file|config|setting)",
]


class ScratchPadRouter:
    """
    Routes requests through the dual-model pipeline.

    Classifies incoming messages and decides whether the helper LLM
    can handle them alone, should pre-process, or should verify output.
    """

    def __init__(self, helper: HelperLLM, config: Optional[Dict] = None):
        self.helper = helper
        self.config = config or {}
        self._routing_stats = {c.value: 0 for c in TaskComplexity}

    def classify(self, messages: List[Dict]) -> RoutingDecision:
        """
        Classify the task and decide routing.

        This is the core intelligence — it looks at the conversation
        to decide the optimal path through the dual-model pipeline.
        """
        if not messages:
            return RoutingDecision(
                TaskComplexity.STANDARD, "main",
                reasoning="empty input"
            )

        last_msg = messages[-1].get("content", "").strip().lower()
        has_tools = any("tool" in str(m).lower() for m in messages)
        conversation_length = len(messages)

        # ── Check TRIVIAL (helper handles alone) ──
        for pattern in TRIVIAL_PATTERNS:
            if re.search(pattern, last_msg, re.IGNORECASE):
                decision = RoutingDecision(
                    TaskComplexity.TRIVIAL,
                    route="helper_only",
                    helper_system_prefix=(
                        "You are a fast assistant. Answer concisely in 1-3 sentences. "
                        "No preamble, no filler. Direct answer only."
                    ),
                    max_tokens_helper=128,
                    reasoning=f"trivial pattern: {pattern[:40]}",
                )
                self._routing_stats["trivial"] += 1
                return decision

        # ── Check COMPLEX (main + verification) ──
        complex_score = sum(
            1 for p in COMPLEX_PATTERNS
            if re.search(p, last_msg, re.IGNORECASE)
        )

        # ── Check TOOL CHAIN ──
        tool_score = sum(
            1 for p in TOOL_CHAIN_PATTERNS
            if re.search(p, last_msg, re.IGNORECASE)
        )

        if tool_score >= 1 or has_tools:
            decision = RoutingDecision(
                TaskComplexity.TOOL_CHAIN,
                route="main",
                verify_output=tool_score >= 2,
                compress_context=conversation_length > 15,
                reasoning=f"tool signals: {tool_score}, has_tools: {has_tools}",
            )
            self._routing_stats["tool_chain"] += 1
            return decision

        if complex_score >= 1 or len(last_msg) > 200:
            decision = RoutingDecision(
                TaskComplexity.COMPLEX,
                route="helper_then_main",
                helper_system_prefix=(
                    "Analyze this request. Extract: 1) Key intent in 1 sentence. "
                    "2) Required capabilities. 3) Suggested approach. Be brief."
                ),
                max_tokens_helper=192,
                verify_output=True,
                compress_context=conversation_length > 12,
                reasoning=f"complex signals: {complex_score}, msg_len: {len(last_msg)}",
            )
            self._routing_stats["complex"] += 1
            return decision

        # ── Default: SIMPLE ──
        decision = RoutingDecision(
            TaskComplexity.SIMPLE,
            route="helper_then_main",
            helper_system_prefix=(
                "You are a pre-processor. Extract the user's core request "
                "in 1-2 sentences. Remove filler. Preserve all specifics."
            ),
            max_tokens_helper=128,
            reasoning="default simple path",
        )
        self._routing_stats["simple"] += 1
        return decision

    async def preprocess(
        self,
        messages: List[Dict],
        decision: RoutingDecision,
    ) -> List[Dict]:
        """
        Pre-process messages through the helper if routing says so.

        Returns the (possibly modified) message list for the main model.
        """
        if decision.route == "helper_only":
            # Helper handles it entirely
            return messages  # Caller should check route and short-circuit

        if decision.route == "helper_then_main":
            # Run helper pre-processing
            result = await self.helper.complete(
                messages=messages,
                max_tokens=decision.max_tokens_helper,
                system_prefix=decision.helper_system_prefix,
            )

            if result.ok and result.text.strip():
                logger.info(
                    f"Helper pre-processed in {result.elapsed_ms:.0f}ms "
                    f"({result.tok_per_sec:.0f} tok/s)"
                )
                # Inject helper's analysis as a system message prepended
                # to give the main model compressed context
                processed = [
                    m for m in messages if m.get("role") != "system"
                ]
                processed.insert(0, {
                    "role": "system",
                    "content": (
                        f"## Pre-analysis (from helper model)\n"
                        f"{result.text}\n\n"
                        f"Use this as context. Respond to the user's original request."
                    ),
                })
                return processed

        return messages

    async def handle(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        main_completion_fn=None,
    ) -> Dict:
        """
        Full routing pipeline: classify → preprocess → main → verify.

        Args:
            messages: Conversation messages
            tools: Available tool definitions
            main_completion_fn: Async callable(messages, tools) -> response dict
                               This is the main model's completion function.

        Returns:
            Response dict with routing metadata
        """
        start = time.monotonic()
        decision = self.classify(messages)

        result = {
            "routing": decision.complexity.value,
            "route": decision.route,
            "reasoning": decision.reasoning,
        }

        # ── Fast path: helper handles it alone ──
        if decision.route == "helper_only":
            helper_result = await self.helper.complete(
                messages=messages,
                max_tokens=decision.max_tokens_helper,
                system_prefix=decision.helper_system_prefix,
            )
            result["helper_handled"] = True
            result["helper_ms"] = helper_result.elapsed_ms
            result["helper_toks"] = helper_result.tokens_out
            result["helper_tok_per_sec"] = helper_result.tok_per_sec
            result["text"] = helper_result.text
            result["error"] = helper_result.error
            return result

        # ── Pre-process with helper ──
        processed_messages = await self.preprocess(messages, decision)
        result["preprocessed"] = decision.route == "helper_then_main"

        # ── Main model completion ──
        if main_completion_fn is None:
            result["error"] = "no_main_completion_fn"
            return result

        main_response = await main_completion_fn(processed_messages, tools)
        result["main_response"] = main_response

        # ── Post-verification with helper ──
        if decision.verify_output and "text" in main_response:
            verify_messages = [
                {
                    "role": "user",
                    "content": (
                        f"Verify this response for factual errors or hallucinations. "
                        f"If it contains code, check for syntax errors. "
                        f"Reply ONLY with 'PASS' or 'FAIL: <brief reason>'.\n\n"
                        f"Response:\n{main_response['text'][:1000]}"
                    ),
                }
            ]
            verify_result = await self.helper.complete(
                messages=verify_messages,
                max_tokens=64,
                system_prefix="You are a strict output verifier. Be terse.",
            )
            result["verified"] = True
            result["verify_passed"] = (
                verify_result.ok and "pass" in verify_result.text.lower()
            )
            result["verify_ms"] = verify_result.elapsed_ms

        result["total_ms"] = (time.monotonic() - start) * 1000
        return result

    @property
    def stats(self) -> Dict:
        return {
            "routing": self._routing_stats,
            "helper": self.helper.stats,
        }
