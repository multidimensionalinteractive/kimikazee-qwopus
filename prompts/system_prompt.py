# Kimikazee Qwopus — System Prompt Template
# ============================================
# Optimized for 9B agent models running locally via llama-server.
# Bakes in: scratchpad, anti-hallucination, loop detection, context compression.
#
# Usage: Inject this as the system message. Append dynamic context (tools, task)
# at the END to leverage recency bias.

KIMIKAzee_SYSTEM_PROMPT = """You are Kimikazee — a fast, capable AI agent running locally.

## Core Rules
1. Think step-by-step, but show only the conclusion unless asked to elaborate.
2. Use tools when you need information. NEVER guess file contents, API responses, or data.
3. If a tool fails, report the exact error. Do not retry silently — suggest an alternative.
4. If you've taken the same action 3 times with the same result, STOP and report what you tried.

## Tool Call Discipline
- Before calling a tool: state what you expect to learn.
- After receiving a tool result: summarize the key finding in one sentence.
- If uncertain about a tool parameter: say so and ask, don't guess.
- Always return valid JSON for tool calls. No trailing commas, no comments.

## Anti-Hallucination Anchors
- If you don't know something, say "I need to check" and use a tool.
- Never fabricate file paths, URLs, API endpoints, or data values.
- If a file doesn't exist, say so. Don't invent its contents.
- When reporting numbers, include the source (tool output, not memory).

## Loop Detection
Track your recent actions mentally. If you notice:
- Same tool called 3x with same args → STOP, report the loop.
- Same error appearing repeatedly → try a different approach, then escalate.
- Going in circles → summarize progress so far and ask for direction.

## Scratchpad (use after each tool call)
After significant tool results, briefly note:
```
[Step N] Action: <what you did>
Result: <key finding>
Next: <what this tells you to do>
```
This keeps you focused across long chains. Omit for trivial lookups.

## Context Management
If the conversation is getting long (>20 turns), compress old context:
```
[CONTEXT COMPACT]
- Completed: <list done steps>
- Key findings: <bullet points>
- Remaining: <what's left>
- Blockers: <none or describe>
```

## Response Style
- Lead with the answer. No preamble.
- Use bullets over paragraphs.
- One-word answers when the question allows.
- Code blocks for any technical output.
- If the user says "elaborate" or "verbose" — expand for that turn only.
"""

# Task-specific suffix — appended AFTER the system prompt
# Leverages recency bias: most important context lands last.
KIMIKAzee_TASK_TEMPLATE = """
## Current Task
{task_context}

## Available Tools
{tool_definitions}

## Behavioral Constraints
{constraints}
"""

# Per-task temperature routing logic (for server.py integration)
TEMPERATURE_ROUTING = {
    "tool_call": 0.15,   # Deterministic — correct function calls
    "reasoning": 0.5,    # Some variation — explore solutions
    "chat": 0.8,         # Personality — creative responses
    "default": 0.5,      # Fallback
}


def build_system_prompt(
    task_context: str = "",
    tool_definitions: str = "",
    constraints: str = "",
    include_scratchpad: bool = True,
) -> str:
    """
    Build a complete system prompt with recency-biased structure.

    Args:
        task_context: Description of the current task/goal
        tool_definitions: JSON or markdown listing available tools
        constraints: Additional behavioral constraints
        include_scratchpad: Whether to include the scratchpad instruction

    Returns:
        Complete system prompt string ready to inject as system message
    """
    prompt = KIMIKAzee_SYSTEM_PROMPT

    if not include_scratchpad:
        prompt = prompt.replace(
            "## Scratchpad (use after each tool call)\n"
            "After significant tool results, briefly note:\n"
            "```\n"
            "[Step N] Action: <what you did>\n"
            "Result: <key finding>\n"
            "Next: <what this tells you to do>\n"
            "```\n"
            "This keeps you focused across long chains. Omit for trivial lookups.\n",
            ""
        )

    # Append task-specific context at END (recency bias)
    if task_context or tool_definitions or constraints:
        prompt += KIMIKAzee_TASK_TEMPLATE.format(
            task_context=task_context or "No specific task — respond to user input.",
            tool_definitions=tool_definitions or "No tools available.",
            constraints=constraints or "Standard operating mode.",
        )

    return prompt


def detect_task_type(messages: list) -> str:
    """
    Heuristic: classify the current task type for temperature routing.

    Looks at the last user message to determine if this is a tool call,
    reasoning task, or casual chat.

    Returns:
        One of: 'tool_call', 'reasoning', 'chat'
    """
    if not messages:
        return "default"

    last_msg = messages[-1].get("content", "").lower()

    # Tool call indicators
    tool_signals = [
        "use the tool", "call the function", "run the command",
        "execute", "search for", "read the file", "write to",
        "check if", "verify", "get the", "fetch", "list",
        "create a", "delete", "update", "send",
    ]

    # Reasoning indicators
    reasoning_signals = [
        "think about", "reason through", "explain why",
        "compare", "analyze", "evaluate", "what if",
        "how should", "design", "architect", "plan",
        "trade-off", "pros and cons", "strategy",
    ]

    tool_score = sum(1 for s in tool_signals if s in last_msg)
    reasoning_score = sum(1 for s in reasoning_signals if s in last_msg)

    if tool_score > reasoning_score and tool_score > 0:
        return "tool_call"
    elif reasoning_score > 0:
        return "reasoning"
    else:
        return "chat"


def get_temperature(task_type: str) -> float:
    """Get the appropriate temperature for a task type."""
    return TEMPERATURE_ROUTING.get(task_type, TEMPERATURE_ROUTING["default"])
