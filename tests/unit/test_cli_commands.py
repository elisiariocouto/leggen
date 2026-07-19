"""Tests for CLI command discovery, including the bank command group."""

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
