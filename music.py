import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# ================= SPOTIFY SETUP =================
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
    "noplaylist": True,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
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

    # ---------- PLAY (SPOTIFY ONLY) ----------
    @commands.command()
    async def play(self, ctx, *, spotify_url: str):
        try:
            if not ctx.author.voice:
                return await ctx.send("❌ Join a voice channel first")

            if not ctx.voice_client:
                await ctx.author.voice.channel.connect()

            if "open.spotify.com" not in spotify_url:
                return await ctx.send("❌ Only Spotify links are allowed")

            await ctx.send("🎧 Reading Spotify track...")

            # -------- TRACK --------
            if "/track/" in spotify_url:
                track = sp.track(spotify_url)
                search = f"{track['name']} {track['artists'][0]['name']}"

            # -------- PLAYLIST (FIRST TRACK ONLY) --------
            elif "/playlist/" in spotify_url:
                playlist = sp.playlist_items(spotify_url, limit=1)
                track = playlist["items"][0]["track"]
                search = f"{track['name']} {track['artists'][0]['name']}"

            else:
                return await ctx.send("❌ Unsupported Spotify link")

            loop = asyncio.get_event_loop()

            def extract():
                data = ytdl.extract_info(search, download=False)
                if "entries" in data:
                    data = data["entries"][0]
                return data["url"], data["title"]

            url, title = await loop.run_in_executor(None, extract)

            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

            vc = ctx.voice_client
            if vc.is_playing():
                vc.stop()

            vc.play(source)

            await ctx.send(f"🎶 Now playing: **{title}**")

        except Exception as e:
            print("❌ SPOTIFY MUSIC ERROR:", repr(e))
            await ctx.send("❌ Failed to play Spotify track")

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
