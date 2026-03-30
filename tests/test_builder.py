"""Tests for the builder module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from cc_plugin_catalog.builder import (
    RepositoryNotDetectedError,
    _extract_repo_id,
    _get_repo_base_url,
    _resolve_repository_id,
    build_site,
)


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

    def test_category_pages_generated(
        self, sample_marketplace_path: Path, tmp_path: Path
    ) -> None:
        build_site(sample_marketplace_path, tmp_path)
        cat_page = tmp_path / "categories" / "development" / "index.html"
        assert cat_page.exists()
        content = cat_page.read_text()
        assert "full-plugin" in content

    def test_readme_rendered_not_escaped(
        self, sample_marketplace_path: Path, tmp_path: Path
    ) -> None:
        build_site(sample_marketplace_path, tmp_path)
        content = (tmp_path / "plugins" / "full-plugin" / "index.html").read_text()
        # README should be rendered as HTML, not escaped
        assert "Full Plugin" in content
        assert "<ul>" in content
        assert "&lt;ul&gt;" not in content


class TestExtractRepoId:
    """Tests for _extract_repo_id."""

    def test_github_https_url(self) -> None:
        assert _extract_repo_id("https://github.com/owner/repo") == "owner/repo"

    def test_github_https_url_with_dot_git(self) -> None:
        assert _extract_repo_id("https://github.com/owner/repo.git") == "owner/repo"

    def test_github_https_url_with_trailing_slash(self) -> None:
        assert _extract_repo_id("https://github.com/owner/repo/") == "owner/repo"

    def test_github_enterprise_https_url_returns_none(self) -> None:
        assert _extract_repo_id("https://my-git-server.com/owner/repo") is None

    def test_ssh_url_returns_none(self) -> None:
        assert _extract_repo_id("git@github.com:owner/repo") is None

    def test_github_enterprise_ssh_url_returns_none(self) -> None:
        assert _extract_repo_id("git@my-git-server.com:owner/repo") is None


class TestGetRepoBaseUrl:
    """Tests for _get_repo_base_url with various git remote formats."""

    def _mock_git_remote(self, url: str):
        """Helper to mock git remote get-url origin."""
        import subprocess

        result = subprocess.CompletedProcess(args=[], returncode=0, stdout=f"{url}\n")
        return patch("cc_plugin_catalog.builder.subprocess.run", return_value=result)

    def test_github_ssh_url(self, tmp_path: Path) -> None:
        with self._mock_git_remote("git@github.com:owner/repo.git"):
            assert _get_repo_base_url(tmp_path) == "https://github.com/owner/repo"

    def test_github_https_url(self, tmp_path: Path) -> None:
        with self._mock_git_remote("https://github.com/owner/repo.git"):
            assert _get_repo_base_url(tmp_path) == "https://github.com/owner/repo"

    def test_github_enterprise_ssh_url(self, tmp_path: Path) -> None:
        """GHE SSH URLs are converted to HTTPS browse URLs."""
        with self._mock_git_remote("git@my-git-server.com:owner/repo.git"):
            result = _get_repo_base_url(tmp_path)
            assert result == "https://my-git-server.com/owner/repo"

    def test_github_enterprise_https_url(self, tmp_path: Path) -> None:
        with self._mock_git_remote("https://my-git-server.com/owner/repo.git"):
            result = _get_repo_base_url(tmp_path)
            assert result == "https://my-git-server.com/owner/repo"

    def test_github_enterprise_https_url_without_dot_git(self, tmp_path: Path) -> None:
        with self._mock_git_remote("https://my-git-server.com/owner/repo"):
            result = _get_repo_base_url(tmp_path)
            assert result == "https://my-git-server.com/owner/repo"


class TestResolveRepositoryId:
    """Tests for _resolve_repository_id."""

    def test_git_remote_takes_priority_over_default_repository(self) -> None:
        """git remote auto-detect is preferred over --default-repository."""
        result = _resolve_repository_id(
            "my-org/my-repo", "https://github.com/other/repo"
        )
        assert result == "other/repo"

    def test_github_url_extracts_owner_repo(self) -> None:
        result = _resolve_repository_id(None, "https://github.com/owner/repo")
        assert result == "owner/repo"

    def test_github_enterprise_https_uses_full_url(self) -> None:
        result = _resolve_repository_id(None, "https://my-git-server.com/owner/repo")
        assert result == "https://my-git-server.com/owner/repo"

    def test_github_enterprise_https_auto_detect_over_default(self) -> None:
        """GHE auto-detect takes priority over --default-repository."""
        result = _resolve_repository_id(
            "fallback/repo",
            "https://my-git-server.com/owner/repo",
        )
        assert result == "https://my-git-server.com/owner/repo"

    def test_default_repository_used_when_no_remote(self) -> None:
        """--default-repository is used as fallback when git remote is unavailable."""
        result = _resolve_repository_id("my-org/my-marketplace", None)
        assert result == "my-org/my-marketplace"

    def test_no_remote_no_default_returns_none(self) -> None:
        assert _resolve_repository_id(None, None) is None

    def test_empty_default_repository_with_remote(self) -> None:
        result = _resolve_repository_id("", "https://github.com/owner/repo")
        assert result == "owner/repo"

    def test_empty_default_repository_no_remote_returns_none(self) -> None:
        assert _resolve_repository_id("", None) is None


class TestBuildSiteRepositoryId:
    """Tests for repository_id error handling in build_site."""

    def test_build_site_raises_error_when_no_repository(
        self, sample_marketplace_path: Path, tmp_path: Path
    ) -> None:
        """build_site raises UsageError when repository cannot be resolved."""
        with (
            patch("cc_plugin_catalog.builder._get_repo_base_url", return_value=None),
            pytest.raises(RepositoryNotDetectedError, match="Could not detect"),
        ):
            build_site(sample_marketplace_path, tmp_path)

    def test_build_site_uses_default_repository_fallback(
        self, sample_marketplace_path: Path, tmp_path: Path
    ) -> None:
        """build_site succeeds with --default-repository when no git remote."""
        with patch("cc_plugin_catalog.builder._get_repo_base_url", return_value=None):
            build_site(
                sample_marketplace_path, tmp_path, default_repository="my-org/my-repo"
            )
        assert (tmp_path / "index.html").exists()

    def test_build_site_with_github_enterprise_remote(
        self, sample_marketplace_path: Path, tmp_path: Path
    ) -> None:
        """build_site auto-detects GHE HTTPS remote as full URL."""
        with patch(
            "cc_plugin_catalog.builder._get_repo_base_url",
            return_value="https://my-git-server.com/owner/repo",
        ):
            build_site(sample_marketplace_path, tmp_path)
        content = (tmp_path / "index.html").read_text()
        assert "https://my-git-server.com/owner/repo" in content
