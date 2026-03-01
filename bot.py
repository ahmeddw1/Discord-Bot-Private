from dotenv import load_dotenv
import discord
from discord.ext import commands
import asyncio
import os
from aiohttp import web  # Add this for the dashboard connection

# ---------- LOAD ENV ----------
load_dotenv("env.txt")

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True
intents.presences = True  # CRITICAL: Must be ON in Developer Portal for online/offline counts

# ---------- BOT SETUP ----------
# Fixed: We set the status/activity here so it shows IDLE the moment it starts
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    status=discord.Status.idle,
    activity=discord.Activity(type=discord.ActivityType.listening, name="🌐 24/7 | Works")
)

# ---------- DASHBOARD API (The "Real" Link) ----------
async def get_stats(request):
    server_list = []
    for guild in bot.guilds:
        # Count online vs offline
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
    new_status = data.get('status', 'online')
    new_type = data.get('type', 'PLAYING')
    new_name = data.get('name', 'Works')

    status_map = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd}
    type_map = {"PLAYING": discord.ActivityType.playing, "LISTENING": discord.ActivityType.listening, "WATCHING": discord.ActivityType.watching}

    await bot.change_presence(
        status=status_map.get(new_status, discord.Status.online),
        activity=discord.Activity(type=type_map.get(new_type, discord.ActivityType.playing), name=new_name)
    )
    return web.json_response({"success": True})

# ---------- SETUP HOOK ----------
@bot.event
async def setup_hook():
    # Start the web server for the dashboard
    app = web.Application()
    app.router.add_get('/api/dashboard', get_stats)
    app.router.add_post('/api/settings/status', update_status)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 3000) # Dashboard port
    asyncio.create_task(site.start())

    try:
        await bot.load_extension("music")
        await bot.load_extension("radio")
        await bot.load_extension("moderation")
        await bot.tree.sync()
        print("✅ Slash commands synced & Dashboard API started")
    except Exception as e:
        print(f"❌ Error: {e}")

# ---------- READY ----------
@bot.event
async def on_ready():
    print("=================================")
    print(f"✅ Logged in as {bot.user}")
    print(f"🌙 Status: IDLE")
    print(f"🌐 Servers: {len(bot.guilds)}")
    print("=================================")

# ---------- MAIN ----------
async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("❌ DISCORD_TOKEN missing in env.txt")
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
