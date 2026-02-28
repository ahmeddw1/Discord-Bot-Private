import discord
from discord.ext import commands

RADIO_STREAM_URL = "https://stream.lofi.cafe/lofi.mp3"

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def start_radio(self, voice_client):
        source = discord.FFmpegPCMAudio(
            RADIO_STREAM_URL,
            **FFMPEG_OPTIONS
        )
        voice_client.play(source)

    # ---------- PREFIX ----------
    @commands.command(name="radio")
    async def radio_prefix(self, ctx):
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel first")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        if ctx.voice_client.is_playing():
            return await ctx.send("📻 Radio is already playing")

        await self.start_radio(ctx.voice_client)
        await ctx.send("📻 Radio started (24/7)")

    # ---------- SLASH ----------
    @discord.app_commands.command(
        name="radio",
        description="Play 24/7 radio stream"
    )
    async def radio_slash(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not interaction.user.voice:
            return await interaction.followup.send("❌ Join a voice channel first")

        if not interaction.guild.voice_client:
            await interaction.user.voice.channel.connect()

        if interaction.guild.voice_client.is_playing():
            return await interaction.followup.send("📻 Radio already playing")

        await self.start_radio(interaction.guild.voice_client)
        await interaction.followup.send("📻 Radio started (24/7)")

    @discord.app_commands.command(
        name="radio_stop",
        description="Stop radio"
    )
    async def radio_stop(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("⏹ Radio stopped")


async def setup(bot):
    await bot.add_cog(Radio(bot))