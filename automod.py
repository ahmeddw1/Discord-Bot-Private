import discord
from discord.ext import commands
import json

with open("config.json") as f:
    config = json.load(f)

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Bad words filter
        for word in config["bad_words"]:
            if word in message.content.lower():
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention} watch your language"
                )
                return

        # Mention spam
        if len(message.mentions) > config["max_mentions"]:
            await message.delete()
            await message.channel.send("🚫 Too many mentions")

async def setup(bot):
    await bot.add_cog(AutoMod(bot))