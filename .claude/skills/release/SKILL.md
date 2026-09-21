---
name: release
description: Release a new version. Bumps minor version, creates git tag, pushes, and creates GitHub Release. Use when the user says "release" or wants to publish a new version.
disable-model-invocation: true
allowed-tools: Read, Edit, Bash, Grep, Glob
---

# Release

Publish a new version of cc-plugin-catalog.

## Arguments

- If `$ARGUMENTS` specifies a version number, use that version (e.g. `/release 2.0.0`)
- If no version is specified, bump the minor version by 1 (e.g. `1.1.0` -> `1.2.0`, patch resets to 0)

## Steps

### 1. Determine the current version

Read the `version` field from `pyproject.toml`.

### 2. Determine the new version

- Use `$ARGUMENTS` if provided
- Otherwise, increment the minor version by 1 and reset patch to 0

### 3. Update version strings

Update the version in the following files:

- `pyproject.toml` — the `version` field
- `src/cc_plugin_catalog/__init__.py` — the `__version__` variable

### 4. Sync lockfile

Run `uv sync` to ensure `uv.lock` reflects the updated version.

### 5. Commit

Commit all changed files (including `uv.lock`). Commit message: `Bump version to X.Y.Z`

### 6. Create a tag

Create a git tag **without** a `v` prefix. Example: `1.2.0`

### 7. Push

Push the commit and tag to the remote:

```bash
git push origin HEAD
git push origin <tag>
```

### 8. Create a GitHub Release

Summarize the changes since the previous tag and create a GitHub Release.

```bash
# Get the previous tag
PREV_TAG=$(git tag --sort=-v:refname | head -2 | tail -1)

# Get the commit log since the previous tag
git log ${PREV_TAG}..HEAD --oneline

# Create the GitHub Release using gh CLI
gh release create <new_tag> --title "<new_tag>" --notes "<release notes>"
```

The release notes should contain a concise bulleted summary of changes since the previous version.
