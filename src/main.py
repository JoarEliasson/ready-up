"""
The main entry point for the ReadyUp Discord Bot application.

This script is responsible for setting up logging, initializing all layers
of the application (repositories, services, and the bot client), and
running the bot.
"""

import asyncio
import logging
import discord

from bot.bot import ReadyUpBot
from application.services import ReadyUpService
from infrastructure.persistence import JsonSessionRepository, JsonStatsRepository
from config import settings

# Logging configuration for clear, structured output.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


async def main():
    """Initialize all application components and start the bot."""
    log.info("--- Starting ReadyUp Bot ---")

    # --- Dependency Injection ---
    # Repository instantiation (Infrastructure Layer).
    session_repo = JsonSessionRepository(settings.data_dir_path / "active_session.json")
    stats_repo = JsonStatsRepository(settings.data_dir_path / "user_stats.json")

    # Application service, injecting the repositories as dependencies.
    readyup_service = ReadyUpService(session_repo, stats_repo)

    # Bot instance, injecting the application service.
    bot = ReadyUpBot(service=readyup_service)

    # --- Run Bot ---
    try:
        await bot.start(settings.DISCORD_TOKEN)
    except discord.LoginFailure:
        log.error("Failed to log in. Please check your DISCORD_TOKEN in the .env file.")
    except Exception as e:
        log.critical(f"An unhandled error occurred: {e}", exc_info=True)
    finally:
        log.info("--- Shutting down ReadyUp Bot ---")
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutdown initiated by user.")
