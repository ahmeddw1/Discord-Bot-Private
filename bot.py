import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from aiohttp import web
from dotenv import load_dotenv

# ---------- 1. SETUP & INTENTS ----------
load_dotenv("env.txt")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.presences = True 

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    status=discord.Status.dnd,
    activity=discord.Activity(type=discord.ActivityType.listening, name="📻 Radio 24/7")
)

# ---------- 2. RADIO CONFIGURATION (FIXED FOR SOUND) ----------
RADIO_URL = "http://n02.radiojar.com/0tpy1h0kxtzuv"

# Fixed FFmpeg options to prevent silent timeouts and force audio reconnection
FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -loglevel panic'
}

# ---------- 3. RADIO LOGIC (FIXED) ----------
async def start_radio(vc):
    """Helper function to handle audio source creation and playback"""
    if vc.is_playing():
        vc.stop()
    
    # We use PCMVolumeTransformer to ensure the stream is wrapped correctly for Discord
    source = discord.FFmpegPCMAudio(RADIO_URL, **FFMPEG_OPTS)
    transformed_source = discord.PCMVolumeTransformer(source, volume=0.5)
    
    vc.play(transformed_source, after=lambda e: print(f'Player error: {e}') if e else None)

# ---------- 4. COMMANDS (PREFIX & SLASH) ----------
@bot.hybrid_command(name="radio", description="Play 24/7 Radio")
async def radio(ctx):
    if not ctx.author.voice:
        return await ctx.send("❌ You must be in a voice channel!")
    
    # Connect or Move to the user's channel
    if not ctx.voice_client:
        vc = await ctx.author.voice.channel.connect()
    else:
        vc = ctx.voice_client
        if vc.channel != ctx.author.voice.channel:
            await vc.move_to(ctx.author.voice.channel)

    await start_radio(vc)
    await ctx.send("📻 **Radio is now playing!** (If no sound, wait 3 seconds)")

@bot.hybrid_command(name="stop", description="Stop the radio and leave")
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⏹ Radio stopped.")

# ---------- 5. DASHBOARD API & SYNC FIX ----------
async def get_stats(request):
    server_list = []
    for guild in bot.guilds:
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        server_list.append({
            "name": guild.name,
            "online": online,
            "total": guild.member_count,
            "icon": str(guild.icon.url) if guild.icon else None
        })
    return web.json_response({"status": str(bot.status), "serverList": server_list})

@bot.event
async def setup_hook():
    # Start API for Dashboard
    app = web.Application()
    app.router.add_get('/api/dashboard', get_stats)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 3000).start()

    # Sync commands while ignoring Entry Point errors
    try:
        await bot.tree.sync()
    except discord.HTTPException as e:
        if e.code == 50240: print("⚠️ Ignoring Entry Point error.")

# ---------- 6. RUN ----------
async def main():
    token = os.getenv("DISCORD_TOKEN")
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())

