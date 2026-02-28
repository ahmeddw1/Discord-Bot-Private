import discord
from discord.ext import commands

# ✅ WORKING RADIO STREAM (Radio Fm)
RADIO_STREAM_URL = "http://stream.radiojar.com/0tpy1h0kxtzuv"

FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 "
        "-reconnect_streamed 1 "
        "-reconnect_delay_max 5 "
        "-loglevel panic"
    ),
    "options": "-vn"
}


class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def play_radio(self, voice_client: discord.VoiceClient):
        if voice_client.is_playing():
            voice_client.stop()

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

        await self.play_radio(ctx.voice_client)
        await ctx.send("📻 Radio is now playing (24/7)")

    # ---------- SLASH ----------
    @discord.app_commands.command(
        name="radio",
        description="Play 24/7 radio"
    )
    async def radio_slash(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not interaction.user.voice:
            return await interaction.followup.send(
                "❌ Join a voice channel first"
            )

        if not interaction.guild.voice_client:
            await interaction.user.voice.channel.connect()

        await self.play_radio(interaction.guild.voice_client)
        await interaction.followup.send("📻 Radio is now playing (24/7)")

    @discord.app_commands.command(
        name="radio_stop",
        description="Stop radio and leave"
    )
    async def radio_stop(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("⏹ Radio stopped")


async def setup(bot):
    await bot.add_cog(Radio(bot))

