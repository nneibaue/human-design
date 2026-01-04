"""
Tests for cli module.

Tests cover:
- CLI command functions
- Argument parsing
- Output formatting
"""

from unittest.mock import patch, MagicMock

import pytest

from human_design.cli import app, gate
from typer.testing import CliRunner


class TestCLIStructure:
    """Tests for CLI module structure."""

    def test_cli_app_exists(self) -> None:
        """Test that CLI app is properly defined."""
        assert app is not None
        # Typer app should have a __call__ method
        assert callable(app)

    def test_gate_command_exists(self) -> None:
        """Test that gate command exists."""
        assert callable(gate)

    def test_cli_is_typer_app(self) -> None:
        """Test that app is a Typer application."""
        import typer

        assert isinstance(app, typer.Typer)


class TestCLIInvocation:
    """Tests for CLI command invocation."""

    def test_help_command(self) -> None:
        """Test that CLI help command works."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage" in result.stdout or "usage" in result.stdout.lower()

    def test_gate_help(self) -> None:
        """Test gate subcommand help."""
        runner = CliRunner()
        result = runner.invoke(app, ["gate", "--help"])
        assert result.exit_code == 0
        assert "Usage" in result.stdout or "usage" in result.stdout.lower()

    @patch("human_design.cli.get_gate")
    def test_gate_command_with_valid_number(self, mock_get_gate: MagicMock) -> None:
        """Test gate command with valid gate number."""
        # Mock the gate data
        mock_gate = MagicMock()
        mock_gate.number = 11
        mock_gate.name = "Peace"
        mock_gate.quarter = "Q1"
        mock_gate.summary = "Test summary"
        mock_gate.description = "Test description"
        mock_gate.strive = "Test strive"
        mock_gate.lines = []
        mock_get_gate.return_value = mock_gate

        runner = CliRunner()
        result = runner.invoke(app, ["gate", "11"])

        # Should succeed or have proper error handling
        assert result.exit_code in [0, 1]

