import discord
from discord.ext import commands
import os
import json

# ---------- LOAD CONFIG ----------
with open("config.json", "r") as f:
    config = json.load(f)

# ---------- INTENTS (VERY IMPORTANT) ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix=config.get("prefix", "!"),
    intents=intents
)

# ---------- BOT READY ----------
@bot.event
async def on_ready():
    status_map = {
        "online": discord.Status.online,
        "idle": discord.Status.idle,
        "dnd": discord.Status.dnd
    }

    await bot.change_presence(
        status=status_map.get(config.get("default_status", "online")),
        activity=discord.Game(config.get("status", "Bot Online"))
    )

    print(f"✅ Logged in as {bot.user}")

# ---------- TEST COMMAND ----------
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 pong") 


@bot.event
async def on_ready():
    await bot.tree.sync()
    print("✅ Slash commands synced")
    
# ---------- LOAD COGS ----------
async def load_extensions():
    await bot.load_extension("music")
    await bot.load_extension("automod")

# ---------- START BOT ----------
async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv("DISCORD_TOKEN") or config["token"])

import asyncio
asyncio.run(main())

