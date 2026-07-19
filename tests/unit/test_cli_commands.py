"""Tests for CLI command discovery, including the bank command group."""

import os
import subprocess
import sys

import pytest
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
class TestHelpWithoutConfig:
    """Help must work without a config file and must not create any files.

    Runs in a subprocess because the --help guards check sys.argv, which
    CliRunner does not simulate.
    """

    def _run(self, args, tmp_path):
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
        )

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
