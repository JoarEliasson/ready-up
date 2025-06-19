"""
Implements the data persistence repositories using JSON files.

This module is part of the Infrastructure Layer. It provides concrete
implementations for the repository interfaces defined in the application
layer, handling the specifics of reading from and writing to JSON files.
"""

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Union, Dict
from datetime import datetime
from enum import Enum
import asyncio

import aiofiles
from pydantic import BaseModel, ValidationError

from domain.models import Session, UserStats, UserETA, UserStatus

log = logging.getLogger(__name__)


# --- Pydantic Models for Deserialization ---
# These models act as a "schema" for the raw data read from JSON.
# Pydantic validates and parses this data, automatically
# converting ISO datetime strings into aware datetime objects.
# This is a far more reliable approach than manual parsing.


class PydanticUserETA(BaseModel):
    """A Pydantic model for validating UserETA data from JSON."""

    user_id: int
    user_name: str
    command_timestamp: datetime
    arrival_timestamp: datetime
    status: UserStatus
    actual_arrival_time: Union[datetime, None] = None


class PydanticSession(BaseModel):
    """A Pydantic model for validating Session data from JSON."""

    users: Dict[int, PydanticUserETA]
    start_time: datetime
    last_activity_time: datetime


class PydanticUserStats(BaseModel):
    """A Pydantic model for validating UserStats data from JSON."""

    user_id: int
    user_name: str
    total_sessions: int = 0
    on_time_arrivals: int = 0
    total_lateness_seconds: int = 0
    late_arrivals: int = 0
    no_shows: int = 0


class CustomJSONEncoder(json.JSONEncoder):
    """A custom JSON encoder to handle non-standard types like datetimes and enums."""

    def default(self, o):
        """Handle datetime and Enum objects during JSON serialization."""
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return o.value
        return super().default(o)


class JsonRepository:
    """A base class for JSON repositories that provides thread-safe, atomic file writes."""

    def __init__(self, file_path: Path):
        """
        Initialize the repository.

        Args:
            file_path: The path to the JSON file this repository manages.
        """
        self._file_path = file_path
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def _read_file(self) -> Union[dict, None]:
        """Read and decode the JSON file in a thread-safe manner."""
        async with self._lock:
            if not self._file_path.exists():
                return None
            try:
                async with aiofiles.open(self._file_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                    if not content:
                        return None
                    return json.loads(content)
            except (IOError, json.JSONDecodeError) as e:
                log.error(f"Error reading or decoding {self._file_path}: {e}")
                return None

    async def _write_file(self, data: dict):
        """Write data to the JSON file atomically and safely."""
        # The atomic write pattern (write to temp file, then rename) prevents
        # data corruption if the bot crashes mid-write. The asyncio lock
        # prevents race conditions between different bot tasks.
        async with self._lock:
            temp_path = self._file_path.with_suffix(f".json.tmp.{uuid.uuid4()}")
            try:
                async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(data, cls=CustomJSONEncoder, indent=2))
                os.replace(temp_path, self._file_path)
            except IOError as e:
                log.error(f"Error writing to {self._file_path}: {e}")
            finally:
                if temp_path.exists():
                    os.remove(temp_path)

    async def _clear_file(self):
        """Safely remove the data file."""
        async with self._lock:
            if self._file_path.exists():
                try:
                    os.remove(self._file_path)
                except IOError as e:
                    log.error(f"Error removing file {self._file_path}: {e}")


class JsonSessionRepository(JsonRepository):
    """A JSON file implementation of the SessionRepository interface."""

    async def get_session(self) -> Union[Session, None]:
        """Retrieve and validate the active session from its JSON file."""
        data = await self._read_file()
        if not data:
            return None
        try:
            pydantic_session = PydanticSession.model_validate(data)

            domain_users = {
                uid: UserETA(
                    user_id=p_eta.user_id,
                    user_name=p_eta.user_name,
                    command_timestamp=p_eta.command_timestamp,
                    arrival_timestamp=p_eta.arrival_timestamp,
                    status=p_eta.status,
                    actual_arrival_time=p_eta.actual_arrival_time,
                )
                for uid, p_eta in pydantic_session.users.items()
            }
            return Session(
                users=domain_users,
                start_time=pydantic_session.start_time,
                last_activity_time=pydantic_session.last_activity_time,
            )
        except ValidationError as e:
            log.error(
                f"Session data validation failed in {self._file_path}. Data might be corrupt. Error: {e}"
            )
            return None

    async def save_session(self, session: Session):
        """Serialize and save the current session state to its JSON file."""
        data = {
            "start_time": session.start_time,
            "last_activity_time": session.last_activity_time,
            "users": {uid: eta.__dict__ for uid, eta in session.users.items()},
        }
        await self._write_file(data)

    async def clear_session(self):
        """Delete the active session file."""
        await self._clear_file()


class JsonStatsRepository(JsonRepository):
    """A JSON file implementation of the StatsRepository interface."""

    async def get_all_stats(self) -> Dict[int, UserStats]:
        """Retrieve and validate all user statistics from the JSON file."""
        data = await self._read_file()
        if not data:
            return {}
        try:
            domain_stats = {}
            for uid, stats_data in data.items():
                pydantic_stat = PydanticUserStats.model_validate(stats_data)
                domain_stats[int(uid)] = UserStats(**pydantic_stat.model_dump())
            return domain_stats
        except ValidationError as e:
            log.error(f"User stats validation failed in {self._file_path}. Error: {e}")
            return {}

    async def get_stats_for_user(self, user_id: int) -> Union[UserStats, None]:
        """Retrieve statistics for a single user."""
        all_stats = await self.get_all_stats()
        return all_stats.get(user_id)

    async def save_stats(self, stats: Dict[int, UserStats]):
        """Serialize and save all user statistics to the JSON file."""
        data = {uid: s.__dict__ for uid, s in stats.items()}
        await self._write_file(data)
