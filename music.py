import discord
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

queues = {}

ytdl = yt_dlp.YoutubeDL({"format": "bestaudio", "quiet": True})
ffmpeg_opts = {"options": "-vn"}

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id="1a81aeeefd5247c0a6bc1d4698cf39d3",
        client_secret="95ec8923a60e4529969ebb78477161e0"
    )
)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_queue(self, guild_id):
        return queues.setdefault(guild_id, [])

    async def play_next(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            return

        source = queue.pop(0)
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(source, **ffmpeg_opts),
            after=lambda e: self.bot.loop.create_task(self.play_next(ctx))
        )

    @commands.hybrid_command(name="play")
    async def play(self, ctx, *, query: str):
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        # Spotify track → YouTube search
        if "spotify.com" in query:
            track = sp.track(query)
            query = f"{track['name']} {track['artists'][0]['name']}"

        info = ytdl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
        url = info["url"]

        queue = self.get_queue(ctx.guild.id)
        queue.append(url)

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

        await ctx.send(f"🎶 Added to queue: **{info['title']}**")

    @commands.hybrid_command(name="queue")
    async def queue(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            return await ctx.send("📭 Queue is empty")
        await ctx.send("\n".join([f"{i+1}. Song" for i in range(len(queue))]))

async def setup(bot):
    await bot.add_cog(Music(bot))