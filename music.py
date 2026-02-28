import discord
from discord.ext import commands
import yt_dlp
import asyncio

YTDLP_OPTIONS = {
    "format": "bestaudio[ext=mp3]/bestaudio",
    "quiet": True,
    "default_search": "scsearch",
    "noplaylist": True,
    "nocheckcertificate": True,
    "user_agent": "Mozilla/5.0",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    def get_queue(self, guild_id):
        return self.queues.setdefault(guild_id, [])

    async def play_next(self, guild):
        queue = self.get_queue(guild.id)
        if not queue:
            return

        query = queue.pop(0)

        with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)

        # 🔥 FIX: GET REAL AUDIO STREAM
        if "formats" in info:
            audio_url = next(
                f["url"] for f in info["formats"]
                if f.get("acodec") != "none"
            )
        else:
            audio_url = info["url"]

        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)

        guild.voice_client.play(
            source,
            after=lambda _: asyncio.run_coroutine_threadsafe(
                self.play_next(guild),
                self.bot.loop
            )
        )

    # ---------- PREFIX ----------
    @commands.command()
    async def play(self, ctx, *, query: str):
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel first")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        self.get_queue(ctx.guild.id).append(query)

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx.guild)

        await ctx.send(f"🎶 Playing:\n`{query}`")

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            await ctx.send("⏭ Skipped")

    # ---------- SLASH ----------
    @discord.app_commands.command(name="play", description="Play SoundCloud music")
    async def play_slash(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            return await interaction.followup.send("❌ Join a voice channel first")

        if not interaction.guild.voice_client:
            await interaction.user.voice.channel.connect()

        self.get_queue(interaction.guild.id).append(query)

        if not interaction.guild.voice_client.is_playing():
            await self.play_next(interaction.guild)

        await interaction.followup.send(f"🎶 Playing:\n`{query}`")

    @discord.app_commands.command(name="skip", description="Skip track")
    async def skip_slash(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("⏭ Skipped")


async def setup(bot):
    await bot.add_cog(Music(bot))
