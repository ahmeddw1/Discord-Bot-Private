import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

# ---------- OPTIONAL SPOTIFY ----------
SPOTIFY_ENABLED = False
try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

    if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
        sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            )
        )
        SPOTIFY_ENABLED = True
except Exception as e:
    print("⚠️ Spotify disabled:", e)

# ---------- YTDLP + FFMPEG ----------
ytdl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
}

ffmpeg_opts = {
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

    # ---------- PLAY ----------
    @commands.command()
    async def play(self, ctx, *, query: str):
        try:
            if not ctx.author.voice:
                return await ctx.send("❌ Join a voice channel first")

            if not ctx.voice_client:
                await ctx.author.voice.channel.connect()

            await ctx.send("🔍 Searching...")

            # 🎧 Spotify → YouTube (ONLY if enabled)
            if SPOTIFY_ENABLED and "open.spotify.com/track" in query:
                track = sp.track(query)
                query = f"{track['name']} {track['artists'][0]['name']}"

            def extract():
                info = ytdl.extract_info(
                    f"ytsearch:{query}", download=False
                )["entries"][0]
                return info["url"], info["title"]

            url, title = await asyncio.get_event_loop().run_in_executor(None, extract)

            source = discord.FFmpegPCMAudio(url, **ffmpeg_opts)

            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()

            ctx.voice_client.play(source)

            await ctx.send(f"🎶 Now playing: **{title}**")

        except Exception as e:
            print("❌ MUSIC ERROR:", e)
            await ctx.send("❌ Error playing this track")

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
