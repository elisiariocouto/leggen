import os
import sys
import tomllib
from pathlib import Path
from typing import Any, Dict, Optional

import click
import tomli_w
from loguru import logger
from pydantic import ValidationError

from leggen.models.config import Config as ConfigModel
from leggen.utils import paths
from leggen.utils.text import error


class Config:
    """Configuration manager singleton.
    
    Loads and manages the application configuration from a TOML file.
    Configuration is cached after first load for performance.
    """
    _instance = None
    _config: Optional[Dict[str, Any]] = None
    _config_path: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_config_path(self, config_path: Optional[str] = None) -> str:
        """Determine the configuration file path.
        
        Priority:
        1. Provided config_path parameter
        2. LEGGEN_CONFIG_FILE environment variable
        3. Default path from paths module
        """
        if config_path is not None:
            return config_path
        
        config_path = os.environ.get("LEGGEN_CONFIG_FILE")
        if config_path:
            return config_path
            
        return str(paths.get_config_file_path())

    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from TOML file.
        
        Args:
            config_path: Optional path to configuration file.
                        Falls back to environment variable or default path.
        
        Returns:
            Validated configuration dictionary
        
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration validation fails
        """
        if self._config is not None:
            return self._config

        config_path = self._get_config_path(config_path)
        self._config_path = config_path

        try:
            with open(config_path, "rb") as f:
                raw_config = tomllib.load(f)

            # Validate configuration using Pydantic
            try:
                config_model = ConfigModel(**raw_config)
                self._config = config_model.dict(by_alias=True, exclude_none=True)
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
        config_data: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
    ) -> None:
        """Save configuration to TOML file.
        
        Args:
            config_data: Configuration data to save. Uses current config if None.
            config_path: Path to save configuration. Uses current path if None.
        
        Raises:
            ValueError: If no config data or path is available
        """
        if config_data is None:
            config_data = self._config

        if config_path is None:
            config_path = self._get_config_path(self._config_path)

        if config_path is None:
            raise ValueError("No config path specified")
        if config_data is None:
            raise ValueError("No config data to save")

        # Validate the configuration before saving
        try:
            validated_model = ConfigModel(**config_data)
            validated_config = validated_model.dict(by_alias=True, exclude_none=True)
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
            self._config_path = config_path
            logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise

    def update_config(self, section: str, key: str, value: Any) -> None:
        """Update a specific configuration value"""
        if self._config is None:
            self.load_config()

        if self._config is None:
            raise RuntimeError("Failed to load config")

        if section not in self._config:
            self._config[section] = {}

        self._config[section][key] = value
        self.save_config()

    def update_section(self, section: str, data: Dict[str, Any]) -> None:
        """Update an entire configuration section"""
        if self._config is None:
            self.load_config()

        if self._config is None:
            raise RuntimeError("Failed to load config")

        self._config[section] = data
        self.save_config()

    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration, loading it if necessary."""
        if self._config is None:
            self.load_config()
        
        if self._config is None:
            raise RuntimeError("Configuration failed to load")
        
        return self._config

    @property
    def gocardless_config(self) -> Dict[str, str]:
        """Get GoCardless configuration section."""
        return self.config.get("gocardless", {})

    @property
    def database_config(self) -> Dict[str, Any]:
        """Get database configuration section."""
        return self.config.get("database", {})

    @property
    def notifications_config(self) -> Dict[str, Any]:
        """Get notifications configuration section."""
        return self.config.get("notifications", {})

    @property
    def filters_config(self) -> Dict[str, Any]:
        """Get filters configuration section."""
        return self.config.get("filters", {})

    @property
    def scheduler_config(self) -> Dict[str, Any]:
        """Get scheduler configuration with defaults."""
        default_schedule = {
            "sync": {
                "enabled": True,
                "hour": 3,
                "minute": 0,
                "cron": None,
            }
        }
        return self.config.get("scheduler", default_schedule)

    @property
    def backup_config(self) -> Dict[str, Any]:
        """Get backup configuration section."""
        return self.config.get("backup", {})


def load_config(ctx: click.Context, _, filename):
    try:
        with click.open_file(str(filename), "rb") as f:
            raw_config = tomllib.load(f)

        # Validate configuration using Pydantic
        try:
            validated_model = ConfigModel(**raw_config)
            ctx.obj = validated_model.dict(by_alias=True, exclude_none=True)
        except ValidationError as e:
            error(f"Configuration validation failed: {e}")
            sys.exit(1)

    except FileNotFoundError:
        error(
            "Configuration file not found. Provide a valid configuration file path with leggen --config <path> or LEGGEN_CONFIG=<path> environment variable."
        )
        sys.exit(1)


# Global singleton instance
config = Config()
