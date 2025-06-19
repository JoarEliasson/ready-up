"""
Contains the application's use cases and orchestrates operations.

This module acts as a bridge between the presentation layer (the bot) and
the domain layer. It contains the high-level logic for each user-facing
feature, such as recording ETAs, handling arrivals, and calculating stats.
"""

import logging
from datetime import time, timedelta
from typing import Union, List

from domain.models import Session, UserETA, UserStatus, UserStats, get_aware_now
from application.repositories import SessionRepository, StatsRepository


log = logging.getLogger(__name__)


class ReadyUpService:
    """Orchestrates all application logic for the ReadyUp bot."""

    def __init__(self, session_repo: SessionRepository, stats_repo: StatsRepository):
        """
        Initialize the service with its dependencies.

        Args:
            session_repo: The repository for session data.
            stats_repo: The repository for user statistics.
        """
        self.session_repo = session_repo
        self.stats_repo = stats_repo
        log.info("ReadyUpService initialized.")

    async def _get_or_create_user_stats(self, user_id: int, user_name: str) -> UserStats:
        """
        Fetch a user's stats, creating a new record if one doesn't exist.

        This private helper ensures that we can always operate on a stats object,
        simplifying the logic in the public methods.

        Args:
            user_id: The Discord user ID.
            user_name: The user's current display name.

        Returns:
            An existing or new UserStats object.
        """
        stats = await self.stats_repo.get_stats_for_user(user_id)
        if stats is None:
            stats = UserStats(user_id=user_id, user_name=user_name)
        stats.user_name = user_name
        return stats

    async def record_eta(self, user_id: int, user_name: str, minutes: int = None, time_str: time = None) -> UserETA:
        """
        Set a user's ETA, creating a new session if one is not active.

        Args:
            user_id: The Discord user ID.
            user_name: The user's display name.
            minutes: The ETA in minutes from now.
            time_str: The ETA as a specific time of day.

        Returns:
            The UserETA object representing the user's new ETA.
        """
        session = await self.session_repo.get_session()
        if session is None:
            session = Session()

        if minutes:
            eta = session.set_eta(user_id=user_id, user_name=user_name, eta_minutes=minutes)
        else:
            eta = session.set_eta(user_id=user_id, user_name=user_name, eta_time=time_str)

        await self.session_repo.save_session(session)
        return eta

    async def mark_as_arrived(self, user_id: int, user_name: str) -> UserETA:
        """
        Mark a user as arrived and immediately update their statistics.

        Args:
            user_id: The Discord user ID.
            user_name: The user's display name.

        Returns:
            The completed UserETA object.

        Raises:
            KeyError: If the user has not set an ETA first.
            UserStateError: If the user's status is not 'EXPECTED'.
        """
        session = await self.session_repo.get_session()
        if not session:
            raise KeyError("No active session found.")

        arrived_eta = session.mark_arrived(user_id)
        stats = await self._get_or_create_user_stats(user_id, user_name)
        stats.record_arrival(arrived_eta)
        all_stats = await self.stats_repo.get_all_stats()
        all_stats[user_id] = stats
        await self.stats_repo.save_stats(all_stats)
        del session.users[user_id]
        await self.session_repo.save_session(session)
        return arrived_eta

    async def check_for_late_users(self) -> List[UserETA]:
        """
        Find users whose ETA has passed within the last minute for notification.

        Returns:
            A list of UserETA objects for users who just became late.
        """
        session = await self.session_repo.get_session()
        if not session:
            return []

        now = get_aware_now()
        newly_late_users = []
        for user_eta in session.users.values():
            if user_eta.status == UserStatus.EXPECTED and (now - timedelta(minutes=1)) < user_eta.arrival_timestamp <= now:
                newly_late_users.append(user_eta)
        return newly_late_users

    async def check_and_expire_etas(self) -> List[UserETA]:
        """
        Check for and expire overdue ETAs, immediately updating stats.

        Returns:
            A list of UserETA objects for users whose ETAs just expired.
        """
        session = await self.session_repo.get_session()
        if not session:
            return []

        users_to_check = list(session.users.keys())
        expired_users_info = []
        stats_changed = False

        for user_id in users_to_check:
            user_eta = session.users.get(user_id)
            if not user_eta or user_eta.status != UserStatus.EXPECTED:
                continue

            if user_eta.should_expire():
                user_eta.status = UserStatus.EXPIRED
                expired_users_info.append(user_eta)
                stats = await self._get_or_create_user_stats(user_eta.user_id, user_eta.user_name)
                stats.record_no_show()
                all_stats = await self.stats_repo.get_all_stats()
                all_stats[user_id] = stats
                await self.stats_repo.save_stats(all_stats)
                stats_changed = True
                del session.users[user_id]

        if stats_changed:
            await self.session_repo.save_session(session)
        return expired_users_info

    async def archive_session_if_inactive(self) -> bool:
        """
        Clean up the session file if it's empty and has been inactive.

        Returns:
            True if the session was cleared, False otherwise.
        """
        session = await self.session_repo.get_session()
        if session and not session.users and session.is_inactive():
            log.info("Empty session is inactive, clearing session file.")
            await self.session_repo.clear_session()
            return True
        return False

    async def get_session_status(self) -> Union[Session, None]:
        """Retrieve the current state of the active session."""
        return await self.session_repo.get_session()

    async def get_user_stats(self, user_id: int) -> Union[UserStats, None]:
        """Retrieve the long-term statistics for a specific user."""
        return await self.stats_repo.get_stats_for_user(user_id)

    async def get_leaderboard(self) -> list[UserStats]:
        """Retrieve all user stats, sorted for a leaderboard display."""
        all_stats = await self.stats_repo.get_all_stats()
        return sorted(all_stats.values(), key=lambda s: (s.no_shows, -s.on_time_percentage, s.average_lateness_seconds))