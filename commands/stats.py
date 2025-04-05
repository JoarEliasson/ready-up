from discord.ext import commands
import discord
from models import UserManager

user_manager = UserManager()

@commands.command(name="stats")
async def stats(ctx: commands.Context, member: discord.Member = None) -> None:
    """Query stats of a user. Usage: !stats or !stats @User"""
    if member is None:
        member = ctx.author
    user_id = member.id
    user = user_manager.get_user(user_id)
    on_time = user.on_time_score
    late = user.late_count
    total_late_time_str = str(user.total_late_time).split('.')[0]  # Remove microseconds
    await ctx.send(
        f"📊 **Stats for {member.display_name}:**\n"
        f"✅ On-Time Arrivals: **{on_time}**\n"
        f"⌛ Late Arrivals: **{late}**\n"
        f"⏱ Total Late Time: **{total_late_time_str}**"
    )