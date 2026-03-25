"""Parsers for marketplace and plugin configuration files."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from .models import MarketplaceConfig, PluginManifest


def parse_marketplace(repo_path: Path) -> MarketplaceConfig:
    """Read .claude-plugin/marketplace.json and return a validated MarketplaceConfig."""
    marketplace_json = repo_path / ".claude-plugin" / "marketplace.json"
    data = json.loads(marketplace_json.read_text(encoding="utf-8"))
    return MarketplaceConfig.model_validate(data)


def parse_plugin_manifest(plugin_path: Path) -> PluginManifest | None:
    """Read .claude-plugin/plugin.json from a plugin directory.

    Returns None if the file does not exist.
    """
    plugin_json = plugin_path / ".claude-plugin" / "plugin.json"
    if not plugin_json.exists():
        return None
    data = json.loads(plugin_json.read_text(encoding="utf-8"))
    return PluginManifest.model_validate(data)


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
