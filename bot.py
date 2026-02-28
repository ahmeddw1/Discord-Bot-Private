from dotenv import load_dotenv
load_dotenv("env.txt")

import discord
from discord.ext import commands
import asyncio
import os

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

# ---------- BOT ----------
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ---------- SETUP ----------
@bot.event
async def setup_hook():
    await bot.load_extension("music")
    await bot.load_extension("radio")
    await bot.load_extension("moderation")

    await bot.tree.sync()
    print("✅ Slash commands synced")

# ---------- READY ----------
@bot.event
async def on_ready():
    activity = discord.Activity(
        type=discord.ActivityType.listening,  # Listening, Playing, Watching, Competing
        name="24/7 | Online"                  # This is what it will show
    )
    await bot.change_presence(status=discord.Status.idle, activity=activity)

    print(f"✅ Logged in as {bot.user}")
    print(f"🌐 Connected to {len(bot.guilds)} servers")

# ---------- MAIN ----------
async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is missing")

    await bot.start(token)

# ---------- START ----------
if __name__ == "__main__":
    asyncio.run(main())






