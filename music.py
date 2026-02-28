# ================= LOAD ENV =================
from dotenv import load_dotenv
import os

load_dotenv("env.txt")

# ================= IMPORTS =================
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# ================= SPOTIFY =================
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise RuntimeError("Spotify credentials are missing")

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
)

# ================= YTDLP / FFMPEG =================
ytdl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "default_search": "ytsearch",
    "noplaylist": True
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

ytdl = yt_dlp.YoutubeDL(ytdl_opts)

# ================= MUSIC COG =================
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==================================================
    # JOIN (PREFIX)
    # ==================================================
    @commands.command()
    async def join(self, ctx):
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel first")

        if ctx.voice_client:
            return await ctx.send("✅ Already connected")

        await ctx.author.voice.channel.connect()
        await ctx.send("🎧 Joined voice channel")

    # ==================================================
    # JOIN (SLASH)
    # ==================================================
    @app_commands.command(name="join", description="Join your voice channel")
    async def join_slash(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            return await interaction.response.send_message(
                "❌ Join a voice channel first", ephemeral=True
            )

        if interaction.guild.voice_client:
            return await interaction.response.send_message(
                "✅ Already connected", ephemeral=True
            )

        await interaction.user.voice.channel.connect()
        await interaction.response.send_message("🎧 Joined voice channel")

    # ==================================================
    # PLAY (PREFIX)
    # ==================================================
    @commands.command()
    async def play(self, ctx, spotify_url: str):
        await self._play_music(ctx, spotify_url)

    # ==================================================
    # PLAY (SLASH)
    # ==================================================
    @app_commands.command(name="play", description="Play a Spotify track or playlist")
    async def play_slash(self, interaction: discord.Interaction, spotify_url: str):
        await interaction.response.defer()
        await self._play_music(interaction, spotify_url, slash=True)

    # ==================================================
    # CORE PLAY LOGIC
    # ==================================================
    async def _play_music(self, ctx, spotify_url: str, slash=False):
        try:
            user = ctx.user if slash else ctx.author
            guild = ctx.guild

            if not user.voice:
                msg = "❌ Join a voice channel first"
                return await (ctx.followup.send(msg) if slash else ctx.send(msg))

            vc = guild.voice_client
            if not vc:
                vc = await user.voice.channel.connect()

            if "open.spotify.com" not in spotify_url:
                msg = "❌ Only Spotify links allowed"
                return await (ctx.followup.send(msg) if slash else ctx.send(msg))

            # ---------- TRACK ----------
            if "/track/" in spotify_url:
                track = sp.track(spotify_url)
                search = f"{track['name']} {track['artists'][0]['name']}"

            # ---------- PLAYLIST (FIRST TRACK ONLY) ----------
            elif "/playlist/" in spotify_url:
                playlist = sp.playlist_items(spotify_url, limit=1)
                track = playlist["items"][0]["track"]
                search = f"{track['name']} {track['artists'][0]['name']}"

            else:
                msg = "❌ Unsupported Spotify link"
                return await (ctx.followup.send(msg) if slash else ctx.send(msg))

            loop = asyncio.get_event_loop()

            def extract():
                data = ytdl.extract_info(search, download=False)
                if "entries" in data:
                    data = data["entries"][0]
                return data["url"], data["title"]

            url, title = await loop.run_in_executor(None, extract)

            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

            if vc.is_playing():
                vc.stop()

            vc.play(source)

            msg = f"🎶 Now playing: **{title}**"
            await (ctx.followup.send(msg) if slash else ctx.send(msg))

        except Exception as e:
            print("❌ MUSIC ERROR:", e)
            msg = "❌ Error playing this track"
            await (ctx.followup.send(msg) if slash else ctx.send(msg))

    # ==================================================
    # STOP (PREFIX)
    # ==================================================
    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏹ Stopped")
        else:
            await ctx.send("❌ Nothing is playing")

    # ==================================================
    # STOP (SLASH)
    # ==================================================
    @app_commands.command(name="stop", description="Stop music")
    async def stop_slash(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏹ Stopped")
        else:
            await interaction.response.send_message(
                "❌ Nothing is playing", ephemeral=True
            )

    # ==================================================
    # LEAVE (PREFIX)
    # ==================================================
    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Left voice channel")
        else:
            await ctx.send("❌ Not connected")

    # ==================================================
    # LEAVE (SLASH)
    # ==================================================
    @app_commands.command(name="leave", description="Leave voice channel")
    async def leave_slash(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("👋 Left voice channel")
        else:
            await interaction.response.send_message(
                "❌ Not connected", ephemeral=True
            )

# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(Music(bot))
