"""Shared test fixtures."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_marketplace_path() -> Path:
    return FIXTURES_DIR / "sample_marketplace"


@pytest.fixture
def full_plugin_path(sample_marketplace_path: Path) -> Path:
    return sample_marketplace_path / "plugins" / "full-plugin"


@pytest.fixture
def minimal_plugin_path(sample_marketplace_path: Path) -> Path:
    return sample_marketplace_path / "plugins" / "minimal-plugin"
