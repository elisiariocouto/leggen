"""Tests for configuration management."""

import pytest
from unittest.mock import patch

from leggend.config import Config


@pytest.mark.unit
class TestConfig:
    """Test configuration management."""

    def test_singleton_behavior(self):
        """Test that Config is a singleton."""
        config1 = Config()
        config2 = Config()
        assert config1 is config2

    def test_load_config_success(self, temp_config_dir):
        """Test successful configuration loading."""
        config_data = {
            "gocardless": {
                "key": "test-key",
                "secret": "test-secret",
                "url": "https://test.example.com",
            },
            "database": {"sqlite": True},
        }

        config_file = temp_config_dir / "config.toml"
        with open(config_file, "wb") as f:
            import tomli_w

            tomli_w.dump(config_data, f)

        config = Config()
        # Reset singleton state for testing
        config._config = None
        config._config_path = None

        result = config.load_config(str(config_file))

        assert result == config_data
        assert config.gocardless_config["key"] == "test-key"
        assert config.database_config["sqlite"] is True

    def test_load_config_file_not_found(self):
        """Test handling of missing configuration file."""
        config = Config()
        config._config = None  # Reset for test

        with pytest.raises(FileNotFoundError):
            config.load_config("/nonexistent/config.toml")

    def test_save_config_success(self, temp_config_dir):
        """Test successful configuration saving."""
        config_data = {"gocardless": {"key": "new-key", "secret": "new-secret"}}

        config_file = temp_config_dir / "new_config.toml"
        config = Config()
        config._config = None

        config.save_config(config_data, str(config_file))

        # Verify file was created and contains correct data
        assert config_file.exists()

        import tomllib

        with open(config_file, "rb") as f:
            saved_data = tomllib.load(f)

        assert saved_data == config_data

    def test_update_config_success(self, temp_config_dir):
        """Test updating configuration values."""
        initial_config = {
            "gocardless": {"key": "old-key"},
            "database": {"sqlite": True},
        }

        config_file = temp_config_dir / "config.toml"
        with open(config_file, "wb") as f:
            import tomli_w

            tomli_w.dump(initial_config, f)

        config = Config()
        config._config = None
        config.load_config(str(config_file))

        config.update_config("gocardless", "key", "new-key")

        assert config.gocardless_config["key"] == "new-key"

        # Verify it was saved to file
        import tomllib

        with open(config_file, "rb") as f:
            saved_data = tomllib.load(f)
        assert saved_data["gocardless"]["key"] == "new-key"

    def test_update_section_success(self, temp_config_dir):
        """Test updating entire configuration section."""
        initial_config = {"database": {"sqlite": True}}

        config_file = temp_config_dir / "config.toml"
        with open(config_file, "wb") as f:
            import tomli_w

            tomli_w.dump(initial_config, f)

        config = Config()
        config._config = None
        config.load_config(str(config_file))

        new_db_config = {"sqlite": False, "path": "./custom.db"}
        config.update_section("database", new_db_config)

        assert config.database_config == new_db_config

    def test_scheduler_config_defaults(self):
        """Test scheduler configuration with defaults."""
        config = Config()
        config._config = {}  # Empty config

        scheduler_config = config.scheduler_config

        assert scheduler_config["sync"]["enabled"] is True
        assert scheduler_config["sync"]["hour"] == 3
        assert scheduler_config["sync"]["minute"] == 0
        assert scheduler_config["sync"]["cron"] is None

    def test_scheduler_config_custom(self):
        """Test scheduler configuration with custom values."""
        custom_config = {
            "scheduler": {
                "sync": {
                    "enabled": False,
                    "hour": 6,
                    "minute": 30,
                    "cron": "0 6 * * 1-5",
                }
            }
        }

        config = Config()
        config._config = custom_config

        scheduler_config = config.scheduler_config

        assert scheduler_config["sync"]["enabled"] is False
        assert scheduler_config["sync"]["hour"] == 6
        assert scheduler_config["sync"]["minute"] == 30
        assert scheduler_config["sync"]["cron"] == "0 6 * * 1-5"

    def test_environment_variable_config_path(self):
        """Test using environment variable for config path."""
        with patch.dict(
            "os.environ", {"LEGGEN_CONFIG_FILE": "/custom/path/config.toml"}
        ):
            config = Config()
            config._config = None

            with (
                patch("builtins.open", side_effect=FileNotFoundError),
                pytest.raises(FileNotFoundError),
            ):
                config.load_config()

    def test_notifications_config(self):
        """Test notifications configuration access."""
        custom_config = {
            "notifications": {
                "discord": {"webhook": "https://discord.webhook", "enabled": True},
                "telegram": {"token": "bot-token", "chat_id": 123},
            }
        }

        config = Config()
        config._config = custom_config

        notifications = config.notifications_config
        assert notifications["discord"]["webhook"] == "https://discord.webhook"
        assert notifications["telegram"]["token"] == "bot-token"

    def test_filters_config(self):
        """Test filters configuration access."""
        custom_config = {
            "filters": {
                "case-insensitive": ["salary", "utility"],
                "case-sensitive": ["SpecificStore"],
                "amount_threshold": 100.0,
            }
        }

        config = Config()
        config._config = custom_config

        filters = config.filters_config
        assert "salary" in filters["case-insensitive"]
        assert "utility" in filters["case-insensitive"]
        assert "SpecificStore" in filters["case-sensitive"]
        assert filters["amount_threshold"] == 100.0
