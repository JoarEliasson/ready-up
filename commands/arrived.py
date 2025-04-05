from discord.ext import commands
from datetime import datetime
from models import UserManager, BOT_TIMEZONE

user_manager = UserManager()

@commands.command(name="arrived")
async def arrived(ctx: commands.Context) -> None:
    """Mark yourself as arrived. Usage: !arrived"""
    user_id = ctx.author.id
    user = user_manager.get_user(user_id)
    if not user.eta:
        await ctx.send("❌ You haven't set an ETA yet! Please use `!eta HH:MM` first.")
        return
    if user.arrived:
        await ctx.send("⚠️ You have already marked your arrival!")
        return

    user.arrived = True
    now = datetime.now(BOT_TIMEZONE)
    if now <= user.eta:
        user.on_time_score += 1
        await ctx.send(
            f"✅ Great job, <@{user_id}>! You arrived on time.\n"
            f"**Total On-Time Arrivals:** {user.on_time_score}"
        )
    else:
        late_time = now - user.eta
        user.late_count += 1
        user.total_late_time += late_time
        diff_minutes = int(late_time.total_seconds() / 60)
        await ctx.send(
            f"😅 Oops, <@{user_id}>! You arrived **{diff_minutes}** minute(s) late.\n"
            f"**Late Arrivals:** {user.late_count} | **On-Time Arrivals:** {user.on_time_score}"
        )