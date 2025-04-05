import asyncio
import logging
from datetime import datetime
from models import UserManager, BOT_TIMEZONE

user_manager = UserManager()

async def check_intervals(bot):
    while True:
        now = datetime.now(BOT_TIMEZONE)
        for user_id, user in list(user_manager.users.items()):
            if user.arrived or not user.eta:
                continue
            eta_dt = user.eta
            channel = bot.get_channel(user.channel_id)
            if not channel:
                continue
            delta_minutes = (now - eta_dt).total_seconds() / 60
            if delta_minutes >= 24 * 60 and "no_show" not in user.notifications_sent:
                user.notifications_sent.add("no_show")
                try:
                    await channel.send(
                        f"🚨 <@{user_id}>, you did not show up! 24 hours have passed since your scheduled time."
                    )
                except Exception as e:
                    logging.error(f"Failed to send no-show notification: {e}")
                del user_manager.users[user_id]
                continue
            intervals = [
                (
                    lambda dm: -1.0 <= dm < 0,
                    "one_min_before",
                    f"⏰ Heads up, <@{user_id}>! Your session starts in 1 minute."
                ),
                (
                    lambda dm: 15 <= dm < 16,
                    "15min_late",
                    f"⌛ <@{user_id}>, you're 15 minutes late. Time to get moving!"
                ),
                (
                    lambda dm: 30 <= dm < 31,
                    "30min_late",
                    f"⌛ <@{user_id}>, you're 30 minutes late. Hurry up!"
                ),
                (
                    lambda dm: 60 <= dm < 61,
                    "60min_late",
                    f"⏰ <@{user_id}>, you're 60 minutes late. Seriously, what happened?"
                )
            ]
            for condition, key, message in intervals:
                if condition(delta_minutes) and key not in user.notifications_sent:
                    user.notifications_sent.add(key)
                    try:
                        await channel.send(message)
                    except Exception as e:
                        logging.error(f"Failed to send notification for interval {key}: {e}")
        await asyncio.sleep(60)