import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "pncp.db"


def get_connection() -> sqlite3.Connection:
    """Cria uma conexão com o banco SQLite da aplicação."""

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database() -> None:
    """Cria a estrutura inicial do banco caso ela ainda não exista."""

    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS procurements (
                pncp_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                modality TEXT,
                last_update TEXT,
                organization TEXT,
                city TEXT,
                state TEXT,
                object_description TEXT,
                url TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:
        connection.close()