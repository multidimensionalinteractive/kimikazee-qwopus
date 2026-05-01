#!/usr/bin/env python3
"""
Qwuopus Discord Bot — Dual-Model Testing Interface
Routes messages through the Qwopus proxy (main 9B + helper 1.7B).
Usage: DISCORD_TOKEN=xxx QWOPUS_API=http://localhost:8888 python3 bot.py
"""

import os
import sys
import discord
from discord.ext import commands
import aiohttp
import time

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
QWOPUS_API = os.environ.get("QWOPUS_API", "http://localhost:8888")

if not DISCORD_TOKEN:
    print("❌ Set DISCORD_TOKEN env var")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_PROMPT = """You are Qwuopus, an AI assistant powered by the Kimikazee Qwopus dual-model architecture running on a local RTX 4080 Super (16GB VRAM). You use a smart routing system:
- Qwen3.5-9B (Qwopus) for complex reasoning, code, analysis, and creative tasks
- SmolLM2-1.7B for quick classification, simple Q&A, formatting, and extraction

You are concise, helpful, and honest. When asked what you can do, describe your capabilities: research, analysis, code generation, creative writing, classification, data extraction, reasoning, and general conversation. You run entirely on local hardware with no cloud API dependency."""

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

    async with message.channel.typing():
        result = await call_qwopus(channel_history[channel_id])

    if "error" in result:
        await message.reply(f"❌ Error: {result['error']}")
        return

    channel_history[channel_id].append({"role": "assistant", "content": result["content"]})

    stats = (
        f"\n\n`{result['model']}` | "
        f"`{result['elapsed']}s` | "
        f"`{result['prompt_tokens']}↑ {result['completion_tokens']}↓`"
    )

    response = result["content"]
    if len(response) + len(stats) > 2000:
        response = response[:1950 - len(stats)] + "..."

    await message.reply(response + stats)


@bot.command(name="model")
async def model_cmd(ctx):
    await ctx.send(
        f"🧠 **Qwopus Dual-Model**\n"
        f"Proxy: `{QWOPUS_API}`\n"
        f"History: `{len(channel_history.get(ctx.channel.id, []))}` messages"
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
