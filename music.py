import discord
from discord.ext import commands
import yt_dlp
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# ---------- SPOTIFY SETUP ----------
SPOTIFY_CLIENT_ID = "YOUR_SPOTIFY_CLIENT_ID"
SPOTIFY_CLIENT_SECRET = "YOUR_SPOTIFY_CLIENT_SECRET"

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=1a81aeeefd5247c0a6bc1d4698cf39d3,
        client_secret=95ec8923a60e4529969ebb78477161e0
    )
)

# ---------- YTDLP + FFMPEG ----------
ytdl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True
}

ffmpeg_opts = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

ytdl = yt_dlp.YoutubeDL(ytdl_opts)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- JOIN ----------
    @commands.command()
    async def join(self, ctx):
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel first")

        if ctx.voice_client:
            return await ctx.send("✅ Already connected")

        await ctx.author.voice.channel.connect()
        await ctx.send("🎧 Joined voice channel")

    # ---------- PLAY ----------
    @commands.command()
    async def play(self, ctx, *, query: str):
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel first")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        await ctx.send("🔍 Processing request...")

        # 🎧 Spotify track → YouTube search
        if "open.spotify.com/track" in query:
            track = sp.track(query)
            query = f"{track['name']} {track['artists'][0]['name']}"

        # 🎧 Spotify playlist → first track only (safe)
        if "open.spotify.com/playlist" in query:
            playlist = sp.playlist_items(query, limit=1)
            track = playlist["items"][0]["track"]
            query = f"{track['name']} {track['artists'][0]['name']}"

        def get_audio():
            info = ytdl.extract_info(
                f"ytsearch:{query}", download=False
            )["entries"][0]
            return info["url"], info["title"]

        url, title = await asyncio.get_event_loop().run_in_executor(None, get_audio)

        source = discord.FFmpegPCMAudio(url, **ffmpeg_opts)

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        ctx.voice_client.play(source)

        await ctx.send(f"🎶 Now playing: **{title}**")

    # ---------- STOP ----------
    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏹ Stopped")

    # ---------- LEAVE ----------
    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Left voice channel")


async def setup(bot):
    await bot.add_cog(Music(bot))
