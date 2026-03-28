"""Tests for the plugin scanner module."""

from pathlib import Path

from cc_plugin_catalog.scanner import (
    _parse_frontmatter,
    read_license,
    read_readme,
    scan_agents,
    scan_commands,
    scan_hooks,
    scan_lsp_servers,
    scan_mcp_servers,
    scan_plugin,
    scan_skills,
)


class TestScanSkills:
    def test_full_plugin(self, full_plugin_path: Path) -> None:
        skills = scan_skills(full_plugin_path)
        assert len(skills) == 2
        names = [s.name for s in skills]
        assert "code-review" in names
        assert "deploy" in names

        code_review = next(s for s in skills if s.name == "code-review")
        expected = "Review code for best practices and potential issues"
        assert code_review.description == expected
        assert code_review.source_path == "skills/code-review/SKILL.md"
        assert "description" in code_review.frontmatter
        assert "disable-model-invocation" in code_review.frontmatter
        assert code_review.frontmatter["disable-model-invocation"] == "True"
        assert code_review.body_html is not None
        assert "Code organization" in code_review.body_html

    def test_minimal_plugin(self, minimal_plugin_path: Path) -> None:
        assert scan_skills(minimal_plugin_path) == []


class TestScanCommands:
    def test_full_plugin(self, full_plugin_path: Path) -> None:
        commands = scan_commands(full_plugin_path)
        assert len(commands) == 1
        assert commands[0].name == "greet"
        assert commands[0].description == "Greet the user with a friendly message"
        assert "description" in commands[0].frontmatter
        assert commands[0].body_html is not None
        assert "warmly" in commands[0].body_html

    def test_minimal_plugin(self, minimal_plugin_path: Path) -> None:
        assert scan_commands(minimal_plugin_path) == []


class TestScanAgents:
    def test_full_plugin(self, full_plugin_path: Path) -> None:
        agents = scan_agents(full_plugin_path)
        assert len(agents) == 1
        assert agents[0].name == "security-reviewer"
        assert agents[0].description == "Reviews code for security vulnerabilities"
        assert agents[0].model == "sonnet"
        assert "name" in agents[0].frontmatter
        assert "model" in agents[0].frontmatter
        assert agents[0].body_html is not None
        assert "security reviewer" in agents[0].body_html

    def test_minimal_plugin(self, minimal_plugin_path: Path) -> None:
        assert scan_agents(minimal_plugin_path) == []


class TestScanHooks:
    def test_full_plugin(self, full_plugin_path: Path) -> None:
        hooks = scan_hooks(full_plugin_path)
        assert len(hooks) == 2

        event_names = [h.event_name for h in hooks]
        assert "PostToolUse" in event_names
        assert "SessionStart" in event_names

        post_tool = next(h for h in hooks if h.event_name == "PostToolUse")
        assert post_tool.matcher == "Write|Edit"
        assert post_tool.hook_type == "command"

        session_start = next(h for h in hooks if h.event_name == "SessionStart")
        assert session_start.matcher is None

    def test_minimal_plugin(self, minimal_plugin_path: Path) -> None:
        assert scan_hooks(minimal_plugin_path) == []


class TestScanMcpServers:
    def test_full_plugin(self, full_plugin_path: Path) -> None:
        servers = scan_mcp_servers(full_plugin_path)
        assert len(servers) == 2

        names = [s.name for s in servers]
        assert "db-server" in names
        assert "cache-server" in names

        db = next(s for s in servers if s.name == "db-server")
        assert db.command == "${CLAUDE_PLUGIN_ROOT}/bin/db-server"
        assert db.args == ["--port", "3000"]

    def test_minimal_plugin(self, minimal_plugin_path: Path) -> None:
        assert scan_mcp_servers(minimal_plugin_path) == []


class TestScanLspServers:
    def test_full_plugin(self, full_plugin_path: Path) -> None:
        servers = scan_lsp_servers(full_plugin_path)
        assert len(servers) == 2

        names = [s.name for s in servers]
        assert "python" in names
        assert "go" in names

        python = next(s for s in servers if s.name == "python")
        assert python.command == "pyright"
        assert python.extensions == {".py": "python", ".pyi": "python"}

    def test_minimal_plugin(self, minimal_plugin_path: Path) -> None:
        assert scan_lsp_servers(minimal_plugin_path) == []


class TestReadReadme:
    def test_full_plugin(self, full_plugin_path: Path) -> None:
        readme = read_readme(full_plugin_path)
        assert readme is not None
        assert "Full Plugin" in readme

    def test_minimal_plugin(self, minimal_plugin_path: Path) -> None:
        assert read_readme(minimal_plugin_path) is None


class TestReadLicense:
    def test_full_plugin(self, full_plugin_path: Path) -> None:
        license_text = read_license(full_plugin_path)
        assert license_text is not None
        assert "MIT License" in license_text

    def test_minimal_plugin(self, minimal_plugin_path: Path) -> None:
        assert read_license(minimal_plugin_path) is None


class TestParseFrontmatter:
    def test_simple_key_value(self) -> None:
        text = "---\nname: my-skill\ndescription: A skill\n---\nBody text"
        meta, body = _parse_frontmatter(text)
        assert meta["name"] == "my-skill"
        assert meta["description"] == "A skill"
        assert body == "Body text"

    def test_no_frontmatter(self) -> None:
        text = "Just plain text"
        meta, body = _parse_frontmatter(text)
        assert meta == {}
        assert body == "Just plain text"

    def test_multiline_block_scalar(self) -> None:
        text = (
            "---\n"
            "name: my-agent\n"
            "description: |\n"
            "  This is a multi-line\n"
            "  description value.\n"
            "model: sonnet\n"
            "---\n"
            "Body content"
        )
        meta, body = _parse_frontmatter(text)
        assert meta["name"] == "my-agent"
        assert "multi-line" in meta["description"]
        assert "description value" in meta["description"]
        assert meta["model"] == "sonnet"
        assert body == "Body content"

    def test_folded_block_scalar(self) -> None:
        text = (
            "---\n"
            "description: >\n"
            "  This is a folded\n"
            "  description.\n"
            "---\n"
            "Body"
        )
        meta, body = _parse_frontmatter(text)
        assert "folded" in meta["description"]
        assert body == "Body"

    def test_boolean_values_as_string(self) -> None:
        text = "---\ndisable-model-invocation: true\n---\nBody"
        meta, body = _parse_frontmatter(text)
        assert meta["disable-model-invocation"] == "True"

    def test_list_values_joined(self) -> None:
        text = "---\ntools:\n  - Read\n  - Write\n  - Bash\n---\nBody"
        meta, body = _parse_frontmatter(text)
        assert meta["tools"] == "Read, Write, Bash"

    def test_unclosed_frontmatter(self) -> None:
        text = "---\nname: test\nNo closing delimiter"
        meta, body = _parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_empty_frontmatter(self) -> None:
        text = "---\n---\nBody only"
        meta, body = _parse_frontmatter(text)
        assert meta == {}
        assert body == "Body only"

    def test_value_with_colon(self) -> None:
        text = "---\ndescription: 'Deploy to production: safely'\n---\nBody"
        meta, body = _parse_frontmatter(text)
        assert "production" in meta["description"]
        assert "safely" in meta["description"]

    def test_inline_list(self) -> None:
        text = "---\nallowed-tools: [Read, Grep, Glob]\n---\nBody"
        meta, body = _parse_frontmatter(text)
        assert meta["allowed-tools"] == "Read, Grep, Glob"


class TestScanPlugin:
    def test_full_plugin(self, full_plugin_path: Path) -> None:
        components = scan_plugin(full_plugin_path)
        assert len(components.skills) == 2
        assert len(components.commands) == 1
        assert len(components.agents) == 1
        assert len(components.hooks) == 2
        assert len(components.mcp_servers) == 2
        assert len(components.lsp_servers) == 2

    def test_minimal_plugin(self, minimal_plugin_path: Path) -> None:
        components = scan_plugin(minimal_plugin_path)
        assert components.skills == []
        assert components.commands == []
        assert components.agents == []
        assert components.hooks == []
        assert components.mcp_servers == []
        assert components.lsp_servers == []
