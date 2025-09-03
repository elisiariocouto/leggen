import os
import tomllib
import tomli_w
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger


class Config:
    _instance = None
    _config = None
    _config_path = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_config(self, config_path: str = None) -> Dict[str, Any]:
        if self._config is not None:
            return self._config

        if config_path is None:
            config_path = os.environ.get(
                "LEGGEN_CONFIG_FILE",
                str(Path.home() / ".config" / "leggen" / "config.toml"),
            )

        self._config_path = config_path

        try:
            with open(config_path, "rb") as f:
                self._config = tomllib.load(f)
                logger.info(f"Configuration loaded from {config_path}")
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

        return self._config

    def save_config(
        self, config_data: Dict[str, Any] = None, config_path: str = None
    ) -> None:
        """Save configuration to TOML file"""
        if config_data is None:
            config_data = self._config

        if config_path is None:
            config_path = self._config_path or os.environ.get(
                "LEGGEN_CONFIG_FILE",
                str(Path.home() / ".config" / "leggen" / "config.toml"),
            )

        # Ensure directory exists
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(config_path, "wb") as f:
                tomli_w.dump(config_data, f)

            # Update in-memory config
            self._config = config_data
            self._config_path = config_path
            logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise

    def update_config(self, section: str, key: str, value: Any) -> None:
        """Update a specific configuration value"""
        if self._config is None:
            self.load_config()

        if section not in self._config:
            self._config[section] = {}

        self._config[section][key] = value
        self.save_config()

    def update_section(self, section: str, data: Dict[str, Any]) -> None:
        """Update an entire configuration section"""
        if self._config is None:
            self.load_config()

        self._config[section] = data
        self.save_config()

    @property
    def config(self) -> Dict[str, Any]:
        if self._config is None:
            self.load_config()
        return self._config

    @property
    def gocardless_config(self) -> Dict[str, str]:
        return self.config.get("gocardless", {})

    @property
    def database_config(self) -> Dict[str, Any]:
        return self.config.get("database", {})

    @property
    def notifications_config(self) -> Dict[str, Any]:
        return self.config.get("notifications", {})

    @property
    def filters_config(self) -> Dict[str, Any]:
        return self.config.get("filters", {})

    @property
    def scheduler_config(self) -> Dict[str, Any]:
        """Get scheduler configuration with defaults"""
        default_schedule = {
            "sync": {
                "enabled": True,
                "hour": 3,
                "minute": 0,
                "cron": None,  # Optional custom cron expression
            }
        }
        return self.config.get("scheduler", default_schedule)


config = Config()
