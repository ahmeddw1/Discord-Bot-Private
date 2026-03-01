from dotenv import load_dotenv
import discord
from discord.ext import commands
import asyncio
import os
from aiohttp import web

# ---------- LOAD ENV ----------
load_dotenv("env.txt")

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True # Required for member lists
intents.presences = True # Required for Online/Offline counts

# ---------- BOT SETUP ----------
# Fixed: Instant IDLE status
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    status=discord.Status.idle,
    activity=discord.Activity(type=discord.ActivityType.listening, name="🌐 24/7 | Works")
)

# ---------- DASHBOARD API ----------
async def get_stats(request):
    server_list = []
    total_online = 0
    
    for guild in bot.guilds:
        # Fixed: Logic for Online vs Offline members
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        total_online += online
        
        server_list.append({
            "id": str(guild.id),
            "name": guild.name,
            "members": guild.member_count,
            "online": online,
            "offline": guild.member_count - online,
            "icon": str(guild.icon.url) if guild.icon else None
        })
    
    return web.json_response({
        "status": str(bot.status),
        "servers": len(bot.guilds),
        "users": sum(g.member_count for g in bot.guilds),
        "online": total_online,
        "offline": sum(g.member_count for g in bot.guilds) - total_online,
        "serverList": server_list
    })

async def update_status(request):
    data = await request.json()
    new_status = data.get('status', 'idle')
    new_type = data.get('type', 'LISTENING')
    new_name = data.get('name', 'Works')

    s_map = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd}
    t_map = {"PLAYING": discord.ActivityType.playing, "LISTENING": discord.ActivityType.listening, "WATCHING": discord.ActivityType.watching}

    await bot.change_presence(
        status=s_map.get(new_status, discord.Status.idle),
        activity=discord.Activity(type=t_map.get(new_type, discord.ActivityType.playing), name=new_name)
    )
    return web.json_response({"success": True})

# ---------- SETUP HOOK ----------
# ---------- SETUP ----------
@bot.event
async def setup_hook():
    # 1. Start the Dashboard Web Server first
    try:
        app = web.Application()
        app.router.add_get('/api/dashboard', get_stats)
        app.router.add_post('/api/settings/status', update_status)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 3000)
        asyncio.create_task(site.start())
        print("✅ Dashboard API started on port 3000")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")

    # 2. Load your extensions (Music, Radio, etc.)
    for ext in ["music", "radio", "moderation"]:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load {ext}: {e}")

    # 3. Sync commands with Error Handling for 50240
    try:
        print("Attempting to sync commands...")
        await bot.tree.sync()
        print("✅ Slash commands synced successfully")
    except discord.errors.HTTPException as e:
        if e.code == 50240:
            print("⚠️ Entry Point error (50240) detected.")
            print("⚠️ Ignoring the sync error so the bot stays online.")
        else:
            print(f"❌ HTTP Error during sync: {e}")
    await bot.tree.sync()

@bot.event
async def on_ready():
    print("=================================")
    print(f"✅ Logged in as {bot.user}")
    print(f"🌙 Status set to: IDLE")
    print(f"🌐 Connected to {len(bot.guilds)} servers")
    print("=================================")

async def main():
    token = os.getenv("DISCORD_TOKEN")
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())

