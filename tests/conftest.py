"""Shared pytest fixtures for the MC Everywhere Analyzer Agent."""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_bq_results():
    path = FIXTURES_DIR / "mock_bq_results.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}
