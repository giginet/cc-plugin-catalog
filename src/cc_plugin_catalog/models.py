"""Data models for Claude Code Plugin Marketplace."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Author:
    name: str
    email: str | None = None
    url: str | None = None


@dataclass
class Owner:
    name: str
    email: str | None = None


@dataclass
class MarketplaceMetadata:
    description: str | None = None
    version: str | None = None
    plugin_root: str | None = None


@dataclass
class SkillInfo:
    name: str
    description: str | None = None
    source_path: str = ""
    frontmatter: dict[str, str] = field(default_factory=dict)
    body_html: str | None = None


@dataclass
class CommandInfo:
    name: str
    description: str | None = None
    source_path: str = ""
    frontmatter: dict[str, str] = field(default_factory=dict)
    body_html: str | None = None


@dataclass
class AgentInfo:
    name: str
    description: str | None = None
    model: str | None = None
    frontmatter: dict[str, str] = field(default_factory=dict)
    body_html: str | None = None


@dataclass
class HookEntry:
    event_name: str
    matcher: str | None = None
    hook_type: str = "command"


@dataclass
class McpServerEntry:
    name: str
    command: str = ""
    args: list[str] = field(default_factory=list)


@dataclass
class LspServerEntry:
    name: str
    command: str = ""
    extensions: dict[str, str] = field(default_factory=dict)


@dataclass
class PluginComponents:
    skills: list[SkillInfo] = field(default_factory=list)
    commands: list[CommandInfo] = field(default_factory=list)
    agents: list[AgentInfo] = field(default_factory=list)
    hooks: list[HookEntry] = field(default_factory=list)
    mcp_servers: list[McpServerEntry] = field(default_factory=list)
    lsp_servers: list[LspServerEntry] = field(default_factory=list)


@dataclass
class PluginManifest:
    name: str
    version: str | None = None
    description: str | None = None
    author: Author | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] = field(default_factory=list)


@dataclass
class MarketplacePluginEntry:
    name: str
    source: str | dict = ""
    description: str | None = None
    version: str | None = None
    author: Author | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] = field(default_factory=list)
    category: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class Plugin:
    name: str
    description: str | None = None
    version: str | None = None
    author: Author | None = None
    homepage: str | None = None
    repository: str | None = None
    license_id: str | None = None
    keywords: list[str] = field(default_factory=list)
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    source: str | dict = ""
    source_url: str | None = None
    components: PluginComponents = field(default_factory=PluginComponents)
    readme_html: str | None = None
    license_text: str | None = None
    is_local: bool = False


@dataclass
class MarketplaceConfig:
    name: str
    owner: Owner
    metadata: MarketplaceMetadata | None = None
    plugins: list[MarketplacePluginEntry] = field(default_factory=list)


@dataclass
class Marketplace:
    name: str
    owner: Owner
    description: str | None = None
    repository_url: str | None = None
    repository_id: str | None = None
    plugins: list[Plugin] = field(default_factory=list)
