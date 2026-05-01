#!/usr/bin/env python3
"""
Skills registry for Qwuopus bot.
Each skill is a callable with a name, description, and parameter schema.
Skills run on the Alpha server (Hetzner) with access to terminal, web, files.
"""

import json
import subprocess
import time
import traceback
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# SKILL DEFINITIONS (OpenAI function-calling format)
# ─────────────────────────────────────────────────────────────────────────────

SKILLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information. Returns top 5 results with titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch and extract text content from a URL. Useful for reading articles, docs, or web pages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return (default 4000)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command on the server. Returns stdout, stderr, and exit code. Use for file operations, git, system info, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 30)",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file on the server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative file path",
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum lines to return (default 100)",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file on the server. Creates parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to write to",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current date, time, and timezone.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SKILL IMPLEMENTATIONS
# ─────────────────────────────────────────────────────────────────────────────

async def execute_skill(name: str, arguments: Dict[str, Any]) -> str:
    """Execute a skill by name and return the result as a string."""
    handlers = {
        "web_search": _web_search,
        "web_fetch": _web_fetch,
        "run_command": _run_command,
        "read_file": _read_file,
        "write_file": _write_file,
        "get_time": _get_time,
    }
    handler = handlers.get(name)
    if not handler:
        return json.dumps({"error": f"Unknown skill: {name}"})
    try:
        result = await handler(arguments)
        return result
    except Exception as e:
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()[:500]})


async def _web_search(args: Dict) -> str:
    """Search using DuckDuckGo instant answer API (no key needed)."""
    import httpx
    query = args["query"]
    url = f"https://html.duckduckgo.com/html/?q={query}"
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = await client.get(url, headers=headers)
    # Simple parse of results
    import re
    results = []
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', resp.text, re.S)
    titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', resp.text, re.S)
    urls = re.findall(r'class="result__url"[^>]*href="([^"]*)"', resp.text)
    for i in range(min(5, len(titles))):
        title = re.sub(r"<[^>]+>", "", titles[i]).strip()
        snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""
        link = urls[i] if i < len(urls) else ""
        results.append({"title": title, "url": link, "snippet": snippet})
    return json.dumps({"results": results}, ensure_ascii=False)


async def _web_fetch(args: Dict) -> str:
    """Fetch URL and extract text."""
    import httpx
    url = args["url"]
    max_chars = args.get("max_chars", 4000)
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
    # Strip HTML tags for plain text
    import re
    text = re.sub(r"<script[^>]*>.*?</script>", "", resp.text, flags=re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return json.dumps({"url": url, "content": text[:max_chars]})


async def _run_command(args: Dict) -> str:
    """Run a shell command."""
    command = args["command"]
    timeout = args.get("timeout", 30)
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return json.dumps({
            "stdout": result.stdout[:3000],
            "stderr": result.stderr[:1000],
            "exit_code": result.returncode,
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Command timed out after {timeout}s"})


async def _read_file(args: Dict) -> str:
    """Read a file."""
    path = args["path"]
    max_lines = args.get("max_lines", 100)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        content = "".join(lines[:max_lines])
        return json.dumps({"path": path, "lines": len(lines), "content": content})
    except FileNotFoundError:
        return json.dumps({"error": f"File not found: {path}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def _write_file(args: Dict) -> str:
    """Write to a file."""
    import os
    path = args["path"]
    content = args["content"]
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return json.dumps({"written": path, "bytes": len(content.encode())})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def _get_time(args: Dict) -> str:
    """Get current time."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return json.dumps({
        "utc": now.isoformat(),
        "unix": int(now.timestamp()),
    })


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT FORMATTING
# ─────────────────────────────────────────────────────────────────────────────

def format_skills_for_prompt() -> str:
    """Format skill definitions as text for injection into the system prompt."""
    lines = ["You have access to the following tools. To use a tool, output a JSON block:\n"
             "```tool\n{\"name\": \"skill_name\", \"arguments\": {\"key\": \"value\"}}\n```\n"
             "You may call up to 3 tools per response. Wait for tool results before continuing.\n"
             "\nAvailable tools:"]
    for skill in SKILLS:
        fn = skill["function"]
        lines.append(f"\n### {fn['name']}")
        lines.append(f"Description: {fn['description']}")
        props = fn["parameters"].get("properties", {})
        required = fn["parameters"].get("required", [])
        if props:
            lines.append("Parameters:")
            for pname, pinfo in props.items():
                req = " (required)" if pname in required else " (optional)"
                lines.append(f"  - {pname}: {pinfo.get('type', 'string')} — {pinfo.get('description', '')}{req}")
    return "\n".join(lines)
