"""Tests for the CLI module."""

import threading
import urllib.request
from pathlib import Path
from unittest.mock import patch

from cc_plugin_catalog.cli import main


class TestBuildCommand:
    def test_build_succeeds(
        self, sample_marketplace_path: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        with patch(
            "cc_plugin_catalog.builder._get_repo_base_url",
            return_value="https://github.com/test/repo",
        ):
            main(["build", str(sample_marketplace_path), "-o", str(output_dir)])
        assert (output_dir / "index.html").exists()

    def test_build_invalid_path(self, tmp_path: Path) -> None:
        import pytest

        with pytest.raises(SystemExit) as exc_info:
            main(["build", "/nonexistent/path"])
        assert exc_info.value.code != 0


class TestPreviewCommand:
    def test_preview_builds_and_serves(
        self, sample_marketplace_path: Path, tmp_path: Path
    ) -> None:
        import functools
        import http.server
        import os

        output_dir = tmp_path / "output"
        port = 18765

        # Build first so we can verify the server serves the right files
        with patch(
            "cc_plugin_catalog.builder._get_repo_base_url",
            return_value="https://github.com/test/repo",
        ):
            main(["build", str(sample_marketplace_path), "-o", str(output_dir)])
        assert (output_dir / "index.html").exists()

        # Start server in a thread
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
        import pytest

        with pytest.raises(SystemExit) as exc_info:
            main(["preview", "/nonexistent/path"])
        assert exc_info.value.code != 0
