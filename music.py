import discord
from discord.ext import commands
import yt_dlp
import asyncio

YTDLP_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "default_search": "scsearch",
    "noplaylist": True,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    # ---------- QUEUE ----------
    def get_queue(self, guild_id):
        return self.queues.setdefault(guild_id, [])

    async def play_next(self, guild):
        queue = self.get_queue(guild.id)

        if not queue:
            return

        url = queue.pop(0)

        with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]

        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)

        guild.voice_client.play(
            source,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(guild), self.bot.loop
            ),
        )

    # ---------- PREFIX COMMANDS ----------
    @commands.command(name="play")
    async def play_prefix(self, ctx, *, query: str):
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel first")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        queue = self.get_queue(ctx.guild.id)
        queue.append(query)

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx.guild)

        await ctx.send(f"🎶 Added to queue:\n`{query}`")

    @commands.command(name="skip")
    async def skip_prefix(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭ Skipped")

    @commands.command(name="stop")
    async def stop_prefix(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queues[ctx.guild.id] = []
            await ctx.send("⏹ Stopped and left the channel")

    # ---------- SLASH COMMANDS ----------
    @discord.app_commands.command(name="play", description="Play SoundCloud music")
    async def play_slash(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            return await interaction.followup.send("❌ Join a voice channel first")

        if not interaction.guild.voice_client:
            await interaction.user.voice.channel.connect()

        queue = self.get_queue(interaction.guild.id)
        queue.append(query)

        if not interaction.guild.voice_client.is_playing():
            await self.play_next(interaction.guild)

        await interaction.followup.send(f"🎶 Added to queue:\n`{query}`")

    @discord.app_commands.command(name="skip", description="Skip current track")
    async def skip_slash(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("⏭ Skipped")

    @discord.app_commands.command(name="stop", description="Stop music and leave")
    async def stop_slash(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            self.queues[interaction.guild.id] = []
            await interaction.response.send_message("⏹ Stopped and left")


async def setup(bot):
    await bot.add_cog(Music(bot))
