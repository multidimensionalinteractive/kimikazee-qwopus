#!/usr/bin/env python3
"""
Qwuopus Discord Bot — Dual-Model Testing Interface
Routes messages through the Qwopus proxy (main 9B + helper 1.7B).
Supports tool/skill calling via structured JSON blocks.
Usage: DISCORD_TOKEN=*** QWOPUS_API=http://localhost:8888 python3 bot.py
"""

import asyncio
import os
import re
import sys
import json
import time

import discord
from discord.ext import commands
import aiohttp

from skills import SKILLS, execute_skill, format_skills_for_prompt

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
QWOPUS_API = os.environ.get("QWOPUS_API", "http://localhost:8888")

if not DISCORD_TOKEN:
    print("❌ Set DISCORD_TOKEN env var")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_PROMPT = (
    """You are Qwuopus, an AI assistant powered by the Kimikazee Qwopus dual-model architecture running on a local RTX 4080 Super (16GB VRAM). You use a smart routing system:
- Qwen3.5-9B fine-tune (Q3_K_M, 4.2GB) for reasoning, code, analysis
- SmolLM2-1.7B-Q4_K_M (1GB) for fast classification, extraction, short answers

"""
    + format_skills_for_prompt()
    + """

When asked about yourself, explain you're Qwuopus — a dual-model local AI running on a custom proxy with smart routing. Mention you can help with reasoning, code, analysis, search, file operations, and shell commands.

Be concise and helpful. Use tools when they'd improve your answer."""
)

channel_history: dict[int, list[dict]] = {}
MAX_HISTORY = 10


async def call_qwopus(messages: list[dict]) -> dict:
    url = f"{QWOPUS_API}/v1/chat/completions"
    payload = {
        "model": "auto",
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.7,
        "stream": False,
    }
    start = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                text = await resp.text()
                return {"error": f"HTTP {resp.status}: {text[:200]}"}
            data = await resp.json()
    elapsed = time.time() - start

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    model_used = data.get("model", "unknown")
    usage = data.get("usage", {})
    route = data.get("_route", {})
    backend = route.get("backend", "?")

    return {
        "content": content,
        "model": model_used,
        "backend": backend,
        "elapsed": round(elapsed, 2),
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
    }


def parse_tool_calls(content: str) -> list[dict]:
    """Extract tool calls from ```tool ... ``` blocks in LLM output."""
    tool_calls = []
    for match in re.finditer(r"```tool\s*\n(.*?)\n```", content, re.DOTALL):
        try:
            call = json.loads(match.group(1))
            if "name" in call:
                tool_calls.append(call)
        except json.JSONDecodeError:
            pass
    return tool_calls


def strip_tool_blocks(content: str) -> str:
    """Remove ```tool ... ``` blocks from the response text."""
    return re.sub(r"```tool\s*\n.*?\n```", "", content, flags=re.DOTALL).strip()


async def process_tool_loop(messages: list[dict], max_iterations: int = 3) -> tuple[str, dict]:
    """Send messages to model, execute any tool calls, repeat until no more tools."""
    last_result = None
    for _ in range(max_iterations):
        result = await call_qwopus(messages)
        if "error" in result:
            return result["content"], result
        last_result = result

        content = result["content"]
        tool_calls = parse_tool_calls(content)

        if not tool_calls:
            # No more tool calls — return final response
            return content, result

        # Strip tool blocks from the visible text
        text_part = strip_tool_blocks(content)

        # Add assistant message with tool call text
        messages.append({"role": "assistant", "content": content})

        # Execute tools and add results
        for call in tool_calls[:3]:  # max 3 tools per round
            tool_name = call["name"]
            tool_args = call.get("arguments", {})
            tool_result = await execute_skill(tool_name, tool_args)
            messages.append({
                "role": "user",
                "content": f"Tool `{tool_name}` returned:\n{tool_result}",
            })

    # Ran out of iterations — return last result
    if last_result:
        return strip_tool_blocks(last_result["content"]), last_result
    return "Error: no response", {"error": "max iterations"}


@bot.event
async def on_ready():
    print(f"✅ Qwopus Bot online: {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mention = bot.user.mentioned_in(message) if bot.user else False

    if not (is_dm or is_mention):
        return

    # Strip mention
    content = message.content
    if bot.user:
        content = content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()

    if not content:
        return

    channel_id = message.channel.id
    if channel_id not in channel_history:
        channel_history[channel_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    channel_history[channel_id].append({"role": "user", "content": content})
    if len(channel_history[channel_id]) > MAX_HISTORY * 2:
        channel_history[channel_id] = channel_history[channel_id][-MAX_HISTORY * 2:]

    # Keep system prompt in copy for tool loop
    msgs_for_llm = list(channel_history[channel_id])

    async with message.channel.typing():
        response_text, result = await process_tool_loop(msgs_for_llm)

    if "error" in result and not response_text:
        await message.reply(f"❌ Error: {result['error']}")
        return

    # Save clean response to history (without tool blocks)
    channel_history[channel_id].append({"role": "assistant", "content": response_text})

    stats = (
        f"\n\n`{result.get('model', '?')}` | "
        f"`{result.get('elapsed', 0)}s` | "
        f"`{result.get('prompt_tokens', 0)}↑ {result.get('completion_tokens', 0)}↓`"
    )

    response = response_text
    if len(response) + len(stats) > 2000:
        response = response[:1950 - len(stats)] + "..."

    await message.reply(response + stats)


@bot.command(name="model")
async def model_cmd(ctx):
    await ctx.send(
        f"🧠 **Qwopus Dual-Model**\n"
        f"Proxy: `{QWOPUS_API}`\n"
        f"History: `{len(channel_history.get(ctx.channel.id, []))}` messages\n"
        f"Skills: {', '.join(s['function']['name'] for s in SKILLS)}"
    )


@bot.command(name="reset")
async def reset_cmd(ctx):
    channel_history[ctx.channel.id] = []
    await ctx.send("🔄 History cleared.")


@bot.command(name="ping")
async def ping_cmd(ctx):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{QWOPUS_API}/v1/models", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m.get("id", "?") for m in data.get("data", [])]
                    await ctx.send(f"✅ Proxy online. Models: {', '.join(models)}")
                else:
                    await ctx.send(f"⚠️ Proxy returned {resp.status}")
    except Exception as e:
        await ctx.send(f"❌ Cannot reach proxy: {e}")


@bot.command(name="set")
async def set_cmd(ctx, key: str = "", value: str = ""):
    if key == "model" and value in ("main", "helper", "auto"):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{QWOPUS_API}/set-model", json={"model": value}) as resp:
                if resp.status == 200:
                    await ctx.send(f"🧠 Model set to `{value}`")
                else:
                    await ctx.send(f"⚠️ Failed (HTTP {resp.status})")
    else:
        await ctx.send("Usage: `!set model main|helper|auto`")


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
