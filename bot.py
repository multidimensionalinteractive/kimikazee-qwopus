#!/usr/bin/env python3
"""
Qwopus Discord Bot — Dual-Model Testing Interface
Routes messages through the Qwopus proxy (main 9B + helper 1.7B).
Usage: DISCORD_TOKEN=xxx QWOPUS_API=http://localhost:8888 python3 bot.py
"""

import os
import sys
import asyncio
import discord
from discord.ext import commands
import aiohttp
import json
import time

# Config
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
QWOPUS_API = os.environ.get("QWOPUS_API", "http://localhost:8888")
MODEL = os.environ.get("QWOPUS_MODEL", "auto")  # auto = router decides

if not DISCORD_TOKEN:
    print("❌ Set DISCORD_TOKEN env var")
    sys.exit(1)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Conversation history per channel (last 10 messages)
channel_history: dict[int, list[dict]] = {}
MAX_HISTORY = 10


async def call_qwopus(messages: list[dict]) -> dict:
    """Call the Qwopus proxy API."""
    url = f"{QWOPUS_API}/v1/chat/completions"
    payload = {
        "model": MODEL,
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

    # Extract response
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    model_used = data.get("model", "unknown")
    usage = data.get("usage", {})

    return {
        "content": content,
        "model": model_used,
        "elapsed": round(elapsed, 2),
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
    }


@bot.event
async def on_ready():
    print(f"✅ Qwopus Bot online: {bot.user}")
    print(f"📡 Proxy: {QWOPUS_API}")
    print(f"🧠 Model: {MODEL}")


@bot.event
async def on_message(message):
    # Ignore own messages
    if message.author == bot.user:
        return

    # Process commands
    await bot.process_commands(message)

    # Only respond to mentions or DMs
    if not (bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel)):
        return

    # Strip mention from content
    content = message.content
    for mention in bot.mentions:
        content = content.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "").strip()

    if not content:
        return

    # Build message history
    channel_id = message.channel.id
    if channel_id not in channel_history:
        channel_history[channel_id] = []

    # Add user message
    channel_history[channel_id].append({"role": "user", "content": content})

    # Trim history
    if len(channel_history[channel_id]) > MAX_HISTORY * 2:
        channel_history[channel_id] = channel_history[channel_id][-MAX_HISTORY * 2:]

    # Show typing
    async with message.channel.typing():
        # Call Qwopus
        result = await call_qwopus(channel_history[channel_id])

    if "error" in result:
        await message.reply(f"❌ Error: {result['error']}")
        return

    # Add assistant response to history
    channel_history[channel_id].append({"role": "assistant", "content": result["content"]})

    # Format response with stats
    stats = (
        f"\n\n`{result['model']}` | "
        f"`{result['elapsed']}s` | "
        f"`{result['prompt_tokens']}↑ {result['completion_tokens']}↓`"
    )

    # Discord message limit is 2000 chars
    response = result["content"]
    if len(response) + len(stats) > 2000:
        response = response[:1950 - len(stats)] + "..."
    
    await message.reply(response + stats)


@bot.command(name="model")
async def model_cmd(ctx):
    """Show current model config."""
    await ctx.send(
        f"🧠 **Qwopus Dual-Model**\n"
        f"Proxy: `{QWOPUS_API}`\n"
        f"Model: `{MODEL}`\n"
        f"History: `{len(channel_history.get(ctx.channel.id, []))}` messages"
    )


@bot.command(name="reset")
async def reset_cmd(ctx):
    """Reset conversation history for this channel."""
    channel_history[ctx.channel.id] = []
    await ctx.send("🔄 History cleared.")


@bot.command(name="ping")
async def ping_cmd(ctx):
    """Check proxy connectivity."""
    try:
        url = f"{QWOPUS_API}/v1/models"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
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
    """Override routing. Usage: !set model main|helper|auto"""
    global MODEL
    if key == "model" and value in ("main", "helper", "auto"):
        MODEL = value
        await ctx.send(f"🧠 Model set to `{MODEL}`")
    else:
        await ctx.send("Usage: `!set model main|helper|auto`")


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
