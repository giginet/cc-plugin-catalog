"""Build orchestrator: parse, scan, merge, and render."""

from __future__ import annotations

from pathlib import Path

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


def build_site(repo_path: Path, output_dir: Path) -> None:
    """Build the complete static site from a marketplace repository."""
    repo_path = repo_path.resolve()
    output_dir = output_dir.resolve()

    config = parse_marketplace(repo_path)

    plugins: list[Plugin] = []
    for entry in config.plugins:
        plugin_path = _resolve_plugin_path(repo_path, entry.source)
        is_local = plugin_path is not None and plugin_path.is_dir()

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

    marketplace = Marketplace(
        name=config.name,
        description=config.metadata.description if config.metadata else None,
        owner=config.owner,
        plugins=plugins,
    )

    render_site(marketplace, output_dir)
