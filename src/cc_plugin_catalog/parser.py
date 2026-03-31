"""Parsers for marketplace and plugin configuration files."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from .models import (
    Author,
    MarketplaceConfig,
    MarketplaceMetadata,
    MarketplacePluginEntry,
    Owner,
    PluginManifest,
)


def _parse_author(data: dict | str | None) -> Author | None:
    if data is None:
        return None
    if isinstance(data, str):
        return Author(name=data)
    return Author(
        name=data["name"],
        email=data.get("email"),
        url=data.get("url"),
    )


def _parse_marketplace_plugin_entry(data: dict) -> MarketplacePluginEntry:
    return MarketplacePluginEntry(
        name=data["name"],
        source=data.get("source", ""),
        description=data.get("description"),
        version=data.get("version"),
        author=_parse_author(data.get("author")),
        homepage=data.get("homepage"),
        repository=data.get("repository"),
        license=data.get("license"),
        keywords=data.get("keywords", []),
        category=data.get("category"),
        tags=data.get("tags", []),
    )


def parse_marketplace(repo_path: Path) -> MarketplaceConfig:
    """Read .claude-plugin/marketplace.json and return a validated MarketplaceConfig."""
    marketplace_json = repo_path / ".claude-plugin" / "marketplace.json"
    data = json.loads(marketplace_json.read_text(encoding="utf-8"))

    metadata_raw = data.get("metadata")
    metadata = None
    if metadata_raw:
        metadata = MarketplaceMetadata(
            description=metadata_raw.get("description"),
            version=metadata_raw.get("version"),
            plugin_root=metadata_raw.get("pluginRoot"),
        )

    owner_raw = data["owner"]
    owner = Owner(name=owner_raw["name"], email=owner_raw.get("email"))

    plugins = [_parse_marketplace_plugin_entry(p) for p in data.get("plugins", [])]

    return MarketplaceConfig(
        name=data["name"],
        owner=owner,
        metadata=metadata,
        plugins=plugins,
    )


def parse_plugin_manifest(plugin_path: Path) -> PluginManifest | None:
    """Read .claude-plugin/plugin.json from a plugin directory.

    Returns None if the file does not exist.
    """
    plugin_json = plugin_path / ".claude-plugin" / "plugin.json"
    if not plugin_json.exists():
        return None
    data = json.loads(plugin_json.read_text(encoding="utf-8"))
    return PluginManifest(
        name=data["name"],
        version=data.get("version"),
        description=data.get("description"),
        author=_parse_author(data.get("author")),
        homepage=data.get("homepage"),
        repository=data.get("repository"),
        license=data.get("license"),
        keywords=data.get("keywords", []),
    )


def parse_frontmatter(md_path: Path) -> tuple[dict, str]:
    """Extract YAML frontmatter from a markdown file.

    Returns (frontmatter_dict, body_content).
    If no frontmatter is present, returns ({}, full_content).
    """
    content = md_path.read_text(encoding="utf-8")

    if not content.startswith("---"):
        return {}, content

    # Find the closing delimiter
    end_index = content.find("---", 3)
    if end_index == -1:
        return {}, content

    frontmatter_raw = content[3:end_index].strip()
    body = content[end_index + 3 :].lstrip("\n")

    frontmatter = yaml.safe_load(frontmatter_raw) or {}
    return frontmatter, body
