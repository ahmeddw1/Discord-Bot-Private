from dotenv import load_dotenv
import discord
from discord.ext import commands
import asyncio
import os

# ---------- LOAD ENV ----------
load_dotenv("env.txt")  # Make sure file name is correct

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
    try:
        await bot.load_extension("music")
        await bot.load_extension("radio")
        await bot.load_extension("moderation")

        await bot.tree.sync()  # Sync global slash commands
        print("✅ Slash commands synced")

    except Exception as e:
        print(f"❌ Extension error: {e}")

# ---------- READY ----------
@bot.event
async def on_ready():

    # Custom status (Listening)
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="🌐 24/7 | Works"
        )
    )

    print("=================================")
    print(f"✅ Logged in as {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"🌐 Connected to {len(bot.guilds)} servers")
    print("=================================")

# ---------- ERROR HANDLER ----------
@bot.event
async def on_command_error(ctx, error):
    print(f"❌ Command Error: {error}")

# ---------- MAIN ----------
async def main():
    token = os.getenv("DISCORD_TOKEN")

    if not token:
        raise RuntimeError("❌ DISCORD_TOKEN is missing in env.txt")

    async with bot:
        await bot.start(token)

# ---------- START ----------
if __name__ == "__main__":
    asyncio.run(main())
