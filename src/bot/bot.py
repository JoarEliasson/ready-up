"""
Defines the custom Discord Bot class and its core lifecycle events.

This module encapsulates the primary bot instance, handling setup hooks
and ready events to ensure a clean and predictable startup sequence.
"""

import logging
import discord
from discord.ext import commands

from application.services import ReadyUpService
from bot.cogs.readyup_cog import ReadyUpCog
from config import settings

log = logging.getLogger(__name__)


class ReadyUpBot(commands.Bot):
    """A custom bot class that encapsulates bot-specific setup and events.

    This improves structure by separating bot lifecycle logic from the main
    application entry point in `main.py`.
    """

    def __init__(self, service: ReadyUpService):
        """
        Initialize the custom bot.

        Args:
            service: The application service that holds the bot's logic.
        """
        intents = discord.Intents.default()
        intents.members = True

        # The command_prefix is required but will not be used if only slash
        # commands are implemented.
        super().__init__(command_prefix="!", intents=intents)

        self.service = service
        self.synced = False  # A flag to prevent syncing commands more than once.

    async def setup_hook(self):
        """Perform asynchronous setup after login but before connecting.

        This special method is the ideal place to load cogs, ensuring that
        they are available before the bot is fully online.
        """
        log.info("Running setup_hook...")
        await self.add_cog(ReadyUpCog(self, self.service))
        log.info("Cogs loaded.")

    async def on_ready(self):
        """Handle events when the bot is fully connected and ready.

        This is the correct and safest place to sync application commands,
        as the bot's internal cache is guaranteed to be populated.
        """
        await self.wait_until_ready()

        if not self.synced:
            try:
                if settings.GUILD_ID:
                    # Syncing to a specific guild is instant and ideal for development.
                    guild_obj = discord.Object(id=settings.GUILD_ID)
                    self.tree.copy_global_to(guild=guild_obj)
                    await self.tree.sync(guild=guild_obj)
                    log.info(f"Commands synced to guild: {settings.GUILD_ID}")
                else:
                    # Global sync can take up to an hour to propagate.
                    await self.tree.sync()
                    log.info("Commands synced globally.")

                self.synced = True
            except discord.errors.Forbidden as e:
                log.error(
                    f"Failed to sync commands: {e}. Ensure the bot has the 'applications.commands' scope in the server."
                )
            except Exception as e:
                log.error(
                    f"An unexpected error occurred during command sync: {e}",
                    exc_info=True,
                )

        log.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        log.info("ReadyUp Bot is now online and ready.")
        log.info("------")
