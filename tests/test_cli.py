"""Tests for the CLI module."""

from pathlib import Path

from click.testing import CliRunner

from cc_plugin_catalog.cli import main


class TestBuildCommand:
    def test_build_succeeds(
        self, sample_marketplace_path: Path, tmp_path: Path
    ) -> None:
        runner = CliRunner()
        output_dir = tmp_path / "output"
        result = runner.invoke(
            main, ["build", str(sample_marketplace_path), "-o", str(output_dir)]
        )
        assert result.exit_code == 0
        assert "Site generated" in result.output
        assert (output_dir / "index.html").exists()

    def test_build_invalid_path(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["build", "/nonexistent/path"])
        assert result.exit_code != 0

    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
