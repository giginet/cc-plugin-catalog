"""Build orchestrator: parse, scan, merge, and render."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import click

from .markdown_utils import render_markdown
from .models import Marketplace, Plugin
from .parser import parse_marketplace, parse_plugin_manifest
from .renderer import render_site
from .scanner import read_license, read_readme, scan_plugin


def _resolve_plugin_path(repo_path: Path, source: str | dict) -> Path | None:
    """Resolve a plugin source to a local path, or None if external."""
    if isinstance(source, str) and source.startswith("./"):
        return repo_path / source
    return None


def _get_repo_base_url(repo_path: Path) -> str | None:
    """Get the GitHub browse URL from the git remote origin."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        url = result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    # Convert git@ or https .git URLs to browse URL
    url = re.sub(r"\.git$", "", url)
    url = re.sub(r"^git@([^:]+):", r"https://\1/", url)
    return url


def _get_default_branch(repo_path: Path) -> str:
    """Get the current branch name."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "main"


def _build_source_url(
    source: str | dict,
    repo_base_url: str | None,
    branch: str,
) -> str | None:
    """Build a browsable URL for a plugin source."""
    if isinstance(source, str) and source.startswith("./"):
        if repo_base_url:
            path = source.lstrip("./")
            return f"{repo_base_url}/tree/{branch}/{path}"
        return None

    if isinstance(source, dict):
        src_type = source.get("source", "")
        if src_type == "github":
            repo = source.get("repo", "")
            ref = source.get("ref", "")
            url = f"https://github.com/{repo}"
            if ref:
                url += f"/tree/{ref}"
            return url
        if src_type == "url":
            url = re.sub(r"\.git$", "", source.get("url", ""))
            ref = source.get("ref", "")
            if ref:
                url += f"/tree/{ref}"
            return url
        if src_type == "git-subdir":
            url = re.sub(r"\.git$", "", source.get("url", ""))
            ref = source.get("ref", branch)
            path = source.get("path", "")
            return f"{url}/tree/{ref}/{path}"

    return None


def _extract_repo_id(url: str) -> str | None:
    """Extract owner/repo from a GitHub URL."""
    m = re.match(r"https?://github\.com/([^/]+/[^/]+?)(?:\.git)?/?$", url)
    if m:
        return m.group(1)
    return None


def _resolve_repository_id(
    default_repository: str | None,
    repo_base_url: str | None,
) -> str | None:
    """Resolve the marketplace repository identifier for install commands.

    Priority:
    1. Auto-detected from git remote (owner/repo for GitHub, full URL otherwise)
    2. Explicit --default-repository fallback
    """
    if repo_base_url:
        repo_id = _extract_repo_id(repo_base_url)
        if repo_id:
            return repo_id
        return repo_base_url
    if default_repository:
        return default_repository
    return None


def build_site(
    repo_path: Path,
    output_dir: Path,
    *,
    base_url: str | None = None,
    logo: Path | None = None,
    default_repository: str | None = None,
) -> None:
    """Build the complete static site from a marketplace repository."""
    repo_path = repo_path.resolve()
    output_dir = output_dir.resolve()

    config = parse_marketplace(repo_path)
    repo_base_url = _get_repo_base_url(repo_path)
    branch = _get_default_branch(repo_path)

    plugins: list[Plugin] = []
    for entry in config.plugins:
        plugin_path = _resolve_plugin_path(repo_path, entry.source)
        is_local = plugin_path is not None and plugin_path.is_dir()

        source_url = _build_source_url(entry.source, repo_base_url, branch)

        # Start with marketplace entry metadata
        plugin = Plugin(
            name=entry.name,
            description=entry.description,
            version=entry.version,
            author=entry.author,
            homepage=entry.homepage,
            repository=entry.repository,
            license_id=entry.license,
            keywords=entry.keywords,
            category=entry.category,
            tags=entry.tags,
            source=entry.source,
            source_url=source_url,
            is_local=is_local,
        )

        if is_local and plugin_path is not None:
            # Merge with plugin.json (plugin.json takes priority)
            manifest = parse_plugin_manifest(plugin_path)
            if manifest is not None:
                plugin.description = manifest.description or plugin.description
                plugin.version = manifest.version or plugin.version
                plugin.author = manifest.author or plugin.author
                plugin.homepage = manifest.homepage or plugin.homepage
                plugin.repository = manifest.repository or plugin.repository
                plugin.license_id = manifest.license or plugin.license_id
                if manifest.keywords:
                    plugin.keywords = manifest.keywords

            # Scan components
            plugin.components = scan_plugin(plugin_path)

            # Read and render README
            readme_text = read_readme(plugin_path)
            if readme_text:
                plugin.readme_html = render_markdown(readme_text)

            # Read LICENSE
            plugin.license_text = read_license(plugin_path)

        plugins.append(plugin)

    repository_id = _resolve_repository_id(default_repository, repo_base_url)
    if repository_id is None:
        raise click.UsageError(
            "Could not detect repository identifier from git remote. "
            "Please specify --default-repository."
        )

    marketplace = Marketplace(
        name=config.name,
        description=config.metadata.description if config.metadata else None,
        owner=config.owner,
        repository_url=repo_base_url,
        repository_id=repository_id,
        plugins=plugins,
    )

    logo_filename: str | None = None
    if logo and logo.is_file():
        logo_filename = logo.name

    render_site(marketplace, output_dir, base_url=base_url, logo=logo_filename)

    # Copy logo after render_site (which overwrites static/)
    if logo_filename and logo and logo.is_file():
        shutil.copy2(logo, output_dir / "static" / logo_filename)
