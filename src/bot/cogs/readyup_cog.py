"""
Defines the bot's commands and event listeners as a Discord.py Cog.

This module acts as the Presentation Layer, handling user interactions
and translating them into calls to the Application Service Layer. It is
responsible for formatting responses and managing background tasks related
to the bot's operation.
"""

import logging
import re
from datetime import time, datetime, timedelta
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands, tasks

from application.services import ReadyUpService
from config import settings
from domain.models import UserStatus, UserStateError

log = logging.getLogger(__name__)
TIME_RE = re.compile(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$")


class ReadyUpCog(commands.Cog):
    """A Cog that encapsulates all commands and tasks for the ReadyUp bot."""

    def __init__(self, bot: commands.Bot, service: ReadyUpService):
        """
        Initialize the Cog with dependencies and start background tasks.

        Args:
            bot: The main bot instance from `commands.Bot`.
            service: The application service for handling business logic.
        """
        self.bot = bot
        self.service = service
        self.notification_channel: Union[discord.TextChannel, None] = None
        log.info("ReadyUpCog loaded.")

        self.check_lateness_task.start()
        self.expire_etas_task.start()
        self.session_archival_task.start()

    def cog_unload(self):
        """Clean up by stopping all background tasks when the cog is unloaded."""
        self.check_lateness_task.cancel()
        self.expire_etas_task.cancel()
        self.session_archival_task.cancel()
        log.info("ReadyUpCog unloaded and tasks cancelled.")

    # --- Background Tasks ---

    @tasks.loop(minutes=1.0)
    async def check_lateness_task(self):
        """Periodically check for users who have just become late and notify them."""
        try:
            newly_late_users = await self.service.check_for_late_users()
            if not newly_late_users or not self.notification_channel:
                return

            for eta in newly_late_users:
                user = self.bot.get_user(eta.user_id)
                if user:
                    await self.notification_channel.send(f"⏰ {user.mention}, your ETA of **<t:{int(eta.arrival_timestamp.timestamp())}:t>** has passed. You are now late!")
        except Exception as e:
            log.error(f"Error in check_lateness_task: {e}", exc_info=True)

    @tasks.loop(minutes=1.0)
    async def expire_etas_task(self):
        """Periodically check for ETAs that have passed the expiration threshold."""
        try:
            expired_users = await self.service.check_and_expire_etas()
            if not expired_users or not self.notification_channel:
                return

            for eta in expired_users:
                user = self.bot.get_user(eta.user_id)
                if user:
                    await self.notification_channel.send(f"⌛ {user.mention}, your ETA has expired and is now marked as a no-show.")
        except Exception as e:
            log.error(f"Error in expire_etas_task: {e}", exc_info=True)

    @tasks.loop(minutes=15.0)
    async def session_archival_task(self):
        """Periodically archive the session if it has been inactive for too long."""
        try:
            if await self.service.archive_session_if_inactive():
                if self.notification_channel:
                    await self.notification_channel.send("🧹 Session has ended due to inactivity. Ready for a new session!")
                    self.notification_channel = None
                log.info("Session successfully archived due to inactivity.")
        except Exception as e:
            log.error(f"Error in session_archival_task: {e}", exc_info=True)

    # --- Application Commands ---

    @app_commands.command(name="ping", description="Check the bot's responsiveness and latency.")
    async def ping(self, interaction: discord.Interaction):
        """Handle the /ping command."""
        latency = self.bot.latency * 1000
        await interaction.response.send_message(f"Pong! Latency: **{latency:.2f}ms**")

    @app_commands.command(name="help", description="Show information about how to use the ReadyUp bot.")
    async def help(self, interaction: discord.Interaction):
        """Handle the /help command."""
        embed = discord.Embed(
            title="ReadyUp Bot Help",
            description="I help coordinate sessions by tracking everyone's arrival time!",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.add_field(
            name="Core Commands",
            value=(
                "`/eta minutes <number>`: Set your ETA in minutes from now.\n"
                "`/eta time <HH:MM>`: Set your ETA to a specific time.\n"
                "`/arrived`: Mark yourself as ready (must have an ETA).\n"
                "`/status`: See the current session's arrival status."
            ),
            inline=False
        )
        embed.add_field(
            name="Statistics Commands",
            value=(
                "`/stats [user]`: View punctuality stats.\n"
                "`/leaderboard`: Display the server's punctuality leaderboard.\n"
                "`/ping`: Check if the bot is responsive."
            ),
            inline=False
        )
        embed.set_footer(text="ReadyUp Bot | Let's get gaming!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="eta", description="Set your estimated time of arrival.")
    @app_commands.describe(minutes="Your ETA in minutes from now.", time_str="Your ETA in HH:MM format (e.g., 21:30).")
    async def eta(self, interaction: discord.Interaction, minutes: int = None, time_str: str = None):
        """Handle the /eta command."""
        await interaction.response.defer()

        if self.notification_channel is None:
            self.notification_channel = interaction.channel
            log.info(f"Notification channel set to: #{interaction.channel.name}")

        if minutes is None and time_str is None:
            await interaction.followup.send("Please provide either `minutes` or `time_str`.", ephemeral=True)
            return

        try:
            parsed_time = None
            if time_str:
                match = TIME_RE.match(time_str)
                if not match:
                    await interaction.followup.send("Invalid time format. Please use `HH:MM` (e.g., `21:30`).", ephemeral=True)
                    return
                parsed_time = time(hour=int(match.group(1)), minute=int(match.group(2)))

            user_eta = await self.service.record_eta(
                user_id=interaction.user.id,
                user_name=interaction.user.display_name,
                minutes=minutes,
                time_str=parsed_time
            )

            msg = f"Got it, {interaction.user.mention}! ETA set for **<t:{int(user_eta.arrival_timestamp.timestamp())}:t>**."
            await interaction.followup.send(msg)
        except Exception as e:
            log.error(f"Error processing /eta command: {e}", exc_info=True)
            await interaction.followup.send("An error occurred while setting your ETA.", ephemeral=True)

    @app_commands.command(name="arrived", description="Mark yourself as arrived and ready.")
    async def arrived(self, interaction: discord.Interaction):
        """Handle the /arrived command, enforcing state rules."""
        await interaction.response.defer()
        try:
            user_eta = await self.service.mark_as_arrived(interaction.user.id, interaction.user.display_name)

            msg_parts = [f"✅ **{interaction.user.mention} has arrived!**"]
            if user_eta.is_late:
                lateness_str = str(timedelta(seconds=user_eta.lateness_seconds)).split('.')[0]
                msg_parts.append(f"*(You were {lateness_str} late.)*")
            else:
                msg_parts.append("*(You are on time!)*")
            await interaction.followup.send(" ".join(msg_parts))

        except UserStateError:
            await interaction.followup.send(f"Hey {interaction.user.mention}, you have already been marked as 'arrived' or 'expired' for this session.", ephemeral=True)
        except KeyError:
            await interaction.followup.send(f"Hey {interaction.user.mention}, you need to set an ETA with `/eta` before you can arrive!", ephemeral=True)
        except Exception as e:
            log.error(f"Error processing /arrived command: {e}", exc_info=True)
            await interaction.followup.send("An unknown error occurred.", ephemeral=True)

    @app_commands.command(name="status", description="Show the current arrival status for the session.")
    async def status(self, interaction: discord.Interaction):
        """Handle the /status command."""
        await interaction.response.defer()
        session = await self.service.get_session_status()
        if not session or not session.users:
            await interaction.followup.send("No active session. Use `/eta` to start one!")
            return

        embed = discord.Embed(
            title="Current Session Status",
            color=discord.Color.blue(),
            timestamp=datetime.now(settings.TIMEZONE)
        )
        arrived, expected, expired = [], [], []

        def sort_key(u):
            # Sort users by status, then by their ETA, for a predictable display.
            return ({UserStatus.ARRIVED: 0, UserStatus.EXPECTED: 1, UserStatus.EXPIRED: 2}.get(u.status, 99), u.arrival_timestamp)

        for u_eta in sorted(session.users.values(), key=sort_key):
            user = self.bot.get_user(u_eta.user_id) or u_eta.user_name
            mention = user.mention if hasattr(user, 'mention') else u_eta.user_name
            if u_eta.status == UserStatus.ARRIVED:
                l_str = f" (Late by {str(timedelta(seconds=u_eta.lateness_seconds)).split('.')[0]})" if u_eta.is_late else ""
                arrived.append(f"✅ {mention} (Arrived at <t:{int(u_eta.actual_arrival_time.timestamp())}:t>{l_str})")
            elif u_eta.status == UserStatus.EXPIRED:
                expired.append(f"❌ {mention} (ETA <t:{int(u_eta.arrival_timestamp.timestamp())}:t> expired)")
            else:
                expected.append(f"⏳ {mention} (ETA: <t:{int(u_eta.arrival_timestamp.timestamp())}:R>)")

        if arrived: embed.add_field(name="Arrived", value="\n".join(arrived), inline=False)
        if expected: embed.add_field(name="Expected", value="\n".join(expected), inline=False)
        if expired: embed.add_field(name="ETA Expired (No-Show)", value="\n".join(expired), inline=False)

        embed.set_footer(text=f"Session started <t:{int(session.start_time.timestamp())}:R>")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="stats", description="Show punctuality statistics for a user.")
    @app_commands.describe(user="The user to get stats for (defaults to yourself).")
    async def stats(self, interaction: discord.Interaction, user: discord.Member = None):
        """Handle the /stats command."""
        await interaction.response.defer(ephemeral=True)
        target_user = user or interaction.user
        stats_data = await self.service.get_user_stats(target_user.id)
        if not stats_data:
            await interaction.followup.send(f"{target_user.mention} has no recorded stats yet.", ephemeral=True)
            return

        embed = discord.Embed(title=f"Punctuality Stats for {stats_data.user_name}", color=discord.Color.green())
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.add_field(name="Sessions", value=str(stats_data.total_sessions), inline=True)
        embed.add_field(name="On-Time %", value=f"{stats_data.on_time_percentage:.2f}%", inline=True)
        embed.add_field(name="No-Shows", value=str(stats_data.no_shows), inline=True)
        avg_lateness = timedelta(seconds=stats_data.average_lateness_seconds)
        embed.add_field(name="Total Late Arrivals", value=str(stats_data.late_arrivals), inline=False)
        embed.add_field(name="Avg. Lateness (when late)", value=str(avg_lateness).split('.')[0], inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="leaderboard", description="Display the server-wide punctuality leaderboard.")
    async def leaderboard(self, interaction: discord.Interaction):
        """Handle the /leaderboard command."""
        await interaction.response.defer()
        leaderboard_stats = await self.service.get_leaderboard()
        if not leaderboard_stats:
            await interaction.followup.send("No stats have been recorded yet to generate a leaderboard.")
            return

        embed = discord.Embed(title="Punctuality Leaderboard", description="Ranked by no-shows, then on-time percentage.", color=discord.Color.gold())
        board_text = []
        for i, s in enumerate(leaderboard_stats[:10]):
            rank_emoji = {0: "🥇", 1: "🥈", 2: "🥉"}.get(i, f"**#{i+1}**")
            user = self.bot.get_user(s.user_id) or s.user_name
            mention = user.mention if hasattr(user, 'mention') else s.user_name
            board_text.append(f"{rank_emoji} {mention} - **{s.on_time_percentage:.1f}%** on-time | **{s.no_shows}** no-shows")

        embed.description = "\n".join(board_text) if board_text else "Not enough data for a leaderboard."
        await interaction.followup.send(embed=embed)