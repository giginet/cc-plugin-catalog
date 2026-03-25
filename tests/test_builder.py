"""Tests for the builder module."""

from pathlib import Path

from cc_plugin_catalog.builder import build_site


class TestBuildSite:
    def test_full_build(self, sample_marketplace_path: Path, tmp_path: Path) -> None:
        build_site(sample_marketplace_path, tmp_path)

        # Index page exists
        assert (tmp_path / "index.html").exists()

        # Static assets copied
        assert (tmp_path / "static" / "style.css").exists()
        assert (tmp_path / "static" / "theme.js").exists()

        # Plugin pages created for local plugins
        assert (tmp_path / "plugins" / "full-plugin" / "index.html").exists()
        assert (tmp_path / "plugins" / "minimal-plugin" / "index.html").exists()
        assert (tmp_path / "plugins" / "external-plugin" / "index.html").exists()

    def test_index_content(self, sample_marketplace_path: Path, tmp_path: Path) -> None:
        build_site(sample_marketplace_path, tmp_path)
        content = (tmp_path / "index.html").read_text()
        assert "sample-marketplace" in content
        assert "full-plugin" in content
        assert "minimal-plugin" in content
        assert "external-plugin" in content

    def test_full_plugin_components(
        self, sample_marketplace_path: Path, tmp_path: Path
    ) -> None:
        build_site(sample_marketplace_path, tmp_path)
        content = (tmp_path / "plugins" / "full-plugin" / "index.html").read_text()
        # Skills
        assert "code-review" in content
        assert "deploy" in content
        # Commands
        assert "greet" in content
        # Agents
        assert "security-reviewer" in content
        # Hooks
        assert "PostToolUse" in content
        # MCP
        assert "db-server" in content
        # LSP
        assert "python" in content
        # README rendered
        assert "Full Plugin" in content

    def test_minimal_plugin_page(
        self, sample_marketplace_path: Path, tmp_path: Path
    ) -> None:
        build_site(sample_marketplace_path, tmp_path)
        content = (tmp_path / "plugins" / "minimal-plugin" / "index.html").read_text()
        assert "minimal-plugin" in content
        # Should not have component sections
        assert "component-table" not in content

    def test_external_plugin_page(
        self, sample_marketplace_path: Path, tmp_path: Path
    ) -> None:
        build_site(sample_marketplace_path, tmp_path)
        content = (tmp_path / "plugins" / "external-plugin" / "index.html").read_text()
        assert "external-plugin" in content
        assert "An external plugin" in content
