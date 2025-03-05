import os
import json
import atexit
import asyncio
import logging
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("readyup.log"),
        logging.StreamHandler()
    ]
)

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
USER_DATA_FILE = "user_data.json"

RULES_MESSAGE = """
**================== ReadyUp Rules ==================**

1. **Set Your Gaming Session Arrival Time:**
   - **Command:** `!eta HH:MM`  
     *(24-hour format, e.g., `!eta 19:00`)*

2. **Mark Your Arrival:**
   - **Automatically:** Join a voice channel.
   - **Manually:** Type `!ready` or `!rdy` in chat.

3. **Scheduled Notifications if You're Late:**
   - **1 Minute Before Your ETA**
   - **15, 30, and 60 Minutes Late**
   - **24 Hours Late** = Final no-show alert.

4. **Check User Stats:**
   - **Command:** `!stats @User`

5. **View These Rules Again:**
   - **Command:** `!rules`

**Have Fun and Stay On Time!**

**===================================================**
"""

# In-memory user data:
# user_data[user_id] = {
#   "eta": datetime,
#   "on_time_score": int,
#   "late_count": int,
#   "arrived": bool,
#   "channel_id": int,
#   "notifications_sent": set,
# }
user_data: dict[int, dict] = {}

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


def serialize_user_data(data: dict[int, dict]) -> dict:
    """Converts the user_data into a JSON-serializable dictionary."""
    serializable = {}
    for user_id, info in data.items():
        serializable[str(user_id)] = {
            "eta": info["eta"].isoformat() if info.get("eta") else None,
            "on_time_score": info.get("on_time_score", 0),
            "late_count": info.get("late_count", 0),
            "arrived": info.get("arrived", False),
            "channel_id": info.get("channel_id", 0),
            "notifications_sent": list(info.get("notifications_sent", [])),
        }
    return serializable


def deserialize_user_data(serialized: dict) -> dict[int, dict]:
    """Converts a serialized user_data dict back into the appropriate format."""
    data = {}
    for user_id_str, info in serialized.items():
        try:
            user_id = int(user_id_str)
            data[user_id] = {
                "eta": datetime.fromisoformat(info["eta"]) if info.get("eta") else None,
                "on_time_score": info.get("on_time_score", 0),
                "late_count": info.get("late_count", 0),
                "arrived": info.get("arrived", False),
                "channel_id": info.get("channel_id", 0),
                "notifications_sent": set(info.get("notifications_sent", [])),
            }
        except Exception as e:
            logging.error(f"Error deserializing data for user {user_id_str}: {e}")
    return data


def load_user_data() -> dict[int, dict]:
    """Loads user data from the JSON file."""
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                serialized = json.load(f)
            logging.info("User data loaded from file.")
            return deserialize_user_data(serialized)
        except Exception as e:
            logging.error(f"Error loading user data: {e}")
    return {}


def save_user_data() -> None:
    """Saves user data to the JSON file."""
    try:
        with open(USER_DATA_FILE, "w") as f:
            json.dump(serialize_user_data(user_data), f, indent=4)
        logging.info("User data saved to file.")
    except Exception as e:
        logging.error(f"Error saving user data: {e}")


atexit.register(save_user_data)


@bot.event
async def on_ready() -> None:
    logging.info(RULES_MESSAGE)
    logging.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    bot.loop.create_task(check_intervals())
    logging.info("Background task for scheduled notifications started.")


@bot.command(name="eta")
async def set_eta(ctx: commands.Context, time_str: str) -> None:
    """
    Set your gaming session arrival time.
    Usage: !eta HH:MM (24-hour format)
    """
    try:
        now = datetime.now()
        hour, minute = map(int, time_str.split(":"))
        eta_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if eta_dt < now:
            eta_dt += timedelta(days=1)
    except ValueError:
        await ctx.send("❌ Invalid time format. Please use `!eta HH:MM` in 24-hour format.")
        return

    user_id = ctx.author.id
    user_info = user_data.get(user_id, {
        "on_time_score": 0,
        "late_count": 0,
        "arrived": False,
        "channel_id": ctx.channel.id,
        "notifications_sent": set(),
    })
    user_info.update({
        "eta": eta_dt,
        "arrived": False,
        "channel_id": ctx.channel.id,
        "notifications_sent": set(),
    })
    user_data[user_id] = user_info

    await ctx.send(f"⏰ <@{user_id}>, your gaming session is scheduled for **{eta_dt.strftime('%Y-%m-%d %H:%M')}**.")


@bot.command(aliases=["rdy"])
async def ready(ctx: commands.Context) -> None:
    """
    Mark yourself as ready.
    Usage: !ready or !rdy
    """
    user_id = ctx.author.id
    if user_id not in user_data or not user_data[user_id].get("eta"):
        await ctx.send("❌ You haven't set an ETA yet! Please use `!eta HH:MM` first.")
        return

    if user_data[user_id]["arrived"]:
        await ctx.send("⚠️ You have already marked your arrival!")
        return

    user_data[user_id]["arrived"] = True
    eta_dt = user_data[user_id]["eta"]
    now = datetime.now()
    if now - eta_dt <= timedelta(0):
        user_data[user_id]["on_time_score"] += 1
        await ctx.send(
            f"✅ Great job, <@{user_id}>! You arrived on time.\n"
            f"**Total On-Time Arrivals:** {user_data[user_id]['on_time_score']}"
        )
    else:
        user_data[user_id]["late_count"] += 1
        diff_minutes = int((now - eta_dt).total_seconds() / 60)
        await ctx.send(
            f"😅 Oops, <@{user_id}>! You arrived **{diff_minutes}** minute(s) late.\n"
            f"**Late Arrivals:** {user_data[user_id]['late_count']} | **On-Time Arrivals:** {user_data[user_id]['on_time_score']}"
        )


@bot.command(name="stats")
async def stats(ctx: commands.Context, member: discord.Member) -> None:
    """
    Query stats of a user.
    Usage: !stats @User
    """
    target_id = member.id
    if target_id in user_data:
        on_time = user_data[target_id]["on_time_score"]
        late = user_data[target_id]["late_count"]
        await ctx.send(
            f"📊 **Stats for {member.display_name}:**\n"
            f"✅ On-Time Arrivals: **{on_time}**\n"
            f"⌛ Late Arrivals: **{late}**"
        )
    else:
        await ctx.send(f"ℹ️ **{member.display_name}** has no recorded stats yet.")


@bot.command(name="rules")
async def rules(ctx: commands.Context) -> None:
    """
    Display the bot rules.
    Usage: !rules
    """
    await ctx.send(RULES_MESSAGE)


@bot.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
) -> None:
    """
    Auto-detect voice channel joins to mark arrival.
    """
    if before.channel is None and after.channel is not None:
        user_id = member.id
        if user_id in user_data and not user_data[user_id]["arrived"]:
            eta_dt = user_data[user_id]["eta"]
            user_data[user_id]["arrived"] = True
            channel = bot.get_channel(user_data[user_id]["channel_id"])
            if channel is None:
                logging.warning(f"Channel ID {user_data[user_id]['channel_id']} not found for user {member.display_name}.")
                return

            now = datetime.now()
            if now - eta_dt <= timedelta(0):
                user_data[user_id]["on_time_score"] += 1
                await channel.send(
                    f"✅ <@{user_id}>, you joined on time via voice!\n"
                    f"**Total On-Time Arrivals:** {user_data[user_id]['on_time_score']}"
                )
                logging.info(f"{member.display_name} arrived on time via voice.")
            else:
                user_data[user_id]["late_count"] += 1
                diff_minutes = int((now - eta_dt).total_seconds() / 60)
                await channel.send(
                    f"😅 <@{user_id}>, you joined **{diff_minutes}** minute(s) late via voice.\n"
                    f"**Late Arrivals:** {user_data[user_id]['late_count']} | **On-Time Arrivals:** {user_data[user_id]['on_time_score']}"
                )
                logging.info(f"{member.display_name} arrived {diff_minutes} minute(s) late via voice.")


async def check_intervals() -> None:
    """
    Background task to check scheduled notifications and send reminders.
    Checks for:
      - 1 minute before ETA,
      - 15, 30, and 60 minutes late,
      - 24-hour no-show.
    """
    while True:
        now = datetime.now()
        to_remove: list[int] = []

        for user_id, info in list(user_data.items()):
            if info.get("arrived"):
                continue

            eta_dt = info.get("eta")
            channel_id = info.get("channel_id")
            notifications_sent = info.get("notifications_sent", set())
            channel = bot.get_channel(channel_id)
            if not channel or not eta_dt:
                continue

            delta_minutes = (now - eta_dt).total_seconds() / 60

            if delta_minutes >= 24 * 60 and "no_show" not in notifications_sent:
                notifications_sent.add("no_show")
                try:
                    await channel.send(
                        f"🚨 <@{user_id}>, you did not show up! 24 hours have passed since your scheduled time."
                    )
                except Exception as e:
                    logging.error(f"Failed to send no-show notification: {e}")
                to_remove.append(user_id)
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
                if condition(delta_minutes) and key not in notifications_sent:
                    notifications_sent.add(key)
                    try:
                        await channel.send(message)
                    except Exception as e:
                        logging.error(f"Failed to send notification for interval {key}: {e}")

        for uid in to_remove:
            user_data.pop(uid, None)

        await asyncio.sleep(60)


if __name__ == "__main__":
    user_data = load_user_data()
    bot.run(DISCORD_TOKEN)