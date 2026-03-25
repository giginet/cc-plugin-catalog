"""Scan plugin directories for components (skills, commands, agents, hooks, etc.)."""

from __future__ import annotations

import json
from pathlib import Path

from cc_plugin_catalog.models import (
    AgentInfo,
    CommandInfo,
    HookEntry,
    LspServerEntry,
    McpServerEntry,
    PluginComponents,
    SkillInfo,
)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-like frontmatter from a markdown file.

    Returns a tuple of (metadata dict, body text).
    """
    if not text.startswith("---"):
        return {}, text

    lines = text.split("\n")
    end_index = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = i
            break

    if end_index is None:
        return {}, text

    metadata: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip()

    body = "\n".join(lines[end_index + 1 :]).strip()
    return metadata, body


def scan_skills(plugin_path: Path) -> list[SkillInfo]:
    """Scan skills/*/SKILL.md for skill definitions."""
    skills_dir = plugin_path / "skills"
    if not skills_dir.is_dir():
        return []

    results: list[SkillInfo] = []
    for skill_dir in sorted(skills_dir.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if skill_dir.is_dir() and skill_file.exists():
            meta, _ = _parse_frontmatter(skill_file.read_text())
            results.append(
                SkillInfo(
                    name=skill_dir.name,
                    description=meta.get("description"),
                    source_path=str(skill_file.relative_to(plugin_path)),
                )
            )
    return results


def scan_commands(plugin_path: Path) -> list[CommandInfo]:
    """Scan commands/*.md for command definitions."""
    commands_dir = plugin_path / "commands"
    if not commands_dir.is_dir():
        return []

    results: list[CommandInfo] = []
    for cmd_file in sorted(commands_dir.glob("*.md")):
        meta, _ = _parse_frontmatter(cmd_file.read_text())
        results.append(
            CommandInfo(
                name=cmd_file.stem,
                description=meta.get("description"),
                source_path=str(cmd_file.relative_to(plugin_path)),
            )
        )
    return results


def scan_agents(plugin_path: Path) -> list[AgentInfo]:
    """Scan agents/*.md for agent definitions."""
    agents_dir = plugin_path / "agents"
    if not agents_dir.is_dir():
        return []

    results: list[AgentInfo] = []
    for agent_file in sorted(agents_dir.glob("*.md")):
        meta, _ = _parse_frontmatter(agent_file.read_text())
        results.append(
            AgentInfo(
                name=meta.get("name", agent_file.stem),
                description=meta.get("description"),
                model=meta.get("model"),
            )
        )
    return results


def scan_hooks(plugin_path: Path) -> list[HookEntry]:
    """Read hooks/hooks.json and extract hook entries."""
    hooks_file = plugin_path / "hooks" / "hooks.json"
    if not hooks_file.exists():
        return []

    data = json.loads(hooks_file.read_text())
    hooks_config = data.get("hooks", {})

    results: list[HookEntry] = []
    for event_name, matchers in hooks_config.items():
        for matcher_block in matchers:
            matcher = matcher_block.get("matcher")
            for hook in matcher_block.get("hooks", []):
                results.append(
                    HookEntry(
                        event_name=event_name,
                        matcher=matcher,
                        hook_type=hook.get("type", "command"),
                    )
                )
    return results


def scan_mcp_servers(plugin_path: Path) -> list[McpServerEntry]:
    """Read .mcp.json and extract MCP server entries."""
    mcp_file = plugin_path / ".mcp.json"
    if not mcp_file.exists():
        return []

    data = json.loads(mcp_file.read_text())
    servers = data.get("mcpServers", {})

    return [
        McpServerEntry(
            name=name,
            command=config.get("command", ""),
            args=config.get("args", []),
        )
        for name, config in sorted(servers.items())
    ]


def scan_lsp_servers(plugin_path: Path) -> list[LspServerEntry]:
    """Read .lsp.json and extract LSP server entries."""
    lsp_file = plugin_path / ".lsp.json"
    if not lsp_file.exists():
        return []

    data = json.loads(lsp_file.read_text())

    return [
        LspServerEntry(
            name=name,
            command=config.get("command", ""),
            extensions=config.get("extensionToLanguage", {}),
        )
        for name, config in sorted(data.items())
    ]


def read_readme(plugin_path: Path) -> str | None:
    """Read README.md if it exists."""
    readme = plugin_path / "README.md"
    if readme.exists():
        return readme.read_text()
    return None


def read_license(plugin_path: Path) -> str | None:
    """Read LICENSE if it exists."""
    license_file = plugin_path / "LICENSE"
    if license_file.exists():
        return license_file.read_text()
    return None


def scan_plugin(plugin_path: Path) -> PluginComponents:
    """Scan a plugin directory and return all discovered components."""
    return PluginComponents(
        skills=scan_skills(plugin_path),
        commands=scan_commands(plugin_path),
        agents=scan_agents(plugin_path),
        hooks=scan_hooks(plugin_path),
        mcp_servers=scan_mcp_servers(plugin_path),
        lsp_servers=scan_lsp_servers(plugin_path),
    )
