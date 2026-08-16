import os
import tomllib
from pathlib import Path
from typing import Any

import tomli_w
from loguru import logger
from pydantic import ValidationError

from leggen.models.config import Config as ConfigModel
from leggen.utils.paths import path_manager


class Config:
    _instance = None
    _config = None
    _config_model = None
    _config_path = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set_config_path(self, config_path: str) -> None:
        """Record an explicit config file path (e.g. from the --config flag).

        Wins over LEGGEN_CONFIG_FILE and the path manager on the next load.
        """
        self._config_path = str(config_path)

    def load_config(self, config_path: str | None = None) -> dict[str, Any]:
        if self._config is not None:
            return self._config

        if config_path is None:
            config_path = self._config_path or os.environ.get("LEGGEN_CONFIG_FILE")
            if not config_path:
                config_path = str(path_manager.get_config_file_path())

        self._config_path = config_path

        try:
            with open(config_path, "rb") as f:
                raw_config = tomllib.load(f)

            # Validate configuration using Pydantic
            try:
                self._config_model = ConfigModel(**raw_config)
                self._config = self._config_model.model_dump(
                    by_alias=True, exclude_none=True
                )
            except ValidationError as e:
                logger.error(f"Configuration validation failed: {e}")
                raise ValueError(f"Invalid configuration: {e}") from e

        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

        return self._config

    def save_config(
        self,
        config_data: dict[str, Any] | None = None,
        config_path: str | None = None,
    ) -> None:
        """Save configuration to TOML file"""
        if config_data is None:
            config_data = self._config

        if config_path is None:
            config_path = self._config_path or os.environ.get("LEGGEN_CONFIG_FILE")
            if not config_path:
                config_path = str(path_manager.get_config_file_path())

        if config_path is None:
            raise ValueError("No config path specified")
        if config_data is None:
            raise ValueError("No config data to save")

        # Validate the configuration before saving
        try:
            validated_model = ConfigModel(**config_data)
            validated_config = validated_model.model_dump(
                by_alias=True, exclude_none=True
            )
        except ValidationError as e:
            logger.error(f"Configuration validation failed before save: {e}")
            raise ValueError(f"Invalid configuration: {e}") from e

        # Ensure directory exists
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(config_path, "wb") as f:
                tomli_w.dump(validated_config, f)

            # Update in-memory config
            self._config = validated_config
            self._config_model = validated_model
            self._config_path = config_path
            logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise

    def update_section(self, section: str, data: dict[str, Any]) -> None:
        """Update an entire configuration section"""
        if self._config is None:
            self.load_config()

        if self._config is None:
            raise RuntimeError("Failed to load config")

        self._config[section] = data
        self.save_config()

    @property
    def is_loaded(self) -> bool:
        """Whether a configuration has been loaded, without triggering a load."""
        return self._config is not None

    @property
    def config(self) -> dict[str, Any]:
        if self._config is None:
            self.load_config()
        if self._config is None:
            raise RuntimeError("Failed to load config")
        return self._config

    @property
    def enablebanking_config(self) -> dict[str, Any]:
        return self.config.get("enablebanking", {})

    @property
    def notifications_config(self) -> dict[str, Any]:
        return self.config.get("notifications", {})

    @property
    def filters_config(self) -> dict[str, Any]:
        return self.config.get("filters", {})

    @property
    def scheduler_config(self) -> dict[str, Any]:
        """Get scheduler configuration with defaults"""
        default_schedule = {
            "sync": {
                "enabled": True,
                "hour": 3,
                "minute": 0,
                "cron": None,  # Optional custom cron expression
            },
            "backup": {
                "enabled": True,
                "hour": 4,
                "minute": 0,
                "cron": None,  # Optional custom cron expression
            },
        }
        return self.config.get("scheduler", default_schedule)

    @property
    def backup_config(self) -> dict[str, Any]:
        """Get backup configuration"""
        return self.config.get("backup", {})

    @property
    def auth_config(self) -> dict[str, Any]:
        """Get authentication configuration"""
        return self.config.get("auth", {})


# Global singleton instance
config = Config()
