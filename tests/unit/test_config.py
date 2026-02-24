"""Tests for configuration management."""

from unittest.mock import patch

import pytest

from leggen.utils.config import Config


@pytest.mark.unit
class TestConfig:
    """Test configuration management."""

    def test_singleton_behavior(self):
        """Test that Config is a singleton."""
        config1 = Config()
        config2 = Config()
        assert config1 is config2

    def test_load_config_success(self, temp_config_dir, test_key_path):
        """Test successful configuration loading."""
        config_data = {
            "enablebanking": {
                "application_id": "test-app-id",
                "key_path": str(test_key_path),
                "url": "https://api.enablebanking.com",
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
        config._config_model = None

        result = config.load_config(str(config_file))

        # Result should contain validated config data
        assert result["enablebanking"]["application_id"] == "test-app-id"
        assert result["database"]["sqlite"] is True
        assert config.enablebanking_config["application_id"] == "test-app-id"
        assert config.database_config["sqlite"] is True

    def test_load_config_file_not_found(self):
        """Test handling of missing configuration file."""
        config = Config()
        config._config = None  # Reset for test

        with pytest.raises(FileNotFoundError):
            config.load_config("/nonexistent/config.toml")

    def test_save_config_success(self, temp_config_dir, test_key_path):
        """Test successful configuration saving."""
        config_data = {
            "enablebanking": {
                "application_id": "new-app-id",
                "key_path": str(test_key_path),
                "url": "https://api.enablebanking.com",
            },
            "database": {"sqlite": True},
        }

        config_file = temp_config_dir / "new_config.toml"
        config = Config()
        config._config = None
        config._config_model = None

        config.save_config(config_data, str(config_file))

        # Verify file was created and contains correct data
        assert config_file.exists()

        import tomllib

        with open(config_file, "rb") as f:
            saved_data = tomllib.load(f)

        assert saved_data["enablebanking"]["application_id"] == "new-app-id"
        assert saved_data["database"]["sqlite"] is True

    def test_update_config_success(self, temp_config_dir, test_key_path):
        """Test updating configuration values."""
        initial_config = {
            "enablebanking": {
                "application_id": "old-app-id",
                "key_path": str(test_key_path),
                "url": "https://api.enablebanking.com",
            },
            "database": {"sqlite": True},
        }

        config_file = temp_config_dir / "config.toml"
        with open(config_file, "wb") as f:
            import tomli_w

            tomli_w.dump(initial_config, f)

        config = Config()
        config._config = None
        config._config_model = None
        config.load_config(str(config_file))

        config.update_config("enablebanking", "application_id", "new-app-id")

        assert config.enablebanking_config["application_id"] == "new-app-id"

        # Verify it was saved to file
        import tomllib

        with open(config_file, "rb") as f:
            saved_data = tomllib.load(f)
        assert saved_data["enablebanking"]["application_id"] == "new-app-id"

    def test_update_section_success(self, temp_config_dir, test_key_path):
        """Test updating entire configuration section."""
        initial_config = {
            "enablebanking": {
                "application_id": "test-app-id",
                "key_path": str(test_key_path),
                "url": "https://api.enablebanking.com",
            },
            "database": {"sqlite": True},
        }

        config_file = temp_config_dir / "config.toml"
        with open(config_file, "wb") as f:
            import tomli_w

            tomli_w.dump(initial_config, f)

        config = Config()
        config._config = None
        config._config_model = None
        config.load_config(str(config_file))

        new_db_config = {"sqlite": False}
        config.update_section("database", new_db_config)

        assert config.database_config["sqlite"] is False

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
                "case_insensitive": ["salary", "utility"],
                "case_sensitive": ["SpecificStore"],
            }
        }

        config = Config()
        config._config = custom_config

        filters = config.filters_config
        assert "salary" in filters["case_insensitive"]
        assert "utility" in filters["case_insensitive"]
        assert "SpecificStore" in filters["case_sensitive"]
