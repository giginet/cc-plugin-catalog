"""Tests for parser module."""

from pathlib import Path

from cc_plugin_catalog.parser import (
    parse_frontmatter,
    parse_marketplace,
    parse_plugin_manifest,
)


class TestParseMarketplace:
    def test_parse_valid_marketplace(self, sample_marketplace_path: Path) -> None:
        config = parse_marketplace(sample_marketplace_path)
        assert config.name == "sample-marketplace"
        assert config.owner.name == "Test Author"
        assert config.owner.email == "test@example.com"
        assert config.metadata is not None
        assert config.metadata.description == "A sample marketplace for testing"
        assert len(config.plugins) == 3

    def test_marketplace_plugin_entries(self, sample_marketplace_path: Path) -> None:
        config = parse_marketplace(sample_marketplace_path)
        full = config.plugins[0]
        assert full.name == "full-plugin"
        assert full.source == "./plugins/full-plugin"
        assert full.category == "development"
        assert full.keywords == ["testing", "example"]

        external = config.plugins[2]
        assert isinstance(external.source, dict)


class TestParsePluginManifest:
    def test_parse_full_plugin(self, full_plugin_path: Path) -> None:
        manifest = parse_plugin_manifest(full_plugin_path)
        assert manifest is not None
        assert manifest.name == "full-plugin"
        assert manifest.version == "1.2.0"
        assert manifest.author is not None
        assert manifest.author.name == "Plugin Author"
        assert manifest.author.email == "author@example.com"
        assert manifest.license == "MIT"
        assert manifest.keywords == ["testing", "example"]

    def test_parse_minimal_plugin(self, minimal_plugin_path: Path) -> None:
        manifest = parse_plugin_manifest(minimal_plugin_path)
        assert manifest is not None
        assert manifest.name == "minimal-plugin"
        assert manifest.version is None
        assert manifest.author is None

    def test_parse_nonexistent_plugin(self, tmp_path: Path) -> None:
        result = parse_plugin_manifest(tmp_path)
        assert result is None


class TestParseFrontmatter:
    def test_parse_with_frontmatter(self, full_plugin_path: Path) -> None:
        skill_path = full_plugin_path / "skills" / "code-review" / "SKILL.md"
        frontmatter, body = parse_frontmatter(skill_path)
        expected = "Review code for best practices and potential issues"
        assert frontmatter["description"] == expected
        assert frontmatter["disable-model-invocation"] is True
        assert "Review the code for:" in body

    def test_parse_without_frontmatter(self, full_plugin_path: Path) -> None:
        readme_path = full_plugin_path / "README.md"
        frontmatter, body = parse_frontmatter(readme_path)
        assert frontmatter == {}
        assert "# Full Plugin" in body

    def test_parse_frontmatter_from_string(self, tmp_path: Path) -> None:
        md_file = tmp_path / "test.md"
        md_file.write_text("---\ntitle: Hello\n---\nBody content\n")
        frontmatter, body = parse_frontmatter(md_file)
        assert frontmatter == {"title": "Hello"}
        assert body == "Body content\n"

    def test_parse_empty_frontmatter(self, tmp_path: Path) -> None:
        md_file = tmp_path / "test.md"
        md_file.write_text("---\n---\nBody only\n")
        frontmatter, body = parse_frontmatter(md_file)
        assert frontmatter == {}
        assert body == "Body only\n"
