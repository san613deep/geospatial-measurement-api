import json
import sqlite3
from pathlib import Path
from typing import Any


# Store the database in the project root directory.
DATABASE_PATH = Path(__file__).resolve().parents[2] / "geospatial_api.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_db():
    """Create the file records table if it does not exist."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS file_records (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                feature_count INTEGER NOT NULL,
                crs TEXT,
                status TEXT NOT NULL,
                features_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def save_file(file_data: dict[str, Any]) -> None:
    """Save an uploaded file's metadata and extracted features."""

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO file_records (
                id,
                filename,
                feature_count,
                crs,
                status,
                features_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                file_data["id"],
                file_data["filename"],
                file_data["feature_count"],
                file_data["crs"],
                file_data["status"],
                json.dumps(file_data["features"], allow_nan=False),
            ),
        )


def get_file(file_id: str) -> dict[str, Any] | None:
    """Retrieve a complete saved file record."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM file_records
            WHERE id = ?
            """,
            (file_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "filename": row["filename"],
        "feature_count": row["feature_count"],
        "crs": row["crs"],
        "status": row["status"],
        "features": json.loads(row["features_json"]),
        "created_at": row["created_at"],
    }
