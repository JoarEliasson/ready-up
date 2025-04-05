from discord.ext import commands
from datetime import datetime, time, timedelta
from models import UserManager, BOT_TIMEZONE

user_manager = UserManager()

@commands.command(name="eta")
async def set_eta(ctx: commands.Context, time_str: str) -> None:
    """Set your gaming session arrival time. Usage: !eta HH:MM"""
    try:
        hour, minute = map(int, time_str.split(":"))
        now = datetime.now(BOT_TIMEZONE)
        eta_time = time(hour, minute)
        eta_dt = BOT_TIMEZONE.localize(datetime.combine(now.date(), eta_time))
        if eta_dt < now:
            eta_dt += timedelta(days=1)
    except ValueError:
        await ctx.send("❌ Invalid time format. Please use `!eta HH:MM` in 24-hour format.")
        return

    user = user_manager.get_user(ctx.author.id)
    user.eta = eta_dt
    user.arrived = False
    user.channel_id = ctx.channel.id
    user.notifications_sent = set()

    await ctx.send(f"⏰ <@{ctx.author.id}>, your gaming session is scheduled for **{eta_dt.strftime('%Y-%m-%d %H:%M')}**.")