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


def render_index(marketplace: Marketplace, output_dir: Path) -> None:
    """Render the index page with plugin grid."""
    env = _create_env()
    template = env.get_template("index.html")
    html = template.render(marketplace=marketplace)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(html, encoding="utf-8")


def render_plugin_page(
    plugin: Plugin, marketplace: Marketplace, output_dir: Path
) -> None:
    """Render an individual plugin detail page."""
    env = _create_env()
    template = env.get_template("plugin.html")
    html = template.render(plugin=plugin, marketplace=marketplace)
    plugin_dir = output_dir / "plugins" / plugin.name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "index.html").write_text(html, encoding="utf-8")


def copy_static(output_dir: Path) -> None:
    """Copy static assets (CSS, JS) to the output directory."""
    static_src = TEMPLATES_DIR / "static"
    static_dst = output_dir / "static"
    if static_dst.exists():
        shutil.rmtree(static_dst)
    shutil.copytree(static_src, static_dst)


def render_site(marketplace: Marketplace, output_dir: Path) -> None:
    """Render the complete static site."""
    render_index(marketplace, output_dir)
    for plugin in marketplace.plugins:
        render_plugin_page(plugin, marketplace, output_dir)
    copy_static(output_dir)
