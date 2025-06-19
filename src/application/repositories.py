"""
Defines the repository interfaces for data persistence.

This module specifies the contracts (interfaces) that the infrastructure
layer must implement for data storage and retrieval. Using interfaces
like Protocols allows the application and domain layers to remain completely
decoupled from the specific persistence technology (e.g., JSON files,
a database), adhering to the Dependency Inversion Principle.
"""

from typing import Protocol, runtime_checkable

from domain.models import Session, UserStats


@runtime_checkable
class SessionRepository(Protocol):
    """An interface for storing and retrieving the active session state."""

    async def get_session(self) -> Session | None:
        """Retrieve the current active session from storage."""
        ...

    async def save_session(self, session: Session) -> None:
        """Save the given session state to storage."""
        ...

    async def clear_session(self) -> None:
        """Clear the active session from storage."""
        ...


@runtime_checkable
class StatsRepository(Protocol):
    """An interface for storing and retrieving user punctuality statistics."""

    async def get_all_stats(self) -> dict[int, UserStats]:
        """Retrieve all user statistics from storage."""
        ...

    async def get_stats_for_user(self, user_id: int) -> UserStats | None:
        """Retrieve statistics for a specific user."""
        ...

    async def save_stats(self, stats: dict[int, UserStats]) -> None:
        """Save the complete dictionary of user stats to storage."""
        ...
