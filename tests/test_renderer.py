"""Tests for the renderer module."""

from pathlib import Path

from cc_plugin_catalog.models import (
    Author,
    Marketplace,
    Owner,
    Plugin,
    PluginComponents,
    SkillInfo,
)
from cc_plugin_catalog.renderer import (
    copy_static,
    render_category_page,
    render_index,
    render_plugin_page,
)


def _make_marketplace() -> Marketplace:
    return Marketplace(
        name="test-marketplace",
        description="A test marketplace",
        owner=Owner(name="Tester"),
        plugins=[
            Plugin(
                name="plugin-a",
                description="Plugin A",
                version="1.0.0",
                author=Author(name="Author A"),
                category="dev",
                tags=["tool", "ci"],
                components=PluginComponents(
                    skills=[SkillInfo(name="review", description="Review code")],
                ),
            ),
            Plugin(
                name="plugin-b",
                description="Plugin B",
                category="dev",
                tags=["tool"],
            ),
        ],
    )


class TestRenderIndex:
    def test_creates_index_html(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path)
        index_file = tmp_path / "index.html"
        assert index_file.exists()
        content = index_file.read_text()
        assert "test-marketplace" in content
        assert "plugin-a" in content
        assert "plugin-b" in content

    def test_contains_badges(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path)
        content = (tmp_path / "index.html").read_text()
        assert "Skills" in content
        assert "badge-skills" in content

    def test_contains_search_input(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path)
        content = (tmp_path / "index.html").read_text()
        assert "plugin-search" in content
        assert "search-input" in content

    def test_contains_category_filter_buttons(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path)
        content = (tmp_path / "index.html").read_text()
        assert 'data-filter-type="category"' in content
        assert 'data-filter-value="dev"' in content

    def test_contains_tag_filter_buttons(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path)
        content = (tmp_path / "index.html").read_text()
        assert 'data-filter-type="tag"' in content
        assert 'data-filter-value="tool"' in content
        assert 'data-filter-value="ci"' in content

    def test_contains_tool_filter_buttons(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path)
        content = (tmp_path / "index.html").read_text()
        assert 'data-filter-type="tool"' in content
        assert 'data-filter-value="skills"' in content

    def test_cards_have_data_tools(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path)
        content = (tmp_path / "index.html").read_text()
        assert "data-tools=" in content
        assert "skills" in content

    def test_card_has_full_link(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path)
        content = (tmp_path / "index.html").read_text()
        assert "card-link" in content


class TestRenderPluginPage:
    def test_creates_plugin_page(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_plugin_page(mp.plugins[0], mp, tmp_path)
        plugin_file = tmp_path / "plugins" / "plugin-a" / "index.html"
        assert plugin_file.exists()
        content = plugin_file.read_text()
        assert "plugin-a" in content
        assert "Plugin A" in content

    def test_contains_components(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_plugin_page(mp.plugins[0], mp, tmp_path)
        content = (tmp_path / "plugins" / "plugin-a" / "index.html").read_text()
        assert "review" in content
        assert "Review code" in content

    def test_readme_rendered_as_html(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        mp.plugins[0].readme_html = "<p>Hello <strong>README</strong></p>"
        render_plugin_page(mp.plugins[0], mp, tmp_path)
        content = (tmp_path / "plugins" / "plugin-a" / "index.html").read_text()
        # Should contain raw HTML, not escaped
        assert "<strong>README</strong>" in content
        assert "&lt;strong&gt;" not in content


class TestRenderCategoryPage:
    def test_creates_category_page(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_category_page("Category", "dev", mp.plugins, mp, tmp_path)
        page = tmp_path / "categories" / "dev" / "index.html"
        assert page.exists()
        content = page.read_text()
        assert "Category: dev" in content
        assert "plugin-a" in content

    def test_creates_tag_page(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_category_page("Tag", "tool", mp.plugins, mp, tmp_path)
        page = tmp_path / "tags" / "tool" / "index.html"
        assert page.exists()
        content = page.read_text()
        assert "Tag: tool" in content


class TestCopyStatic:
    def test_copies_css_and_js(self, tmp_path: Path) -> None:
        copy_static(tmp_path)
        assert (tmp_path / "static" / "style.css").exists()
        assert (tmp_path / "static" / "theme.js").exists()
