"""Parsers for marketplace and plugin configuration files."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from .models import (
    Author,
    MarketplaceConfig,
    MarketplaceFormat,
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
        installation=data.get("policy", {}).get("installation"),
    )


def parse_marketplace(
    repo_path: Path, marketplace_format: MarketplaceFormat = "auto"
) -> MarketplaceConfig:
    """Read a marketplace, preferring Codex in auto mode when both exist."""
    paths = {
        "codex": repo_path / ".agents/plugins/marketplace.json",
        "claude": repo_path / ".claude-plugin/marketplace.json",
    }
    if marketplace_format == "auto":
        marketplace_format = "codex" if paths["codex"].is_file() else "claude"
    marketplace_json = paths[marketplace_format]
    if not marketplace_json.is_file():
        raise FileNotFoundError(
            "Marketplace manifest not found. Expected "
            f"{paths['codex']} or {paths['claude']} "
            f"(selected format: {marketplace_format})."
        )
    data = json.loads(marketplace_json.read_text(encoding="utf-8"))

    metadata_raw = data.get("metadata")
    metadata = None
    if metadata_raw:
        metadata = MarketplaceMetadata(
            description=metadata_raw.get("description"),
            version=metadata_raw.get("version"),
            plugin_root=metadata_raw.get("pluginRoot"),
        )

    owner_raw = data.get("owner")
    owner = (
        Owner(name=owner_raw["name"], email=owner_raw.get("email"))
        if owner_raw
        else None
    )

    plugins = [_parse_marketplace_plugin_entry(p) for p in data.get("plugins", [])]

    return MarketplaceConfig(
        name=data["name"],
        owner=owner,
        metadata=metadata,
        plugins=plugins,
        format=marketplace_format,
        display_name=data.get("interface", {}).get("displayName"),
    )


def parse_plugin_manifest(
    plugin_path: Path, marketplace_format: MarketplaceFormat = "auto"
) -> PluginManifest | None:
    """Read a portable, Codex, or Claude plugin manifest.

    Returns None if the file does not exist.
    """
    names = ["plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json"]
    if marketplace_format == "claude":
        names = [".claude-plugin/plugin.json"]
    plugin_json = next(
        (plugin_path / n for n in names if (plugin_path / n).is_file()), None
    )
    if plugin_json is None:
        return None
    data = json.loads(plugin_json.read_text(encoding="utf-8"))
    settings = data
    portable = plugin_json == plugin_path / "plugin.json"
    if portable:
        settings = data.get("extensions", {}).get("com.openai")
        if not isinstance(settings, dict):
            overlay = plugin_path / ".codex-plugin/plugin.json"
            settings = json.loads(overlay.read_text()) if overlay.is_file() else {}
    interface = settings.get("interface", {})
    return PluginManifest(
        name=data["name"],
        version=data.get("version"),
        description=data.get("description") or interface.get("shortDescription"),
        author=_parse_author(data.get("author") or interface.get("developerName")),
        homepage=data.get("homepage") or interface.get("websiteURL"),
        repository=data.get("repository"),
        license=data.get("license"),
        keywords=data.get("keywords", []),
        display_name=interface.get("displayName"),
        skills=None if portable else data.get("skills"),
        mcp_servers="./mcp.json" if portable else data.get("mcpServers"),
        apps=settings.get("apps"),
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
