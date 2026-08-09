"""Tests for CLI command discovery, including the bank command group."""

import os
import subprocess
import sys

import pytest
import requests
import requests_mock
from click.testing import CliRunner

from leggen.main import cli


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
        assert "Could not connect" in result.output

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
        assert "Internal server error" in result.output


def _run_cli_without_config(args, tmp_path, input=None):
    """Run the CLI in a subprocess with a missing config file.

    A subprocess is required because the no-config guards check sys.argv,
    which CliRunner does not simulate.
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
