"""Tests for data models."""

from cc_plugin_catalog.models import (
    Author,
    Marketplace,
    MarketplaceConfig,
    MarketplacePluginEntry,
    Owner,
    Plugin,
    PluginComponents,
    PluginManifest,
    SkillInfo,
)


class TestAuthor:
    def test_required_fields(self) -> None:
        author = Author(name="Test")
        assert author.name == "Test"
        assert author.email is None

    def test_all_fields(self) -> None:
        author = Author(
            name="Test", email="test@example.com", url="https://example.com"
        )
        assert author.email == "test@example.com"
        assert author.url == "https://example.com"


class TestPluginManifest:
    def test_minimal(self) -> None:
        manifest = PluginManifest(name="test-plugin")
        assert manifest.name == "test-plugin"
        assert manifest.version is None
        assert manifest.keywords == []

    def test_full(self) -> None:
        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            description="A test plugin",
            author=Author(name="Author"),
            license="MIT",
            keywords=["test"],
        )
        assert manifest.version == "1.0.0"
        assert manifest.license == "MIT"


class TestMarketplaceConfig:
    def test_parse(self) -> None:
        config = MarketplaceConfig(
            name="test-marketplace",
            owner=Owner(name="Owner"),
            plugins=[
                MarketplacePluginEntry(
                    name="plugin-a",
                    source="./plugins/plugin-a",
                    description="Plugin A",
                )
            ],
        )
        assert config.name == "test-marketplace"
        assert len(config.plugins) == 1
        assert config.plugins[0].name == "plugin-a"

    def test_source_as_dict(self) -> None:
        entry = MarketplacePluginEntry(
            name="ext",
            source={"source": "github", "repo": "owner/repo"},
        )
        assert isinstance(entry.source, dict)


class TestPlugin:
    def test_defaults(self) -> None:
        plugin = Plugin(name="test")
        assert plugin.components == PluginComponents()
        assert plugin.is_local is False
        assert plugin.readme_html is None

    def test_with_components(self) -> None:
        plugin = Plugin(
            name="test",
            components=PluginComponents(
                skills=[SkillInfo(name="skill-a", description="A skill")],
            ),
        )
        assert len(plugin.components.skills) == 1


class TestMarketplace:
    def test_minimal(self) -> None:
        mp = Marketplace(name="mp", owner=Owner(name="Owner"))
        assert mp.plugins == []
