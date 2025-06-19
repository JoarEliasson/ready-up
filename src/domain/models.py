"""
Defines the core domain models for the ReadyUp Bot.

This module contains the fundamental data structures and business rules
that govern the application's behavior, such as sessions, user ETAs,
and statistics. It is designed to be completely independent of the
presentation (Discord) and infrastructure (persistence) layers.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time, timezone
from enum import Enum

from config import settings

log = logging.getLogger(__name__)


def get_aware_now() -> datetime:
    """Return the current time as a timezone-aware datetime object."""
    # This two-step process is the most robust way to handle timezones.
    # It gets the current time in universal UTC, then converts it to the
    # configured local timezone, avoiding all naive datetime issues.
    return datetime.now(timezone.utc).astimezone(settings.timezone_info)


class UserStateError(Exception):
    """Raised when an operation is attempted on a user in an invalid state.

    Using a custom exception allows the calling code (e.g., the command handler)
    to catch specific, predictable business rule violations and provide
    clear feedback to the user.
    """

    pass


class UserStatus(Enum):
    """Represents the finite states a user can be in during a session."""

    EXPECTED = "Expected"
    ARRIVED = "Arrived"
    EXPIRED = "Expired"


@dataclass
class UserETA:
    """Represents a single user's arrival data for a session."""

    user_id: int
    user_name: str
    command_timestamp: datetime
    arrival_timestamp: datetime
    status: UserStatus = UserStatus.EXPECTED
    actual_arrival_time: datetime | None = None

    @property
    def is_late(self) -> bool:
        """Determine if the user arrived after their stated ETA."""
        if self.status != UserStatus.ARRIVED or self.actual_arrival_time is None:
            return False
        return self.actual_arrival_time > self.arrival_timestamp

    @property
    def lateness_seconds(self) -> int:
        """Calculate how many seconds late the user was. Returns 0 if on time."""
        if not self.is_late:
            return 0
        lateness = self.actual_arrival_time - self.arrival_timestamp
        return max(0, int(lateness.total_seconds()))

    def should_expire(self) -> bool:
        """Determine if this ETA has passed the configured expiration threshold."""
        if self.status != UserStatus.EXPECTED:
            return False
        expiration_threshold = timedelta(minutes=settings.ETA_EXPIRATION_MINUTES)
        return get_aware_now() > (self.arrival_timestamp + expiration_threshold)


@dataclass
class Session:
    """
    Encapsulates the state of a single group session.

    A session is an implicitly created object that holds all users who are
    currently expected to arrive. Once a user arrives or their ETA expires,
    they are removed from the session.
    """

    users: dict[int, UserETA] = field(default_factory=dict)
    start_time: datetime = field(default_factory=get_aware_now)
    last_activity_time: datetime = field(default_factory=get_aware_now)

    def _update_activity_time(self):
        """Update the session's last activity timestamp to the current time."""
        self.last_activity_time = get_aware_now()

    def set_eta(
        self,
        user_id: int,
        user_name: str,
        eta_minutes: int | None = None,
        eta_time: time | None = None,
    ) -> UserETA:
        """
        Set or update a user's ETA for the session.

        Args:
            user_id: The Discord user ID.
            user_name: The user's display name.
            eta_minutes: The ETA in minutes from now.
            eta_time: The ETA as a specific time of day.

        Returns:
            The newly created or updated UserETA object.
        """
        now = get_aware_now()

        if eta_minutes is not None:
            arrival_ts = now + timedelta(minutes=eta_minutes)
        elif eta_time is not None:
            arrival_ts = now.replace(
                hour=eta_time.hour, minute=eta_time.minute, second=0, microsecond=0
            )
            if arrival_ts < now:
                arrival_ts += timedelta(days=1)
        else:
            raise ValueError("Either eta_minutes or eta_time must be provided.")

        user_eta = UserETA(
            user_id=user_id,
            user_name=user_name,
            command_timestamp=now,
            arrival_timestamp=arrival_ts,
        )
        self.users[user_id] = user_eta
        self._update_activity_time()
        return user_eta

    def mark_arrived(self, user_id: int) -> UserETA:
        """
        Mark a user as arrived, enforcing state transition rules.

        This method is the single source of truth for the "arrival" action.
        It ensures a user can only arrive if they are currently expected.

        Args:
            user_id: The Discord user ID of the arriving user.

        Returns:
            The updated UserETA object for the user.

        Raises:
            KeyError: If the user is not found in the session.
            UserStateError: If the user has already arrived or their ETA expired.
        """
        if user_id not in self.users:
            raise KeyError(f"User {user_id} not in session.")

        user_eta_instance = self.users[user_id]

        if user_eta_instance.status != UserStatus.EXPECTED:
            raise UserStateError(
                f"User {user_id} cannot arrive; their status is '{user_eta_instance.status.value}'."
            )

        user_eta_instance.status = UserStatus.ARRIVED
        user_eta_instance.actual_arrival_time = get_aware_now()
        self._update_activity_time()

        return user_eta_instance

    def is_inactive(self) -> bool:
        """Determine if the session has been inactive for longer than the timeout."""
        inactivity_threshold = timedelta(
            hours=settings.SESSION_INACTIVITY_TIMEOUT_HOURS
        )
        return get_aware_now() > (self.last_activity_time + inactivity_threshold)


@dataclass
class UserStats:
    """Stores and calculates long-term punctuality statistics for a user."""

    user_id: int
    user_name: str
    total_sessions: int = 0
    on_time_arrivals: int = 0
    total_lateness_seconds: int = 0
    late_arrivals: int = 0
    no_shows: int = 0

    def record_arrival(self, user_eta: UserETA):
        """
        Update stats for a user who has successfully arrived.

        Args:
            user_eta: The user's completed UserETA object.
        """
        if user_eta.status != UserStatus.ARRIVED:
            return

        self.total_sessions += 1
        if user_eta.is_late:
            self.late_arrivals += 1
            self.total_lateness_seconds += user_eta.lateness_seconds
        else:
            self.on_time_arrivals += 1

    def record_no_show(self):
        """Update stats for a user who failed to arrive (no-show)."""
        self.total_sessions += 1
        self.no_shows += 1

    @property
    def on_time_percentage(self) -> float:
        """Calculate the percentage of on-time arrivals out of all attended sessions."""
        arrived_sessions = self.total_sessions - self.no_shows
        if arrived_sessions == 0:
            return 0.0
        return (self.on_time_arrivals / arrived_sessions) * 100

    @property
    def average_lateness_seconds(self) -> int:
        """Calculate the average lateness in seconds, only for sessions where the user was late."""
        if self.late_arrivals == 0:
            return 0
        return self.total_lateness_seconds // self.late_arrivals
