"""CLI entry point for cc-plugin-catalog."""

from __future__ import annotations

import functools
import http.server
import os
from pathlib import Path

import click

from .builder import RepositoryNotDetectedError, build_site


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
@click.option(
    "--base-url",
    default="",
    help="Base URL for OGP meta tags (e.g. https://example.github.io/my-marketplace).",
)
@click.option(
    "--logo",
    default="",
    type=click.Path(),
    help="Path to a logo image to display in the header.",
)
@click.option(
    "--marketplace-repository",
    default="",
    help="Marketplace repo identifier for install commands (e.g. owner/repo).",
)
def build(
    repo_path: Path, output: Path, base_url: str, logo: str, marketplace_repository: str
) -> None:
    """Build a static site from a Plugin Marketplace repository."""
    click.echo(f"Building site from {repo_path} -> {output}")
    logo_path = Path(logo) if logo else None
    try:
        build_site(
            repo_path,
            output,
            base_url=base_url or None,
            logo=logo_path,
            marketplace_repository=marketplace_repository or None,
        )
    except RepositoryNotDetectedError as e:
        raise click.UsageError(str(e)) from e
    click.echo(f"Site generated at {output}")


@main.command()
@click.argument("repo_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    default="_site",
    type=click.Path(path_type=Path),
    help="Output directory for generated site.",
)
@click.option(
    "-p",
    "--port",
    default=8000,
    type=int,
    help="Port to serve on.",
)
@click.option(
    "--host",
    default="localhost",
    help="Host to bind to.",
)
@click.option(
    "--base-url",
    default="",
    help="Base URL for OGP meta tags (e.g. https://example.github.io/my-marketplace).",
)
@click.option(
    "--logo",
    default="",
    type=click.Path(),
    help="Path to a logo image to display in the header.",
)
@click.option(
    "--marketplace-repository",
    default="",
    help="Marketplace repo identifier for install commands (e.g. owner/repo).",
)
def preview(
    repo_path: Path,
    output: Path,
    port: int,
    host: str,
    base_url: str,
    logo: str,
    marketplace_repository: str,
) -> None:
    """Build and serve the site locally with live preview."""
    click.echo(f"Building site from {repo_path} -> {output}")
    logo_path = Path(logo) if logo else None
    try:
        build_site(
            repo_path,
            output,
            base_url=base_url or None,
            logo=logo_path,
            marketplace_repository=marketplace_repository or None,
        )
    except RepositoryNotDetectedError as e:
        raise click.UsageError(str(e)) from e
    click.echo(f"Site generated at {output}")

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=os.fspath(output.resolve()),
    )
    server = http.server.HTTPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    click.echo(f"Serving at {url}")
    click.echo("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nStopping server.")
        server.shutdown()
