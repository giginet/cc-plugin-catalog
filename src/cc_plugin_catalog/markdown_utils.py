from markdown import markdown


def render_markdown(text: str | None) -> str:
    """Convert markdown text to HTML."""
    if not text:
        return ""
    return markdown(
        text,
        extensions=[
            "fenced_code",
            "tables",
            "toc",
            "codehilite",
        ],
        extension_configs={
            "codehilite": {"css_class": "highlight"},
        },
    )
