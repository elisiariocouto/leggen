"""Tests for CLI command discovery, including the bank command group."""

import os
import shutil
import subprocess
import sys

import pytest
import requests
import requests_mock
from click.testing import CliRunner

from leggen.main import cli
from leggen.utils.config import config as config_singleton
from leggen.utils.paths import path_manager
from tests.conftest import reset_config_singleton


@pytest.mark.cli
class TestCommandDiscovery:
    def test_help_lists_bank_group(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Command Groups" in result.output
        assert "bank" in result.output

    def test_bank_group_lists_subcommands(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["bank", "--help"])
        assert result.exit_code == 0
        assert "add" in result.output
        assert "delete" in result.output

    def test_bank_subcommand_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["bank", "delete", "--help"])
        assert result.exit_code == 0
        assert "SESSION_ID" in result.output

    def test_unknown_command_fails_cleanly(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["nonexistent"])
        assert result.exit_code != 0

    def test_top_level_commands_discovered(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        for command in ("balances", "server", "status", "sync", "transactions"):
            assert command in result.output


@pytest.mark.cli
class TestErrorExitCodes:
    """API failures must exit non-zero with the error on stderr
    (regression: error paths used to echo-and-return with exit code 0)."""

    @pytest.mark.parametrize(
        "command", [["status"], ["balances"], ["sync"], ["transactions"]]
    )
    def test_unreachable_server_exits_nonzero(self, command):
        runner = CliRunner()
        with requests_mock.Mocker() as m:
            m.register_uri(
                requests_mock.ANY,
                requests_mock.ANY,
                exc=requests.exceptions.ConnectionError,
            )
            result = runner.invoke(cli, command)
        assert result.exit_code == 1
        # ClickException output must land on stderr, not stdout
        assert "Could not connect" in result.stderr

    def test_http_error_exits_nonzero(self):
        runner = CliRunner()
        with requests_mock.Mocker() as m:
            m.get(
                requests_mock.ANY,
                status_code=500,
                json={"detail": "Internal server error"},
            )
            result = runner.invoke(cli, ["status"])
        assert result.exit_code == 1
        # ClickException output must land on stderr, not stdout
        assert "Internal server error" in result.stderr


@pytest.mark.cli
class TestConfigResolution:
    """Config is loaded lazily by the singleton; path flags must reach it.

    These interactions were untestable with CliRunner while config loading
    lived in an eager option callback guarded by sys.argv checks.
    """

    @pytest.fixture(autouse=True)
    def clean_singletons(self):
        original_config_dir = path_manager._config_dir
        reset_config_singleton()
        yield
        path_manager._config_dir = original_config_dir
        reset_config_singleton()

    def test_config_dir_flag_resolves_config_file(self, tmp_path, monkeypatch):
        """--config-dir <dir> must find <dir>/config.toml (regression: the
        eager --config default resolved before --config-dir applied)."""
        shutil.copy(os.environ["LEGGEN_CONFIG_FILE"], tmp_path / "config.toml")
        monkeypatch.delenv("LEGGEN_CONFIG_FILE", raising=False)

        runner = CliRunner()
        with requests_mock.Mocker() as m:
            m.register_uri(
                requests_mock.ANY,
                requests_mock.ANY,
                exc=requests.exceptions.ConnectionError,
            )
            result = runner.invoke(cli, ["--config-dir", str(tmp_path), "status"])

        # Reaching the HTTP layer proves the config in --config-dir was found
        assert "Configuration file not found" not in result.stderr
        assert "Could not connect" in result.stderr

    def test_config_flag_reaches_singleton(self, tmp_path):
        """-c <path> must be the path the singleton loads (regression: the
        server lifespan loaded a different config than the flag)."""
        flag_config = tmp_path / "other.toml"
        shutil.copy(os.environ["LEGGEN_CONFIG_FILE"], flag_config)

        runner = CliRunner()
        with requests_mock.Mocker() as m:
            m.register_uri(requests_mock.ANY, requests_mock.ANY, json=[])
            result = runner.invoke(cli, ["-c", str(flag_config), "status"])

        assert result.exit_code == 0
        # The flag wins over LEGGEN_CONFIG_FILE (still set by conftest)
        assert config_singleton._config_path == str(flag_config)

    def test_subcommand_help_never_touches_config(self, tmp_path, monkeypatch):
        """Help output must not require a config file."""
        monkeypatch.setenv("LEGGEN_CONFIG_FILE", str(tmp_path / "missing.toml"))

        runner = CliRunner()
        for args in (["bank", "--help"], ["status", "--help"]):
            result = runner.invoke(cli, args)
            assert result.exit_code == 0, args
            assert "Usage" in result.output

    def test_api_key_falls_back_to_config_file(self):
        """Without --api-key, auth.api_key from the config file is sent."""
        runner = CliRunner()
        with requests_mock.Mocker() as m:
            m.register_uri(requests_mock.ANY, requests_mock.ANY, json=[])
            result = runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        assert m.last_request.headers["X-API-Key"] == "lgn_test-api-key-for-testing"

    def test_api_key_flag_wins_and_needs_no_config(self, tmp_path, monkeypatch):
        """--api-key skips the config fallback entirely."""
        monkeypatch.setenv("LEGGEN_CONFIG_FILE", str(tmp_path / "missing.toml"))

        runner = CliRunner()
        with requests_mock.Mocker() as m:
            m.register_uri(requests_mock.ANY, requests_mock.ANY, json=[])
            result = runner.invoke(cli, ["--api-key", "lgn_flag-key", "status"])

        assert result.exit_code == 0
        assert m.last_request.headers["X-API-Key"] == "lgn_flag-key"


def _run_cli_without_config(args, tmp_path, input=None):
    """Run the CLI in a subprocess with a missing config file.

    A real process pins the full contract: exit codes, stderr wording, and
    that no files are created in the working/config directories.
    """
    env = os.environ.copy()
    env["LEGGEN_CONFIG_FILE"] = str(tmp_path / "missing.toml")
    env["LEGGEN_CONFIG_DIR"] = str(tmp_path)
    env.pop("LEGGEN_DATABASE_PATH", None)
    return subprocess.run(
        [
            sys.executable,
            "-c",
            f"import sys; sys.argv = ['leggen'] + {args!r}; "
            "from leggen.main import cli; cli()",
        ],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        input=input,
    )


@pytest.mark.cli
class TestHelpWithoutConfig:
    """Help must work without a config file and must not create any files."""

    def _run(self, args, tmp_path):
        return _run_cli_without_config(args, tmp_path)

    def test_help_without_config(self, tmp_path):
        result = self._run(["--help"], tmp_path)
        assert result.returncode == 0, result.stderr
        assert "Command Groups" in result.stdout
        assert "FileNotFoundError" not in result.stderr
        assert list(tmp_path.iterdir()) == []

    def test_bank_help_without_config(self, tmp_path):
        result = self._run(["bank", "--help"], tmp_path)
        assert result.returncode == 0, result.stderr
        assert "add" in result.stdout
        assert "delete" in result.stdout
        assert list(tmp_path.iterdir()) == []

    def test_real_command_without_config_fails_cleanly(self, tmp_path):
        result = self._run(["status"], tmp_path)
        assert result.returncode == 1
        assert "Configuration file not found" in result.stderr
        assert "Traceback" not in result.stderr


@pytest.mark.cli
class TestBootstrapCommandsWithoutConfig:
    """Commands that bootstrap a config/database must run without one."""

    def test_generate_auth_config_without_config(self, tmp_path):
        result = _run_cli_without_config(
            ["generate_auth_config"], tmp_path, input="\nsecretpw\nsecretpw\n"
        )
        assert result.returncode == 0, result.stderr
        assert "[auth]" in result.stdout
        assert "password_hash" in result.stdout

    def test_generate_sample_db_without_config(self, tmp_path):
        db_path = tmp_path / "sample.db"
        result = _run_cli_without_config(
            [
                "generate_sample_db",
                "--database",
                str(db_path),
                "--accounts",
                "1",
                "--transactions",
                "2",
                "--force",
            ],
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        assert db_path.exists()

    def test_dashed_command_name_also_skips_config(self, tmp_path):
        result = _run_cli_without_config(
            ["generate-auth-config"], tmp_path, input="\nsecretpw\nsecretpw\n"
        )
        assert result.returncode == 0, result.stderr
        assert "[auth]" in result.stdout
