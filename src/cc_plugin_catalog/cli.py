"""CLI entry point for cc-plugin-catalog."""

from __future__ import annotations

from pathlib import Path

import click

from .builder import build_site


@click.group()
@click.version_option()
def main() -> None:
    """cc-plugin-catalog: Static site generator for Claude Code Plugin Marketplaces."""


@main.command()
@click.argument("repo_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    default="_site",
    type=click.Path(path_type=Path),
    help="Output directory for generated site.",
)
def build(repo_path: Path, output: Path) -> None:
    """Build a static site from a Plugin Marketplace repository."""
    click.echo(f"Building site from {repo_path} -> {output}")
    build_site(repo_path, output)
    click.echo(f"Site generated at {output}")
