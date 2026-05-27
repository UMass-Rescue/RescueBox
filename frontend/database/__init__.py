"""
Database Caching Module

This module provides simple file-based caching for application data, such as
the list of models, to speed up page loads and reduce API calls.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from frontend.config import DATA_DIR

from .job_db import JobRecord, JobStatus, get_job_db, init_database as init_job_database
from .chat_history_db import ConversationRecord, ChatMessageRecord, get_chat_history_db

logger = logging.getLogger(__name__)

# Use a separate database file for the cache to not interfere with other data.
CACHE_DB_PATH = DATA_DIR / 'cache.db'

def _get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(CACHE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and handles simple schema migration for the cache."""
    try:
        logger.info(f"Initializing cache database at {CACHE_DB_PATH}")
        with _get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the 'models' table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='models'")
            table_exists = cursor.fetchone()

            migration_needed = not table_exists
            if table_exists:
                # Check if the schema is outdated
                cursor.execute("PRAGMA table_info(models)")
                columns = {column['name'] for column in cursor.fetchall()}
                desired_columns = {'uid', 'model_data', 'cached_at'}
                if not desired_columns.issubset(columns):
                    logger.warning("Cache database schema is outdated. Recreating 'models' table.")
                    migration_needed = True
                    cursor.execute("DROP TABLE models")

            if migration_needed:
                logger.info("Creating 'models' table with the latest schema.")
                cursor.execute("""
                    CREATE TABLE models (
                        uid TEXT PRIMARY KEY,
                        model_data TEXT NOT NULL,
                        cached_at TEXT NOT NULL
                    )
                """)

            conn.commit()
        logger.info("Cache database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize cache database: {e}", exc_info=True)

async def cache_models(models_data: List[Dict[str, Any]]):
    """Caches a list of models into the database, replacing any existing data."""
    logger.info(f"Caching {len(models_data)} models to the database.")
    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM models")
        now_iso = datetime.now().isoformat()
        models_to_insert = [
            (model.get('uid'), json.dumps(model), now_iso)
            for model in models_data if model.get('uid')
        ]
        cursor.executemany("INSERT INTO models (uid, model_data, cached_at) VALUES (?, ?, ?)", models_to_insert)
        conn.commit()
    logger.debug("Models cached successfully.")

async def get_cached_models() -> List[Dict[str, Any]]:
    """Retrieves all cached models from the database."""
    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT model_data, cached_at FROM models")
        rows = cursor.fetchall()
        all_models = []
        for row in rows:
            model = json.loads(row['model_data'])
            model['cached_at'] = row['cached_at']
            all_models.append(model)
        logger.debug(f"Found {len(all_models)} raw models in database before filtering.")
        # Filter out system models like 'fs', 'docs', 'manage'
        models = [model for model in all_models if model.get('uid') not in ['fs', 'docs', 'manage']]
        logger.debug(f"Retrieved {len(models)} models from cache.")
        return models

async def get_cached_model_by_uid(uid: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single cached model from the database by its UID."""
    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT model_data, cached_at FROM models WHERE uid = ?", (uid,))
        row = cursor.fetchone()
        if row:
            model_data = json.loads(row['model_data'])
            model_data['cached_at'] = row['cached_at']
            logger.debug(f"Retrieved model {uid} from cache.")
            return model_data
        logger.warning(f"Model {uid} not found in cache.")
        return None

__all__ = [
    'init_db', 'cache_models', 'get_cached_models', 'get_cached_model_by_uid',  # Model cache
    'JobRecord', 'JobStatus', 'get_job_db', 'init_job_database',  # Job DB
    'ConversationRecord', 'ChatMessageRecord', 'get_chat_history_db',  # Chat History DB
]
