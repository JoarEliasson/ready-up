"""
Handles application configuration by loading settings from environment variables.

This module uses Pydantic's BaseSettings to define, validate, and access
configuration values, providing a single, reliable source of truth for all
configurable parameters throughout the application.
"""

import logging
import sys
from pathlib import Path
from typing import Any, List, Union
from datetime import tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytz
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger(__name__)
load_dotenv()


class Settings(BaseSettings):
    """Parses and validates application settings from environment variables."""

    DISCORD_TOKEN: str
    GUILD_ID: Union[int, None] = None
    ADMIN_ROLE_IDS: List[int] = Field(default_factory=list)
    DEFAULT_TIMEZONE: str = "Europe/Stockholm"
    DATA_DIR: str = "data"
    ETA_EXPIRATION_MINUTES: int = 60
    SESSION_INACTIVITY_TIMEOUT_HOURS: int = 3

    def __init__(self, **kwargs):
        """
        Initializes the settings object and the private timezone cache.
        This explicitly creates the `_timezone_cache` attribute on the instance,
        preventing potential AttributeErrors on different platforms or versions.
        """
        super().__init__(**kwargs)
        self._timezone_cache: Union[tzinfo, None] = None

    @field_validator("ADMIN_ROLE_IDS", mode="before")
    @classmethod
    def _parse_comma_separated_ints(cls, v: Any) -> list[int]:
        """Parse a comma-separated string of IDs from an env var into a list of ints."""
        if v is None:
            return []
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                return [int(id_str.strip()) for id_str in v.split(",")]
            except (ValueError, TypeError):
                log.error(f"Could not parse ADMIN_ROLE_IDS='{v}'.")
                return []
        if isinstance(v, list):
            return v
        return []

    @property
    def data_dir_path(self) -> Path:
        """Return the data directory as a Path object, creating it if it doesn't exist."""
        path = Path(self.DATA_DIR)
        path.mkdir(exist_ok=True)
        return path

    @property
    def timezone_info(self) -> tzinfo:
        """Return a timezone object, caching the result after the first lookup."""
        if self._timezone_cache is None:
            try:
                self._timezone_cache = ZoneInfo(self.DEFAULT_TIMEZONE_STR)
            except ZoneInfoNotFoundError:
                # The 'tzdata' package is often missing on non-Linux systems.
                # In this case, ZoneInfo is expected to fail and can safely fall back.
                if "linux" not in sys.platform:
                    log.warning(
                        f"Could not find timezone '{self.DEFAULT_TIMEZONE}' using 'zoneinfo'. "
                        "This is expected on non-Linux systems. Falling back to 'pytz'."
                    )
                else:
                    log.error(
                        f"CRITICAL: Could not find timezone '{self.DEFAULT_TIMEZONE}' on Linux!"
                    )

                try:
                    self._timezone = pytz.timezone(self.DEFAULT_TIMEZONE)
                except pytz.UnknownTimeZoneError:
                    log.error(
                        f"Timezone '{self.DEFAULT_TIMEZONE}' is not valid. "
                        "Falling back to UTC. Please check your .env file."
                    )
                    self._timezone = pytz.utc
        return self._timezone

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
