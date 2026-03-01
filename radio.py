import discord
from discord.ext import commands
from discord import app_commands

# ✅ UPDATED STREAM URL & STABLE OPTIONS
RADIO_STREAM_URL = "http://n02.radiojar.com/0tpy1h0kxtzuv"

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "volume=0.5"' # Added volume control and removed video
}

class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def play_radio(self, voice_client: discord.VoiceClient):
        # Clear existing audio if playing
        if voice_client.is_playing():
            voice_client.stop()

        # Added FFmpegPCMAudio with specific executable path if needed (default is 'ffmpeg')
        # We wrap the source in discord.PCMVolumeTransformer to handle volume better
        source = discord.FFmpegPCMAudio(
            RADIO_STREAM_URL,
            **FFMPEG_OPTIONS
        )
        
        # Fixed: Ensure we use the correct AudioSource wrapper
        voice_client.play(discord.PCMVolumeTransformer(source, volume=0.5))

    # ---------- PREFIX COMMAND ----------
    @commands.command(name="radio")
    async def radio_prefix(self, ctx):
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel first")

        # Connect if not connected
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
        
        # Ensure bot moves to user's channel if already in another
        elif ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.voice_client.move_to(ctx.author.voice.channel)

        await self.play_radio(ctx.voice_client)
        await ctx.send("📻 **Radio is now playing (24/7)**")

    # ---------- SLASH COMMAND ----------
    @app_commands.command(
        name="radio",
        description="Play 24/7 radio"
    )
    async def radio_slash(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Join a voice channel first", ephemeral=True)

        await interaction.response.defer()

        # Connect logic
        if not interaction.guild.voice_client:
            vc = await interaction.user.voice.channel.connect()
        else:
            vc = interaction.guild.voice_client
            if vc.channel != interaction.user.voice.channel:
                await vc.move_to(interaction.user.voice.channel)

        await self.play_radio(vc)
        await interaction.followup.send("📻 **Radio is now playing (24/7)**")

    @app_commands.command(
        name="radio_stop",
        description="Stop radio and leave"
    )
    async def radio_stop(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("⏹ Radio stopped and bot left the channel.")
        else:
            await interaction.response.send_message("❌ I am not in a voice channel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Radio(bot))
