import logging
from config import RULES_MESSAGE
from tasks.check_intervals import check_intervals

async def on_ready(bot):
    logging.info(RULES_MESSAGE)
    logging.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    bot.loop.create_task(check_intervals(bot))
    logging.info("Background task for scheduled notifications started.")