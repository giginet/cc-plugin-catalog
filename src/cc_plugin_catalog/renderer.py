"""Render Jinja2 templates to static HTML files."""

from __future__ import annotations

import shutil
from pathlib import Path

from jinja2 import Environment, PackageLoader

from .models import Marketplace, Plugin

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _create_env() -> Environment:
    return Environment(
        loader=PackageLoader("cc_plugin_catalog", "templates"),
        autoescape=True,
    )


def _collect_categories(plugins: list[Plugin]) -> list[str]:
    cats: set[str] = set()
    for p in plugins:
        if p.category:
            cats.add(p.category)
    return sorted(cats)


def _collect_tags(plugins: list[Plugin]) -> list[str]:
    tags: set[str] = set()
    for p in plugins:
        for t in p.tags:
            tags.add(t)
    return sorted(tags)


_TOOL_TYPES = [
    {"key": "skills", "label": "Skills", "css_class": "skills"},
    {"key": "commands", "label": "Commands", "css_class": "commands"},
    {"key": "agents", "label": "Agents", "css_class": "agents"},
    {"key": "hooks", "label": "Hooks", "css_class": "hooks"},
    {"key": "mcp", "label": "MCP", "css_class": "mcp"},
    {"key": "lsp", "label": "LSP", "css_class": "lsp"},
]


def _collect_tool_types(plugins: list[Plugin]) -> list[dict[str, str]]:
    present: set[str] = set()
    for p in plugins:
        c = p.components
        if c.skills:
            present.add("skills")
        if c.commands:
            present.add("commands")
        if c.agents:
            present.add("agents")
        if c.hooks:
            present.add("hooks")
        if c.mcp_servers:
            present.add("mcp")
        if c.lsp_servers:
            present.add("lsp")
    return [t for t in _TOOL_TYPES if t["key"] in present]


def render_index(
    marketplace: Marketplace,
    output_dir: Path,
    *,
    base_url: str | None = None,
    logo: str | None = None,
) -> None:
    """Render the index page with plugin grid."""
    env = _create_env()
    template = env.get_template("index.html")
    categories = _collect_categories(marketplace.plugins)
    tags = _collect_tags(marketplace.plugins)
    tool_types = _collect_tool_types(marketplace.plugins)
    html = template.render(
        marketplace=marketplace,
        categories=categories,
        tags=tags,
        tool_types=tool_types,
        base_url=base_url or "",
        logo=logo,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(html, encoding="utf-8")


def render_plugin_page(
    plugin: Plugin,
    marketplace: Marketplace,
    output_dir: Path,
    *,
    base_url: str | None = None,
    logo: str | None = None,
) -> None:
    """Render an individual plugin detail page."""
    env = _create_env()
    template = env.get_template("plugin.html")
    page_url = f"{base_url}/plugins/{plugin.name}/" if base_url else ""
    html = template.render(
        plugin=plugin,
        marketplace=marketplace,
        base_url=base_url or "",
        page_url=page_url,
        logo=logo,
    )
    plugin_dir = output_dir / "plugins" / plugin.name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "index.html").write_text(html, encoding="utf-8")


def render_category_page(
    label_type: str,
    label_value: str,
    plugins: list[Plugin],
    marketplace: Marketplace,
    output_dir: Path,
) -> None:
    """Render a category or tag listing page."""
    env = _create_env()
    template = env.get_template("category.html")
    html = template.render(
        label_type=label_type,
        label_value=label_value,
        plugins=plugins,
        marketplace=marketplace,
    )
    prefix = "categories" if label_type == "Category" else "tags"
    page_dir = output_dir / prefix / label_value
    page_dir.mkdir(parents=True, exist_ok=True)
    (page_dir / "index.html").write_text(html, encoding="utf-8")


def copy_static(output_dir: Path) -> None:
    """Copy static assets (CSS, JS) to the output directory."""
    static_src = TEMPLATES_DIR / "static"
    static_dst = output_dir / "static"
    if static_dst.exists():
        shutil.rmtree(static_dst)
    shutil.copytree(static_src, static_dst)


def render_site(
    marketplace: Marketplace,
    output_dir: Path,
    *,
    base_url: str | None = None,
    logo: str | None = None,
) -> None:
    """Render the complete static site."""
    render_index(marketplace, output_dir, base_url=base_url, logo=logo)
    for plugin in marketplace.plugins:
        render_plugin_page(
            plugin, marketplace, output_dir, base_url=base_url, logo=logo
        )

    # Category pages
    cat_map: dict[str, list[Plugin]] = {}
    tag_map: dict[str, list[Plugin]] = {}
    for plugin in marketplace.plugins:
        if plugin.category:
            cat_map.setdefault(plugin.category, []).append(plugin)
        for tag in plugin.tags:
            tag_map.setdefault(tag, []).append(plugin)

    for cat, plugins in sorted(cat_map.items()):
        render_category_page("Category", cat, plugins, marketplace, output_dir)
    for tag, plugins in sorted(tag_map.items()):
        render_category_page("Tag", tag, plugins, marketplace, output_dir)

    copy_static(output_dir)
