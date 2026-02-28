import discord
from discord.ext import commands
from discord import app_commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------- CLEAR --------
    @app_commands.command(name="clear", description="Clear messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            return await interaction.response.send_message(
                "❌ Amount must be between 1 and 100", ephemeral=True
            )

        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(
            f"🧹 Cleared {amount} messages", ephemeral=True
        )

    # -------- BAN --------
    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str | None = None,
    ):
        await member.ban(reason=reason)
        await interaction.response.send_message(
            f"🔨 Banned {member.mention}"
        )

    # -------- UNBAN --------
    @app_commands.command(name="unban", description="Unban a user by ID")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        user = await self.bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(
            f"♻️ Unbanned {user.name}"
        )

    # -------- KICK --------
    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str | None = None,
    ):
        await member.kick(reason=reason)
        await interaction.response.send_message(
            f"👢 Kicked {member.mention}"
        )

    # -------- INVITE (REJOIN AFTER KICK) --------
    @app_commands.command(name="invite", description="Create an invite link")
    @app_commands.checks.has_permissions(create_instant_invite=True)
    async def invite(self, interaction: discord.Interaction):
        invite = await interaction.channel.create_invite(
            max_uses=1, unique=True
        )
        await interaction.response.send_message(
            f"🔗 Invite link:\n{invite.url}", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Moderation(bot))