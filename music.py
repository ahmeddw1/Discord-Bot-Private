import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# ================= SPOTIFY =================
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise RuntimeError("Spotify credentials missing")

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


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- /join ----------
    @app_commands.command(name="join", description="Join your voice channel")
    async def join(self, interaction: discord.Interaction):
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

    # ---------- /play (SPOTIFY ONLY) ----------
    @app_commands.command(
        name="play",
        description="Play a Spotify track or playlist"
    )
    @app_commands.describe(spotify_url="Spotify track or playlist link")
    async def play(self, interaction: discord.Interaction, spotify_url: str):
        try:
            if not interaction.user.voice:
                return await interaction.response.send_message(
                    "❌ Join a voice channel first", ephemeral=True
                )

            vc = interaction.guild.voice_client
            if not vc:
                vc = await interaction.user.voice.channel.connect()

            if "open.spotify.com" not in spotify_url:
                return await interaction.response.send_message(
                    "❌ Only Spotify links are allowed", ephemeral=True
                )

            await interaction.response.send_message("🎧 Reading Spotify...")

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
                return await interaction.followup.send("❌ Unsupported Spotify link")

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

            await interaction.followup.send(f"🎶 Now playing: **{title}**")

        except Exception as e:
            print("❌ SPOTIFY SLASH ERROR:", repr(e))
            await interaction.followup.send("❌ Failed to play Spotify track")

    # ---------- /stop ----------
    @app_commands.command(name="stop", description="Stop music")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏹ Stopped")
        else:
            await interaction.response.send_message(
                "❌ Nothing is playing", ephemeral=True
            )

    # ---------- /leave ----------
    @app_commands.command(name="leave", description="Leave voice channel")
    async def leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("👋 Left voice channel")
        else:
            await interaction.response.send_message(
                "❌ Not connected", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Music(bot))
    bot.tree.add_command(Music(bot).join)
    bot.tree.add_command(Music(bot).play)
    bot.tree.add_command(Music(bot).stop)
    bot.tree.add_command(Music(bot).leave)
