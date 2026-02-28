import discord
from discord.ext import commands
from discord import app_commands
import json
import os
intents = discord.Intents.all()

with open("config.json") as f:
    config = json.load(f)

bot = commands.Bot(command_prefix=config["prefix"], intents=intents)

@bot.event
async def on_ready():
    status_map = {
        "online": discord.Status.online,
        "idle": discord.Status.idle,
        "dnd": discord.Status.dnd
    }

    await bot.change_presence(
        status=status_map[config["default_status"]],
        activity=discord.Game(config["status"])
    )

    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# Load cogs
bot.load_extension("music")
bot.load_extension("automod")


bot.run(os.getenv("DISCORD_TOKEN"))
