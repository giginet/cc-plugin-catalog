"""CLI entry point for cc-plugin-catalog."""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import sys
from pathlib import Path

from . import __version__
from .builder import RepositoryNotDetectedError, build_site


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    """Add options shared between build and preview commands."""
    parser.add_argument(
        "repo_path",
        type=Path,
        help="Path to the Plugin Marketplace repository.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="_site",
        type=Path,
        help="Output directory for generated site.",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="Base URL for OGP meta tags (e.g. https://example.github.io/my-marketplace).",
    )
    parser.add_argument(
        "--logo",
        default="",
        help="Path to a logo image to display in the header.",
    )
    parser.add_argument(
        "--marketplace-repository",
        default="",
        help="Marketplace repo identifier for install commands (e.g. owner/repo).",
    )


def _do_build(args: argparse.Namespace) -> None:
    """Shared build logic for build and preview commands."""
    repo_path: Path = args.repo_path
    if not repo_path.exists():
        print(f"Error: path '{repo_path}' does not exist.", file=sys.stderr)
        sys.exit(2)

    output: Path = args.output
    print(f"Building site from {repo_path} -> {output}")
    logo_path = Path(args.logo) if args.logo else None
    marketplace_repository = args.marketplace_repository or None
    try:
        build_site(
            repo_path,
            output,
            base_url=args.base_url or None,
            logo=logo_path,
            marketplace_repository=marketplace_repository,
        )
    except RepositoryNotDetectedError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    print(f"Site generated at {output}")


def _cmd_build(args: argparse.Namespace) -> None:
    _do_build(args)


def _cmd_preview(args: argparse.Namespace) -> None:
    _do_build(args)

    output: Path = args.output
    host: str = args.host
    port: int = args.port

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=os.fspath(output.resolve()),
    )
    server = http.server.HTTPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    print(f"Serving at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        server.shutdown()


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="cc-plugin-catalog",
        description="Static site generator for Claude Code Plugin Marketplaces.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command")

    # build
    build_parser = subparsers.add_parser(
        "build", help="Build a static site from a Plugin Marketplace repository."
    )
    _add_common_options(build_parser)
    build_parser.set_defaults(func=_cmd_build)

    # preview
    preview_parser = subparsers.add_parser(
        "preview", help="Build and serve the site locally with live preview."
    )
    _add_common_options(preview_parser)
    preview_parser.add_argument(
        "-p", "--port", default=8000, type=int, help="Port to serve on."
    )
    preview_parser.add_argument("--host", default="localhost", help="Host to bind to.")
    preview_parser.set_defaults(func=_cmd_preview)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(2)
    args.func(args)
