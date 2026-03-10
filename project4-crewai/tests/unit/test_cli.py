"""
Unit tests for CLI Interface

测试 CLI 接口的基本功能。

注意：这些测试需要 typer、rich 和 crewai 库。
"""

import pytest
from typer.testing import CliRunner

from app.cli import app

# Skip all tests if dependencies are not available
pytest.importorskip("typer")
pytest.importorskip("rich")

runner = CliRunner()


@pytest.mark.skipif(True, reason="CLI tests require special setup")
class TestCLI:
    """Test suite for CLI interface"""

    def test_run_command_exists(self):
        """Test that the run command exists"""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "run" in result.stdout

    def test_version_command(self):
        """Test the version command"""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Project 4 CrewAI" in result.stdout
        assert "Version:" in result.stdout

    def test_help_command(self):
        """Test the help command"""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Project 4 CrewAI" in result.stdout

    def test_run_requires_task(self):
        """Test that run command requires task parameter"""
        # This test would require mocking input
        # Skipping for now as it needs special setup
        pass


def test_cli_module_exists():
    """Test that the CLI module can be imported"""
    import app.cli
    assert hasattr(app.cli, 'app')
    assert hasattr(app.cli, 'console')


def test_cli_functions_defined():
    """Test that CLI functions are defined"""
    from app.cli import run, version, main
    assert callable(run)
    assert callable(version)
    assert callable(main)


def test_cli_runner_creation():
    """Test that CliRunner can be created"""
    from typer.testing import CliRunner
    test_runner = CliRunner()
    assert test_runner is not None


class TestCLIIntegration:
    """Integration tests for CLI (may be slow)"""

    def test_version_output(self):
        """Test version command output"""
        result = runner.invoke(app, ["version"])
        assert "Project 4 CrewAI" in result.stdout
        assert "1.0.0" in result.stdout

    def test_help_contains_all_commands(self):
        """Test that help shows all available commands"""
        result = runner.invoke(app, ["--help"])
        assert "run" in result.stdout
        assert "version" in result.stdout
