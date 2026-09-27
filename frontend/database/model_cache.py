"""SQLite cache for model metadata (separate from jobs / chat / cases)."""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any

from frontend.config import DATA_DIR
from frontend.database.db_exceptions import DB_ERRORS

logger = logging.getLogger(__name__)

CACHE_DB_PATH = DATA_DIR / "cache.db"


def _get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(CACHE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database and handles simple schema migration for the cache."""
    try:
        logger.info("Initializing cache database at %s", CACHE_DB_PATH)
        with _get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='models'"
            )
            table_exists = cursor.fetchone()

            migration_needed = not table_exists
            if table_exists:
                cursor.execute("PRAGMA table_info(models)")
                columns = {column["name"] for column in cursor.fetchall()}
                desired_columns = {"uid", "model_data", "cached_at"}
                if not desired_columns.issubset(columns):
                    logger.warning(
                        "Cache database schema is outdated. Recreating 'models' table."
                    )
                    migration_needed = True
                    cursor.execute("DROP TABLE models")

            if migration_needed:
                logger.info("Creating 'models' table with the latest schema.")
                cursor.execute(
                    """
                    CREATE TABLE models (
                        uid TEXT PRIMARY KEY,
                        model_data TEXT NOT NULL,
                        cached_at TEXT NOT NULL
                    )
                """
                )

            conn.commit()
        logger.info("Cache database initialized successfully.")
    except DB_ERRORS as e:
        logger.error("Failed to initialize cache database: %s", e, exc_info=True)


async def cache_models(models_data: list[dict[str, Any]]):
    """Caches a list of models into the database, replacing any existing data."""
    logger.debug("Caching %d models to the database.", len(models_data))
    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM models")
        now_iso = datetime.now().isoformat()
        models_to_insert = [
            (model.get("uid"), json.dumps(model), now_iso)
            for model in models_data
            if model.get("uid")
        ]
        cursor.executemany(
            "INSERT INTO models (uid, model_data, cached_at) VALUES (?, ?, ?)",
            models_to_insert,
        )
        conn.commit()
    logger.debug("Models cached successfully.")


async def get_cached_models() -> list[dict[str, Any]]:
    """Retrieves all cached models from the database."""
    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT model_data, cached_at FROM models")
        rows = cursor.fetchall()
        all_models = []
        for row in rows:
            model = json.loads(row["model_data"])
            model["cached_at"] = row["cached_at"]
            all_models.append(model)
        logger.debug(
            "Found %d raw models in database before filtering.",
            len(all_models),
        )
        models = [
            model
            for model in all_models
            if model.get("uid") not in ["fs", "docs", "manage"]
        ]
        logger.debug("Retrieved %d models from cache.", len(models))
        return models


async def get_cached_model_by_uid(uid: str) -> dict[str, Any] | None:
    """Retrieves a single cached model from the database by its UID."""
    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT model_data, cached_at FROM models WHERE uid = ?", (uid,))
        row = cursor.fetchone()
        if row:
            model_data = json.loads(row["model_data"])
            model_data["cached_at"] = row["cached_at"]
            logger.debug("Retrieved model %s from cache.", uid)
            return model_data
        logger.warning("Model %s not found in cache.", uid)
        return None


__all__ = [
    "CACHE_DB_PATH",
    "cache_models",
    "get_cached_model_by_uid",
    "get_cached_models",
    "init_db",
]
