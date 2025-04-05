from datetime import datetime
from models import BOT_TIMEZONE


async def handle_arrival(user, user_id, channel, via_voice=False):
    now = datetime.now(BOT_TIMEZONE)
    source = "via voice" if via_voice else ""
    if now <= user.eta:
        user.on_time_score += 1
        await channel.send(
            f"✅ <@{user_id}>, you arrived on time {source}!\n"
            f"**Total On-Time Arrivals:** {user.on_time_score}"
        )
    else:
        late_time = now - user.eta
        user.late_count += 1
        user.total_late_time += late_time
        diff_minutes = int(late_time.total_seconds() / 60)
        await channel.send(
            f"😅 <@{user_id}>, you arrived **{diff_minutes}** minute(s) late {source}.\n"
            f"**Late Arrivals:** {user.late_count} | **On-Time Arrivals:** {user.on_time_score}"
        )