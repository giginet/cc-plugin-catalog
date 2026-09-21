"""Codex marketplace parsing and end-to-end catalog generation."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_plugin_catalog.builder import (
    _build_source_url,
    _resolve_plugin_path,
    build_site,
)
from agent_plugin_catalog.cli import main
from agent_plugin_catalog.parser import parse_marketplace, parse_plugin_manifest
from agent_plugin_catalog.scanner import scan_plugin


def write_json(root: Path, name: str, data: dict) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


@pytest.fixture
def codex_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    write_json(
        repo,
        ".agents/plugins/marketplace.json",
        {
            "name": "codex-marketplace",
            "interface": {"displayName": "Team Plugins"},
            "plugins": [
                {
                    "name": "helper",
                    "source": {"source": "local", "path": "./plugins/helper"},
                    "category": "Productivity",
                    "policy": {"installation": "AVAILABLE"},
                },
                {
                    "name": "remote",
                    "source": {
                        "source": "git-subdir",
                        "url": "https://github.com/example/plugins.git",
                        "path": "plugins/remote",
                        "ref": "v1",
                    },
                    "policy": {"installation": "NOT_AVAILABLE"},
                },
            ],
        },
    )
    plugin = repo / "plugins/helper"
    write_json(
        plugin,
        ".codex-plugin/plugin.json",
        {
            "name": "helper",
            "version": "1.0.0",
            "interface": {
                "displayName": "Team Helper",
                "shortDescription": "Helpful tools",
                "developerName": "Example Team",
            },
            "skills": "./custom-skills/",
            "mcpServers": "./config/mcp.json",
            "apps": "./config/apps.json",
        },
    )
    skill = plugin / "custom-skills/greet/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: greet\ndescription: Greet the user\n---\nSay hello.")
    write_json(
        plugin,
        "config/mcp.json",
        {
            "mcpServers": {
                "remote-mcp": {"type": "http", "url": "https://example.com/mcp"}
            }
        },
    )
    write_json(
        plugin, "config/apps.json", {"apps": {"calendar": {"id": "calendar-app"}}}
    )
    (plugin / "README.md").write_text("# Helper documentation")
    return repo


def test_parse_codex_without_owner(codex_repo: Path) -> None:
    config = parse_marketplace(codex_repo)
    assert config.format == "codex"
    assert config.owner is None
    assert config.display_name == "Team Plugins"
    assert config.plugins[1].installation == "NOT_AVAILABLE"


def test_auto_prefers_codex_and_explicit_format_selects_claude(
    codex_repo: Path,
) -> None:
    write_json(
        codex_repo, ".claude-plugin/marketplace.json", {"name": "claude-marketplace"}
    )
    assert parse_marketplace(codex_repo).name == "codex-marketplace"
    assert parse_marketplace(codex_repo, "claude").name == "claude-marketplace"


def test_codex_can_read_claude_plugin(codex_repo: Path) -> None:
    plugin = codex_repo / "plugins/legacy"
    write_json(
        plugin,
        ".claude-plugin/plugin.json",
        {"name": "legacy", "description": "Legacy plugin"},
    )
    manifest = parse_plugin_manifest(plugin, "codex")
    assert manifest is not None
    assert manifest.description == "Legacy plugin"


def test_manifest_precedence(codex_repo: Path) -> None:
    plugin = codex_repo / "plugins/helper"
    write_json(
        plugin,
        ".claude-plugin/plugin.json",
        {"name": "helper", "description": "Claude description"},
    )
    codex = parse_plugin_manifest(plugin, "codex")
    claude = parse_plugin_manifest(plugin, "claude")
    assert codex is not None and codex.description == "Helpful tools"
    assert claude is not None and claude.description == "Claude description"


def test_codex_source_resolution(codex_repo: Path) -> None:
    source = {"source": "local", "path": "./plugins/helper"}
    assert _resolve_plugin_path(codex_repo, source) == codex_repo / "plugins/helper"
    assert (
        _build_source_url(source, "https://github.com/example/plugins", "main")
        == "https://github.com/example/plugins/tree/main/plugins/helper"
    )
    assert (
        _resolve_plugin_path(
            codex_repo, {"source": "git-subdir", "path": "./plugins/helper"}
        )
        is None
    )
    with pytest.raises(ValueError, match="inside the marketplace"):
        _resolve_plugin_path(codex_repo, {"source": "local", "path": "./../outside"})


def test_codex_catalog_end_to_end(codex_repo: Path, tmp_path: Path) -> None:
    output = tmp_path / "site"
    with patch(
        "agent_plugin_catalog.builder._get_repo_base_url",
        return_value="https://github.com/example/plugins",
    ):
        main(
            [
                "build",
                str(codex_repo),
                "-o",
                str(output),
                "--marketplace-format",
                "codex",
            ]
        )
    index = (output / "index.html").read_text()
    detail = (output / "plugins/helper/index.html").read_text()
    unavailable = (output / "plugins/remote/index.html").read_text()
    category = (output / "categories/Productivity/index.html").read_text()
    assert "Team Plugins" in index and "Team Helper" in index
    assert 'href="plugins/helper/index.html"' in index
    assert "Owner:" not in index
    assert "agent-plugin-catalog" in index
    assert "codex plugin marketplace add example/plugins" in detail
    assert "claude plugin" not in detail
    assert "Greet the user" in detail and "Say hello." in detail
    assert "https://example.com/mcp" in detail
    assert "calendar-app" in detail
    assert "Helper documentation" in detail
    assert "Team Helper" in category and "Apps" in category
    assert "not available for installation" in unavailable
    assert "codex plugin marketplace add" not in unavailable


def test_explicit_claude_catalog(codex_repo: Path, tmp_path: Path) -> None:
    write_json(
        codex_repo,
        ".claude-plugin/marketplace.json",
        {
            "name": "legacy",
            "plugins": [{"name": "helper", "source": "./plugins/helper"}],
        },
    )
    output = tmp_path / "claude-site"
    build_site(
        codex_repo,
        output,
        marketplace_repository="example/plugins",
        marketplace_format="claude",
    )
    detail = (output / "plugins/helper/index.html").read_text()
    assert "/plugin install helper@legacy" in detail
    assert "codex plugin marketplace add" not in detail


def test_portable_manifest_and_inline_overlay(codex_repo: Path) -> None:
    plugin = codex_repo / "plugins/helper"
    write_json(
        plugin,
        "plugin.json",
        {
            "name": "helper",
            "description": "Portable description",
            "extensions": {
                "com.openai": {"interface": {"displayName": "Portable Helper"}}
            },
        },
    )
    write_json(
        plugin,
        "mcp.json",
        {"mcpServers": {"portable": {"type": "stdio", "command": "portable-server"}}},
    )
    manifest = parse_plugin_manifest(plugin, "codex")
    assert manifest is not None
    assert manifest.description == "Portable description"
    assert manifest.display_name == "Portable Helper"
    assert manifest.skills is None
    assert manifest.apps is None  # Inline overlay replaces the compatibility overlay.
    components = scan_plugin(plugin, manifest)
    assert components.skills == []
    assert components.mcp_servers[0].command == "portable-server"


def test_portable_manifest_uses_compatibility_presentation(codex_repo: Path) -> None:
    plugin = codex_repo / "plugins/helper"
    write_json(
        plugin, "plugin.json", {"name": "helper", "description": "Portable description"}
    )
    manifest = parse_plugin_manifest(plugin, "codex")
    assert manifest is not None
    assert manifest.display_name == "Team Helper"
    assert manifest.apps == "./config/apps.json"


def test_default_and_custom_components_deduplicated(codex_repo: Path) -> None:
    plugin = codex_repo / "plugins/helper"
    (plugin / "custom-skills").rename(plugin / "skills")
    write_json(
        plugin,
        ".codex-plugin/plugin.json",
        {
            "name": "helper",
            "skills": "./skills/",
            "mcpServers": {"inline": {"command": "inline-server"}},
        },
    )
    write_json(
        plugin, ".mcp.json", {"mcpServers": {"default": {"command": "default-server"}}}
    )
    components = scan_plugin(plugin, parse_plugin_manifest(plugin))
    assert len(components.skills) == 1
    assert {server.name for server in components.mcp_servers} == {"inline", "default"}


def test_claude_component_path_arrays(codex_repo: Path) -> None:
    plugin = codex_repo / "plugins/helper"
    write_json(
        plugin,
        ".claude-plugin/plugin.json",
        {
            "name": "helper",
            "skills": ["./custom-skills"],
            "mcpServers": ["./config/mcp.json"],
        },
    )
    components = scan_plugin(plugin, parse_plugin_manifest(plugin, "claude"))
    assert components.skills[0].name == "greet"
    assert components.mcp_servers[0].name == "remote-mcp"


@pytest.mark.parametrize("field", ["skills", "mcpServers", "apps"])
def test_component_paths_stay_inside_plugin(codex_repo: Path, field: str) -> None:
    plugin = codex_repo / "plugins/helper"
    write_json(
        plugin,
        ".codex-plugin/plugin.json",
        {"name": "helper", field: "./../../outside"},
    )
    with pytest.raises(ValueError, match="inside the plugin"):
        scan_plugin(plugin, parse_plugin_manifest(plugin))


def test_cli_missing_manifest(tmp_path: Path, capsys) -> None:
    with pytest.raises(SystemExit) as error:
        main(["build", str(tmp_path)])
    assert error.value.code == 2
    assert "Marketplace manifest not found" in capsys.readouterr().err


def test_cli_renamed_version(capsys) -> None:
    with pytest.raises(SystemExit) as error:
        main(["--version"])
    assert error.value.code == 0
    assert capsys.readouterr().out.startswith("agent-plugin-catalog ")
