import sys
from collections.abc import Callable
from pathlib import Path

import pytest

LIB_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = LIB_DIR / "tests" / "fixtures"

sys.path.insert(0, str(LIB_DIR / "scripts"))


@pytest.fixture
def fixture_text() -> Callable[[str], str]:
    """Devuelve una función que lee ``tests/fixtures/<name>.txt`` en UTF-8."""

    def read(name: str) -> str:
        return (FIXTURES_DIR / f"{name}.txt").read_text(encoding="utf-8")

    return read
