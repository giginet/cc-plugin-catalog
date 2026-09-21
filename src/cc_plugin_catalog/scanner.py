"""Scan plugin directories for components (skills, commands, agents, hooks, etc.)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from cc_plugin_catalog.markdown_utils import render_markdown
from cc_plugin_catalog.models import (
    AgentInfo,
    AppEntry,
    CommandInfo,
    HookEntry,
    LspServerEntry,
    McpServerEntry,
    PluginComponents,
    PluginManifest,
    SkillInfo,
)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a markdown file.

    Returns a tuple of (metadata dict, body text).
    Uses PyYAML for proper parsing of multi-line values and complex YAML.
    All values are converted to strings for display purposes.
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

    yaml_text = "\n".join(lines[1:end_index])
    try:
        raw = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        raw = None

    metadata: dict[str, str] = {}
    if isinstance(raw, dict):
        for key, value in raw.items():
            if isinstance(value, list):
                metadata[str(key)] = ", ".join(str(v) for v in value)
            else:
                metadata[str(key)] = str(value) if value is not None else ""

    body = "\n".join(lines[end_index + 1 :]).strip()
    return metadata, body


def _component_path(plugin_path: Path, relative_path: str) -> Path:
    """Resolve component paths without reading files outside the plugin."""
    path = (plugin_path / relative_path).resolve()
    if not path.is_relative_to(plugin_path.resolve()):
        raise ValueError(f"Component path must stay inside the plugin: {relative_path}")
    return path


def scan_skills(
    plugin_path: Path, extra_path: str | list[str] | None = None
) -> list[SkillInfo]:
    """Scan skills/*/SKILL.md for skill definitions."""
    roots = [_component_path(plugin_path, "skills")]
    extras = [extra_path] if isinstance(extra_path, str) else extra_path or []
    roots.extend(_component_path(plugin_path, path) for path in extras)
    files: set[Path] = set()
    for root in roots:
        if root.is_file() and root.name == "SKILL.md":
            files.add(root)
        elif (root / "SKILL.md").is_file():
            files.add(root / "SKILL.md")
        elif root.is_dir():
            files.update(root.glob("*/SKILL.md"))

    results: list[SkillInfo] = []
    for skill_file in sorted(files):
        skill_file = _component_path(plugin_path, str(skill_file))
        if skill_file.is_file():
            meta, body = _parse_frontmatter(skill_file.read_text())
            results.append(
                SkillInfo(
                    name=skill_file.parent.name,
                    description=meta.get("description"),
                    source_path=str(skill_file.relative_to(plugin_path.resolve())),
                    frontmatter=meta,
                    body_html=render_markdown(body) if body else None,
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
        meta, body = _parse_frontmatter(cmd_file.read_text())
        results.append(
            CommandInfo(
                name=cmd_file.stem,
                description=meta.get("description"),
                source_path=str(cmd_file.relative_to(plugin_path)),
                frontmatter=meta,
                body_html=render_markdown(body) if body else None,
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
        meta, body = _parse_frontmatter(agent_file.read_text())
        results.append(
            AgentInfo(
                name=meta.get("name", agent_file.stem),
                description=meta.get("description"),
                model=meta.get("model"),
                frontmatter=meta,
                body_html=render_markdown(body) if body else None,
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


def scan_mcp_servers(
    plugin_path: Path, extra: str | list[str] | dict | None = None
) -> list[McpServerEntry]:
    """Read .mcp.json and extract MCP server entries."""
    servers: dict = {}
    paths = [".mcp.json"]
    if isinstance(extra, str):
        paths.append(extra)
    elif isinstance(extra, list):
        paths.extend(extra)
    for relative_path in paths:
        mcp_file = _component_path(plugin_path, relative_path)
        if mcp_file.is_file():
            data = json.loads(mcp_file.read_text())
            servers.update(data.get("mcpServers", {}))
    if isinstance(extra, dict):
        servers.update(extra.get("mcpServers", extra))

    return [
        McpServerEntry(
            name=name,
            command=config.get("command", ""),
            args=config.get("args", []),
            url=config.get("url"),
        )
        for name, config in sorted(servers.items())
    ]


def scan_apps(plugin_path: Path, extra_path: str | None = None) -> list[AppEntry]:
    """Read the app integrations declared by a Codex plugin."""
    apps_file = _component_path(plugin_path, extra_path or ".app.json")
    if not apps_file.is_file():
        return []
    data = json.loads(apps_file.read_text())
    return [
        AppEntry(name=name, id=config.get("id", ""))
        for name, config in sorted(data.get("apps", {}).items())
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


def scan_plugin(
    plugin_path: Path, manifest: PluginManifest | None = None
) -> PluginComponents:
    """Scan a plugin directory and return all discovered components."""
    return PluginComponents(
        skills=scan_skills(plugin_path, manifest.skills if manifest else None),
        commands=scan_commands(plugin_path),
        agents=scan_agents(plugin_path),
        hooks=scan_hooks(plugin_path),
        mcp_servers=scan_mcp_servers(
            plugin_path, manifest.mcp_servers if manifest else None
        ),
        lsp_servers=scan_lsp_servers(plugin_path),
        apps=scan_apps(plugin_path, manifest.apps if manifest else None),
    )
