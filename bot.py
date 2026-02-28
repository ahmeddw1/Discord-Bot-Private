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
# Panel URL from environment variable (optional: you can hardcode here too)
PANEL_URL = os.environ.get("PANEL_URL", "https://botpanel-ahmeddw.netlify.app/")

class Panel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="panel", description="Get the link to the dashboard panel")
    async def panel(self, interaction: discord.Interaction):
        # Create a button
        button = discord.ui.Button(label="Open Panel", url=PANEL_URL, style=discord.ButtonStyle.link)
        view = discord.ui.View()
        view.add_item(button)

        # Send the message with the button (ephemeral so only the user sees it)
        await interaction.response.send_message("Click the button below to open the panel:", view=view, ephemeral=True)

# Add the cog
bot.add_cog(Panel(bot))
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
    # 🔴 STATUS TYPE OPTIONS:
    # discord.Status.online
    # discord.Status.idle
    # discord.Status.dnd

    activity = discord.Activity(
        type=discord.ActivityType.listening,
        name="🌐 24/7 | Free"
    )

    await bot.change_presence(
        status=discord.Status.dnd,
        activity=activity
    )

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





