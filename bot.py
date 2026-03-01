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
intents.presences = True # Required for Online/Offline dashboard counts

# We set status=idle here so it never flashes green
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    status=discord.Status.idle,
    activity=discord.Activity(type=discord.ActivityType.listening, name="🌐 24/7 | Works")
)

# ---------- 2. RADIO CONFIGURATION ----------
RADIO_URL = "http://n02.radiojar.com/0tpy1h0kxtzuv"
FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# ---------- 3. DASHBOARD API LOGIC ----------
async def get_stats(request):
    server_list = []
    for guild in bot.guilds:
        # Calculate Online vs Offline for the dashboard
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        server_list.append({
            "id": str(guild.id),
            "name": guild.name,
            "total": guild.member_count,
            "online": online,
            "offline": guild.member_count - online,
            "icon": str(guild.icon.url) if guild.icon else None
        })
    
    return web.json_response({
        "status": str(bot.status),
        "servers": len(bot.guilds),
        "users": sum(g.member_count for g in bot.guilds),
        "serverList": server_list
    })

async def update_status(request):
    data = await request.json()
    s_map = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd}
    t_map = {"PLAYING": discord.ActivityType.playing, "LISTENING": discord.ActivityType.listening, "WATCHING": discord.ActivityType.watching}

    await bot.change_presence(
        status=s_map.get(data.get('status'), discord.Status.idle),
        activity=discord.Activity(
            type=t_map.get(data.get('type'), discord.ActivityType.listening), 
            name=data.get('name', 'Works')
        )
    )
    return web.json_response({"success": True})

# ---------- 4. BOT EVENTS & SYNC FIX ----------
@bot.event
async def setup_hook():
    # Start Dashboard Web Server
    app = web.Application()
    app.router.add_get('/api/dashboard', get_stats)
    app.router.add_post('/api/settings/status', update_status)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 3000)
    asyncio.create_task(site.start())

    # Load other cogs if you still have them
    for ext in ["music", "moderation"]:
        try:
            await bot.load_extension(ext)
        except:
            pass

    # FIXED: Sync logic that ignores the 50240 Entry Point error
    try:
        await bot.tree.sync()
        print("✅ Commands synced")
    except discord.errors.HTTPException as e:
        if e.code == 50240:
            print("⚠️ Entry Point error ignored - Bot starting anyway.")

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is Online and IDLE")

# ---------- 5. RADIO COMMANDS (Integrated) ----------
@bot.hybrid_command(name="radio", description="Play 24/7 Radio")
async def radio(ctx):
    if not ctx.author.voice:
        return await ctx.send("❌ Join a voice channel first")
    
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()
    
    source = discord.FFmpegPCMAudio(RADIO_URL, **FFMPEG_OPTS)
    ctx.voice_client.play(discord.PCMVolumeTransformer(source, volume=0.5))
    await ctx.send("📻 **Radio started!**")

@bot.hybrid_command(name="stop", description="Stop the radio")
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⏹ Stopped")

# ---------- 6. START ----------
async def main():
    token = os.getenv("DISCORD_TOKEN")
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
