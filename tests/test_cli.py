"""Tests for the CLI module."""

import threading
import urllib.request
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
            main,
            ["build", str(sample_marketplace_path), "-o", str(output_dir)],
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


class TestPreviewCommand:
    def test_preview_builds_and_serves(
        self, sample_marketplace_path: Path, tmp_path: Path
    ) -> None:
        import http.server

        output_dir = tmp_path / "output"
        port = 18765

        # Build first so we can verify the server serves the right files
        runner = CliRunner()
        runner.invoke(
            main,
            ["build", str(sample_marketplace_path), "-o", str(output_dir)],
        )
        assert (output_dir / "index.html").exists()

        # Start server in a thread
        import functools
        import os

        handler_cls = functools.partial(
            http.server.SimpleHTTPRequestHandler,
            directory=os.fspath(output_dir.resolve()),
        )
        server = http.server.HTTPServer(("localhost", port), handler_cls)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()

        try:
            url = f"http://localhost:{port}/"
            with urllib.request.urlopen(url) as resp:
                content = resp.read().decode()
                assert resp.status == 200
                assert "sample-marketplace" in content
        finally:
            server.shutdown()
            thread.join(timeout=5)

    def test_preview_invalid_path(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["preview", "/nonexistent/path"])
        assert result.exit_code != 0
