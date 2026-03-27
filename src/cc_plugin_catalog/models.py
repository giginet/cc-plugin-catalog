"""Data models for Claude Code Plugin Marketplace."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Author(BaseModel):
    name: str
    email: str | None = None
    url: str | None = None


class Owner(BaseModel):
    name: str
    email: str | None = None


class MarketplaceMetadata(BaseModel):
    description: str | None = None
    version: str | None = None
    plugin_root: str | None = Field(None, alias="pluginRoot")

    model_config = {"populate_by_name": True}


class SkillInfo(BaseModel):
    name: str
    description: str | None = None
    source_path: str = ""


class CommandInfo(BaseModel):
    name: str
    description: str | None = None
    source_path: str = ""


class AgentInfo(BaseModel):
    name: str
    description: str | None = None
    model: str | None = None


class HookEntry(BaseModel):
    event_name: str
    matcher: str | None = None
    hook_type: str = "command"


class McpServerEntry(BaseModel):
    name: str
    command: str = ""
    args: list[str] = []


class LspServerEntry(BaseModel):
    name: str
    command: str = ""
    extensions: dict[str, str] = {}


class PluginComponents(BaseModel):
    skills: list[SkillInfo] = []
    commands: list[CommandInfo] = []
    agents: list[AgentInfo] = []
    hooks: list[HookEntry] = []
    mcp_servers: list[McpServerEntry] = []
    lsp_servers: list[LspServerEntry] = []


class PluginManifest(BaseModel):
    name: str
    version: str | None = None
    description: str | None = None
    author: Author | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] = []


class MarketplacePluginEntry(BaseModel):
    name: str
    source: str | dict = ""
    description: str | None = None
    version: str | None = None
    author: Author | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] = []
    category: str | None = None
    tags: list[str] = []


class Plugin(BaseModel):
    name: str
    description: str | None = None
    version: str | None = None
    author: Author | None = None
    homepage: str | None = None
    repository: str | None = None
    license_id: str | None = None
    keywords: list[str] = []
    category: str | None = None
    tags: list[str] = []
    source: str | dict = ""
    source_url: str | None = None
    components: PluginComponents = PluginComponents()
    readme_html: str | None = None
    license_text: str | None = None
    is_local: bool = False


class MarketplaceConfig(BaseModel):
    name: str
    owner: Owner
    metadata: MarketplaceMetadata | None = None
    plugins: list[MarketplacePluginEntry] = []


class Marketplace(BaseModel):
    name: str
    description: str | None = None
    owner: Owner
    repository_url: str | None = None
    repository_id: str | None = None
    plugins: list[Plugin] = []
