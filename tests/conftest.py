from pathlib import Path
from typing import Iterator

import pytest

import src.database.connection as database


@pytest.fixture
def temporary_database(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[Path]:
    """
    Substitui o banco da aplicação por um SQLite temporário
    durante cada teste que utiliza esta fixture.
    """

    test_database_path = tmp_path / "test_pncp.db"

    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        test_database_path,
    )

    database.initialize_database()

    yield test_database_path