# cc-plugin-catalog

Static site generator for Claude Code Plugin Marketplace repositories.

- Spec: https://code.claude.com/docs/en/plugin-marketplaces
- Official marketplace: https://github.com/anthropics/claude-plugins-official

## Stack

- Python 3.12, managed with uv
- CLI: Click
- Templates: Jinja2
- Models: Pydantic
- Markdown: python-markdown

## Commands

```bash
uv run pytest tests/ -v      # Tests
uv run ruff check src/ tests/ # Lint
uv run ruff format src/ tests/ # Format
uv run ty check src/          # Type check
```

## CI/CD

- `ci.yml`: pytest, ruff, ty
- `build-pages.yml`: Reusable workflow for marketplace repos
- `publish.yml`: PyPI publish on GitHub Release (Trusted Publisher)
