# ================= LOAD ENV =================
from dotenv import load_dotenv
import os

load_dotenv("env.txt")

# ================= IMPORTS =================
import discord
from discord.ext import commands
import asyncio

# ================= INTENTS =================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

# ================= BOT =================
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ================= LOAD EXTENSIONS =================
async def load_extensions():
    await bot.load_extension("music")

# ================= EVENTS =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")
    print("✅ Slash commands synced")

# ================= MAIN =================
async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())
