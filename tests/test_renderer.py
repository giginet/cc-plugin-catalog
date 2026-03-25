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

    def test_install_commands(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_plugin_page(mp.plugins[0], mp, tmp_path)
        content = (tmp_path / "plugins" / "plugin-a" / "index.html").read_text()
        assert "install-section" in content
        assert "/plugin install plugin-a@test-marketplace" in content
        assert "claude plugin install plugin-a@test-marketplace" in content
        assert "install-tab" in content
        assert "copy-btn" in content

    def test_install_commands_tab_switch(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_plugin_page(mp.plugins[0], mp, tmp_path)
        content = (tmp_path / "plugins" / "plugin-a" / "index.html").read_text()
        assert 'data-tab="claude-code"' in content
        assert 'data-tab="bash"' in content
        assert 'data-panel="claude-code"' in content
        assert 'data-panel="bash"' in content

    def test_category_links_to_filtered_index(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_plugin_page(mp.plugins[0], mp, tmp_path)
        content = (tmp_path / "plugins" / "plugin-a" / "index.html").read_text()
        assert "../../index.html?category=dev" in content

    def test_tag_links_to_filtered_index(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        mp.plugins[0].tags = ["tool"]
        render_plugin_page(mp.plugins[0], mp, tmp_path)
        content = (tmp_path / "plugins" / "plugin-a" / "index.html").read_text()
        assert "../../index.html?tag=tool" in content


class TestOGP:
    def test_ogp_included_with_base_url(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path, base_url="https://example.com")
        content = (tmp_path / "index.html").read_text()
        assert "og:title" in content
        assert "og:description" in content
        assert "og:url" in content
        assert "https://example.com/" in content

    def test_ogp_excluded_without_base_url(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path)
        content = (tmp_path / "index.html").read_text()
        assert "og:title" not in content
        assert "og:url" not in content

    def test_plugin_page_ogp(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_plugin_page(
            mp.plugins[0],
            mp,
            tmp_path,
            base_url="https://example.com",
        )
        content = (tmp_path / "plugins" / "plugin-a" / "index.html").read_text()
        assert "og:title" in content
        assert "plugin-a - test-marketplace" in content
        assert "https://example.com/plugins/plugin-a/" in content

    def test_plugin_page_ogp_excluded_without_base_url(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_plugin_page(mp.plugins[0], mp, tmp_path)
        content = (tmp_path / "plugins" / "plugin-a" / "index.html").read_text()
        assert "og:title" not in content

    def test_ogp_image_with_logo(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path, base_url="https://example.com", logo="logo.png")
        content = (tmp_path / "index.html").read_text()
        assert "og:image" in content
        assert "https://example.com/static/logo.png" in content

    def test_ogp_no_image_without_logo(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path, base_url="https://example.com")
        content = (tmp_path / "index.html").read_text()
        assert "og:image" not in content


class TestLogo:
    def test_logo_in_header(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path, logo="logo.png")
        content = (tmp_path / "index.html").read_text()
        assert "header-logo" in content
        assert "static/logo.png" in content

    def test_no_logo_in_header(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_index(mp, tmp_path)
        content = (tmp_path / "index.html").read_text()
        assert "header-logo" not in content

    def test_plugin_page_logo(self, tmp_path: Path) -> None:
        mp = _make_marketplace()
        render_plugin_page(mp.plugins[0], mp, tmp_path, logo="logo.png")
        content = (tmp_path / "plugins" / "plugin-a" / "index.html").read_text()
        assert "header-logo" in content
        assert "../../static/logo.png" in content


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
