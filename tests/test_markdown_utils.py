from cc_plugin_catalog.markdown_utils import render_markdown


class TestRenderMarkdown:
    def test_heading_h1(self):
        result = render_markdown("# Hello")
        assert "<h1" in result
        assert "Hello</h1>" in result

    def test_heading_h2(self):
        result = render_markdown("## World")
        assert "<h2" in result
        assert "World</h2>" in result

    def test_bold(self):
        result = render_markdown("**bold**")
        assert "<strong>bold</strong>" in result

    def test_italic(self):
        result = render_markdown("*italic*")
        assert "<em>italic</em>" in result

    def test_fenced_code_block(self):
        result = render_markdown("```python\nprint('hi')\n```")
        assert "<code" in result
        assert "print" in result

    def test_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        result = render_markdown(md)
        assert "<table>" in result
        assert "<td>1</td>" in result

    def test_link(self):
        result = render_markdown("[example](https://example.com)")
        assert '<a href="https://example.com">example</a>' in result

    def test_empty_string(self):
        assert render_markdown("") == ""

    def test_none(self):
        assert render_markdown(None) == ""
