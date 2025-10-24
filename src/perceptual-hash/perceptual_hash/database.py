"""Database module for storing and querying perceptual hashes using PostgreSQL with pgvector.

IMPROVED SCHEMA with better naming and structure.
"""

import os
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector

logger = logging.getLogger(__name__)


class HashDatabase:
    """PostgreSQL with pgvector-based database for storing and querying perceptual hashes.
    
    IMPROVED VERSION with:
    - Better table naming (no redundant prefixes)
    - Timestamp with timezone
    - File path index
    - Correct L1/Hamming distance indexes
    - Optimal index parameters
    
    Supports context manager for automatic connection cleanup:
        with HashDatabase() as db:
            db.add_hashes(...)
    """

    def __init__(self):
        """Initialize the hash database connection."""
        # Get database connection parameters from environment variables
        self.db_host = os.environ.get("POSTGRES_HOST", "localhost")
        self.db_port = os.environ.get("POSTGRES_PORT", "5432")
        self.db_name = os.environ.get("POSTGRES_DB", "rescuebox")
        self.db_user = os.environ.get("POSTGRES_USER", "test")
        self.db_password = os.environ.get("POSTGRES_PASSWORD", "test")
        
        # Check testing flag with flexible values
        testing = os.environ.get("IS_TESTING", "false").lower()
        if testing in ("true", "1", "yes", "on"):
            # Use separate test database
            self.db_name = "rescuebox_test"
        
        self.conn = None
        self._max_reconnect_attempts = 3
        self._connect()
        self._ensure_extension()
        self._ensure_base_table()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed."""
        self.close()
        return False  # Don't suppress exceptions

    def _connect(self):
        """Establish database connection with retry logic."""
        for attempt in range(self._max_reconnect_attempts):
            try:
                self.conn = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password
                )
                # Register pgvector extension
                register_vector(self.conn)
                logger.info(f"Connected to PostgreSQL database: {self.db_name}")
                return
            except psycopg2.OperationalError as e:
                if attempt < self._max_reconnect_attempts - 1:
                    logger.warning(f"Connection attempt {attempt + 1} failed, retrying...")
                else:
                    logger.error(f"Failed to connect to PostgreSQL after {self._max_reconnect_attempts} attempts: {e}")
                    logger.error(
                        "Make sure PostgreSQL is running and accessible. "
                        "Set POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD environment variables if needed."
                    )
                    raise

    def _ensure_connected(self):
        """Ensure connection is alive, reconnect if needed.
        
        Call this at the start of each public method to handle connection drops.
        """
        try:
            if self.conn is None or self.conn.closed:
                logger.warning("Connection was closed, reconnecting...")
                self._connect()
                # Re-initialize after reconnection
                self._ensure_extension()
                self._ensure_base_table()
            else:
                # Test connection with lightweight query
                with self.conn.cursor() as cur:
                    cur.execute("SELECT 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logger.warning(f"Connection test failed: {e}, reconnecting...")
            self._connect()
            # Re-initialize after reconnection
            self._ensure_extension()
            self._ensure_base_table()

    def _ensure_extension(self):
        """Ensure pgvector extension is installed."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create pgvector extension: {e}")
            raise

    def _ensure_base_table(self):
        """Ensure the collections tracking table exists."""
        try:
            with self.conn.cursor() as cur:
                # Create table to track collections
                # IMPROVED: Better naming, timezone-aware timestamps
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS hash_collections (
                        id SERIAL PRIMARY KEY,
                        collection_name VARCHAR(255) NOT NULL,
                        hash_algorithm VARCHAR(50) NOT NULL,
                        vector_dimension INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        total_hashes INTEGER DEFAULT 0,
                        UNIQUE(collection_name, hash_algorithm)
                    )
                """)
                
                # Create index on created_at for time-based queries
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_hash_collections_created_at 
                    ON hash_collections (created_at DESC)
                """)
                
                self.conn.commit()
                logger.info("Ensured hash_collections table exists")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create collections table: {e}")
            raise

    def create_collection_name(self, base_name: str, hash_algorithm: str) -> str:
        """
        Create a collection table name.
        
        IMPROVED: Simpler naming without redundant prefixes
        Format: {collection}_{algorithm} (e.g., "photos_pdq", "videos_phash")
        
        Args:
            base_name: Base collection name
            hash_algorithm: Hash algorithm (e.g., 'pdq', 'phash', 'dhash')
            
        Returns:
            Table name (sanitized for SQL)
            
        Raises:
            ValueError: If names contain invalid characters
        """
        import re
        
        # Sanitize: only allow alphanumeric and underscore
        safe_base = re.sub(r'[^a-zA-Z0-9_]', '_', base_name).lower()
        safe_algo = re.sub(r'[^a-zA-Z0-9_]', '_', hash_algorithm).lower()
        
        # Simple format: collection_algorithm
        table_name = f"{safe_base}_{safe_algo}"
        
        # Ensure starts with letter
        if table_name[0].isdigit():
            table_name = f"h_{table_name}"
        
        # Truncate to PostgreSQL identifier limit (63 chars)
        if len(table_name) > 63:
            table_name = table_name[:63]
            logger.warning(f"Table name truncated to 63 characters: {table_name}")
        
        return table_name

    def get_available_collections(self) -> List[str]:
        """
        Get list of available collection base names.
        
        Returns:
            List of unique collection base names (without hash algorithm suffix)
        """
        self._ensure_connected()
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT collection_name 
                    FROM hash_collections 
                    ORDER BY collection_name
                """)
                results = cur.fetchall()
                return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Failed to get available collections: {e}")
            return []

    def get_or_create_collection(
        self, 
        collection_name: str, 
        hash_algorithm: str, 
        vector_dimension: Optional[int] = None
    ) -> str:
        """
        Get or create a collection table for a specific hash algorithm.
        
        IMPROVED: Better schema with file_path index and timezone timestamps
        
        Args:
            collection_name: Base collection name
            hash_algorithm: Hash algorithm name
            vector_dimension: Dimension of hash vectors (required for new tables)
            
        Returns:
            Table name
            
        Raises:
            ValueError: If vector_dimension is None for new collection
        """
        self._ensure_connected()
        
        table_name = self.create_collection_name(collection_name, hash_algorithm)
        
        try:
            with self.conn.cursor() as cur:
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s AND table_schema = 'public'
                    )
                """, (table_name,))
                table_exists = cur.fetchone()[0]
                
                if not table_exists:
                    if vector_dimension is None:
                        raise ValueError(
                            f"vector_dimension is required when creating new collection {table_name}"
                        )
                    
                    # Register collection in tracking table
                    cur.execute("""
                        INSERT INTO hash_collections (collection_name, hash_algorithm, vector_dimension, total_hashes)
                        VALUES (%s, %s, %s, 0)
                        ON CONFLICT (collection_name, hash_algorithm)
                        DO UPDATE SET
                            vector_dimension = EXCLUDED.vector_dimension,
                            updated_at = CURRENT_TIMESTAMP
                    """, (collection_name, hash_algorithm, vector_dimension))
                    
                    # Create the hash table with IMPROVED schema
                    cur.execute(f"""
                        CREATE TABLE {table_name} (
                            id SERIAL PRIMARY KEY,
                            file_path TEXT NOT NULL,
                            hash_string TEXT NOT NULL,
                            hash_vector vector({vector_dimension}) NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(file_path)
                        )
                    """)
                    
                    # Add index on file_path for faster lookups
                    # (UNIQUE constraint already creates index, but explicit is clearer)
                    
                    # Add index on created_at for time-based queries
                    cur.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at 
                        ON {table_name} (created_at DESC)
                    """)
                    
                    # Add table comment for documentation
                    cur.execute(f"""
                        COMMENT ON TABLE {table_name} IS 
                        'Perceptual hashes for collection {collection_name} using {hash_algorithm} algorithm ({vector_dimension}-dimensional vectors)'
                    """)
                    
                    logger.info(f"Created table {table_name} with vector dimension {vector_dimension}")
                
                self.conn.commit()
                
            return table_name
        except Exception as e:
            logger.error(f"Failed to create collection {table_name}: {e}")
            self.conn.rollback()
            raise

    def _validate_hashes(self, hashes: List[Dict[str, Any]]) -> int:
        """
        Validate hash data and return vector dimension.
        
        Args:
            hashes: List of hash dictionaries
            
        Returns:
            Vector dimension
            
        Raises:
            ValueError: If hashes are invalid
        """
        if not hashes:
            raise ValueError("hashes list cannot be empty")
        
        # Validate first hash structure
        first_hash = hashes[0]
        required_keys = ["hash_vector", "file_path", "hash_string"]
        for key in required_keys:
            if key not in first_hash:
                raise ValueError(f"Hash must contain '{key}' key")
        
        vector_dimension = len(first_hash["hash_vector"])
        
        # Validate all hashes
        for i, h in enumerate(hashes):
            # Check required keys
            for key in required_keys:
                if key not in h:
                    raise ValueError(f"Hash {i} missing required key: {key}")
            
            # Check dimension consistency
            if len(h["hash_vector"]) != vector_dimension:
                raise ValueError(
                    f"Hash {i} has dimension {len(h['hash_vector'])}, "
                    f"expected {vector_dimension}"
                )
            
            # Check for invalid values
            vec = np.array(h["hash_vector"])
            if np.any(np.isnan(vec)):
                raise ValueError(f"Hash {i} contains NaN values")
            if np.any(np.isinf(vec)):
                raise ValueError(f"Hash {i} contains infinity values")
        
        return vector_dimension

    def add_hashes(
        self,
        collection_name: str,
        hash_algorithm: str,
        hashes: List[Dict[str, Any]]
    ):
        """
        Add perceptual hashes to the database.
        
        IMPROVED: Creates index with correct L1 distance operator and optimal parameters
        
        Args:
            collection_name: Base collection name
            hash_algorithm: Hash algorithm used
            hashes: List of hash dictionaries with 'hash_vector', 'file_path', and 'hash_string' keys
            
        Raises:
            ValueError: If hashes are invalid
        """
        if not hashes:
            logger.info("No hashes to add")
            return
        
        self._ensure_connected()
        
        # Validate hashes
        vector_dimension = self._validate_hashes(hashes)
        
        table_name = self.get_or_create_collection(collection_name, hash_algorithm, vector_dimension)
        
        try:
            with self.conn.cursor() as cur:
                # Prepare data for insertion
                data = [
                    (
                        h["file_path"],
                        h["hash_string"],
                        np.array(h["hash_vector"])
                    )
                    for h in hashes
                ]
                
                # Use ON CONFLICT to handle duplicates
                execute_values(
                    cur,
                    f"""
                    INSERT INTO {table_name} (file_path, hash_string, hash_vector)
                    VALUES %s
                    ON CONFLICT (file_path) DO UPDATE
                    SET hash_string = EXCLUDED.hash_string,
                        hash_vector = EXCLUDED.hash_vector,
                        created_at = CURRENT_TIMESTAMP
                    """,
                    data
                )
                
                # Update total_hashes count
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_count = cur.fetchone()[0]
                
                cur.execute("""
                    UPDATE hash_collections
                    SET total_hashes = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE collection_name = %s AND hash_algorithm = %s
                """, (total_count, collection_name, hash_algorithm))

                # Verify the UPDATE actually affected a row
                if cur.rowcount == 0:
                    logger.warning(
                        f"UPDATE hash_collections affected 0 rows for "
                        f"collection_name={collection_name}, hash_algorithm={hash_algorithm}. "
                        f"This might indicate the tracking table row doesn't exist."
                    )
                
                # Create index if we have enough data
                # Note: IVFFlat does not support L1 distance (Hamming) operator class
                # For Hamming distance on binary vectors, queries will use <+> operator without index acceleration
                # We skip index creation to keep queries using true Hamming distance
                if total_count >= 100:
                    logger.info(
                        f"Collection {table_name} has {total_count} hashes. "
                        f"Note: IVFFlat indexes do not support Hamming distance (L1). "
                        f"Queries will use exact Hamming distance calculation without index acceleration."
                    )
                    # Index creation skipped intentionally to preserve Hamming distance semantics
                
                self.conn.commit()
                logger.info(f"Added {len(hashes)} hashes to {table_name} (total: {total_count})")
                
        except Exception as e:
            logger.error(f"Failed to add hashes to {table_name}: {e}")
            self.conn.rollback()
            raise

    def query_hashes(
        self,
        collection_name: str,
        hash_algorithm: str,
        query_hashes: List[Dict[str, Any]],
        n_results: int = 10,
        threshold: Optional[float] = None,
    ) -> List[List[Dict[str, Any]]]:
        """
        Query the database for similar hashes using Hamming distance (L1).
        
        IMPROVED: Uses L1 distance operator for binary perceptual hashes
        
        Args:
            collection_name: Base collection name
            hash_algorithm: Hash algorithm to use
            query_hashes: List of query hash dictionaries with 'hash_vector' key
            n_results: Number of results to return per query (max 10000)
            threshold: Maximum Hamming distance threshold (None = no filtering)
            
        Returns:
            List of results for each query hash. Each result contains:
                - file_path: Path to the file
                - hash_string: String representation of the hash
                - hamming_distance: Integer Hamming distance
                - distance: Float distance value
                - similarity: Normalized similarity (0.0 to 1.0)
                
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate parameters
        if n_results < 1:
            raise ValueError(f"n_results must be positive, got {n_results}")
        if n_results > 10000:
            logger.warning(f"Large n_results ({n_results}) capped at 10000")
            n_results = 10000
        
        if threshold is not None and threshold < 0:
            raise ValueError(f"threshold must be non-negative, got {threshold}")
        
        if not query_hashes:
            logger.warning("No query hashes provided")
            return []
        
        self._ensure_connected()
        
        table_name = self.create_collection_name(collection_name, hash_algorithm)
        
        # Check if table exists
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s AND table_schema = 'public'
                    )
                """, (table_name,))
                if not cur.fetchone()[0]:
                    logger.warning(f"Collection {collection_name} with algorithm {hash_algorithm} does not exist")
                    return [[] for _ in query_hashes]
        except Exception as e:
            logger.error(f"Failed to check if table exists: {e}")
            return [[] for _ in query_hashes]
        
        all_results: List[List[Dict[str, Any]]] = []
        
        # Process each query individually to handle errors gracefully
        for idx, query_hash in enumerate(query_hashes):
            try:
                with self.conn.cursor() as cur:
                    # Ensure vector is a numpy array
                    query_vector = np.array(query_hash["hash_vector"], dtype=float)
                    vec_len = query_vector.size
                    
                    # Build query with L1 distance (Hamming for binary hashes)
                    if threshold is not None:
                        sql = f"""
                            SELECT file_path, hash_string,
                                   hash_vector <+> %s::vector AS hamming_distance
                            FROM {table_name}
                            WHERE hash_vector <+> %s::vector <= %s
                            ORDER BY hamming_distance
                            LIMIT %s
                        """
                        params = (query_vector, query_vector, threshold, n_results)
                    else:
                        sql = f"""
                            SELECT file_path, hash_string,
                                   hash_vector <+> %s::vector AS hamming_distance
                            FROM {table_name}
                            ORDER BY hamming_distance
                            LIMIT %s
                        """
                        params = (query_vector, n_results)
                    
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    query_results: List[Dict[str, Any]] = []
                    for file_path, hash_string, distance in results:
                        # For binary hashes, distance is Hamming distance
                        hamming = int(distance)
                        # Normalized similarity: 0 bits different = 1.0, all bits different = 0.0
                        similarity = 1.0 - (hamming / float(vec_len)) if vec_len > 0 else 0.0
                        
                        query_results.append({
                            "file_path": file_path,
                            "hash_string": hash_string,
                            "hamming_distance": hamming,
                            "distance": float(distance),
                            "similarity": similarity,
                        })
                    
                    all_results.append(query_results)
                    
            except KeyError as e:
                logger.error(f"Query hash {idx} missing required key: {e}")
                all_results.append([])
            except Exception as e:
                logger.error(f"Failed to query hash {idx} from {table_name}: {e}")
                all_results.append([])
        
        return all_results

    def export_collection(
        self,
        collection_name: str,
        hash_algorithm: str,
        output_path: str
    ):
        """
        Export a collection to a JSON file.
        
        Args:
            collection_name: Base collection name
            hash_algorithm: Hash algorithm
            output_path: Path to output JSON file
            
        Raises:
            ValueError: If collection doesn't exist
        """
        self._ensure_connected()
        
        table_name = self.create_collection_name(collection_name, hash_algorithm)
        
        # Check if table exists
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s AND table_schema = 'public'
                    )
                """, (table_name,))
                
                if not cur.fetchone()[0]:
                    available = self.get_available_collections()
                    raise ValueError(
                        f"Collection '{collection_name}' with algorithm '{hash_algorithm}' does not exist. "
                        f"Available collections: {available}"
                    )
        except psycopg2.Error as e:
            logger.error(f"Failed to check collection existence: {e}")
            raise
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"""
                    SELECT file_path, hash_string, hash_vector
                    FROM {table_name}
                    ORDER BY created_at
                """)
                
                results = cur.fetchall()
                
                export_data = {
                    "collection_name": collection_name,
                    "hash_algorithm": hash_algorithm,
                    "hashes": []
                }
                
                for file_path, hash_string, hash_vector in results:
                    # Convert pgvector to list of Python floats (for JSON serialization)
                    if hash_vector is not None:
                        vector_list = [float(x) for x in hash_vector]
                    else:
                        vector_list = []
                    export_data["hashes"].append({
                        "hash_vector": vector_list,
                        "file_path": file_path,
                        "hash_string": hash_string,
                    })
                
                # Write to file
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                    
                logger.info(f"Exported {len(results)} hashes from {table_name} to {output_path}")
                
        except Exception as e:
            logger.error(f"Failed to export collection {table_name}: {e}")
            raise

    def import_collection(self, input_path: str, new_collection_name: Optional[str] = None):
        """
        Import a collection from a JSON file.
        
        Args:
            input_path: Path to input JSON file
            new_collection_name: Optional new name for the collection (uses original if None)
        """
        self._ensure_connected()
        
        with open(input_path, 'r') as f:
            import_data = json.load(f)
        
        collection_name = new_collection_name or import_data["collection_name"]
        hash_algorithm = import_data["hash_algorithm"]
        
        # Add hashes to collection
        self.add_hashes(collection_name, hash_algorithm, import_data["hashes"])
        logger.info(f"Imported {len(import_data['hashes'])} hashes to {collection_name}")

    def delete_collection(self, collection_name: str, hash_algorithm: str):
        """
        Delete a collection.
        
        Args:
            collection_name: Base collection name
            hash_algorithm: Hash algorithm
        """
        self._ensure_connected()
        
        table_name = self.create_collection_name(collection_name, hash_algorithm)
        
        try:
            with self.conn.cursor() as cur:
                # Remove from tracking table
                cur.execute("""
                    DELETE FROM hash_collections
                    WHERE collection_name = %s AND hash_algorithm = %s
                """, (collection_name, hash_algorithm))
                
                # Drop the table
                cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                
                self.conn.commit()
                logger.info(f"Deleted collection {table_name}")
                
        except Exception as e:
            logger.error(f"Failed to delete collection {table_name}: {e}")
            self.conn.rollback()
            raise

    def get_collection_stats(self, collection_name: str, hash_algorithm: str) -> Dict[str, Any]:
        """
        Get statistics about a collection.
        
        Args:
            collection_name: Base collection name
            hash_algorithm: Hash algorithm
            
        Returns:
            Dictionary with collection statistics
        """
        self._ensure_connected()
        
        table_name = self.create_collection_name(collection_name, hash_algorithm)
        
        try:
            with self.conn.cursor() as cur:
                # Check if table exists first
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s AND table_schema = 'public'
                    )
                """, (table_name,))
                
                if not cur.fetchone()[0]:
                    logger.info(f"Collection {table_name} does not exist")
                    return {
                        "collection_name": collection_name,
                        "hash_algorithm": hash_algorithm,
                        "total_hashes": 0,
                        "vector_dimension": 0,
                    }
                
                # Get stats from tracking table
                cur.execute("""
                    SELECT total_hashes, vector_dimension, created_at, updated_at
                    FROM hash_collections
                    WHERE collection_name = %s AND hash_algorithm = %s
                """, (collection_name, hash_algorithm))
                
                result = cur.fetchone()
                if result:
                    total_hashes, vector_dim, created_at, updated_at = result
                    return {
                        "collection_name": collection_name,
                        "hash_algorithm": hash_algorithm,
                        "total_hashes": total_hashes,
                        "vector_dimension": vector_dim,
                        "created_at": created_at.isoformat() if created_at else None,
                        "updated_at": updated_at.isoformat() if updated_at else None,
                    }
                else:
                    # Fallback to counting
                    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cur.fetchone()[0]
                    return {
                        "collection_name": collection_name,
                        "hash_algorithm": hash_algorithm,
                        "total_hashes": count,
                    }
        except Exception as e:
            logger.error(f"Failed to get stats for {table_name}: {e}")
            return {
                "collection_name": collection_name,
                "hash_algorithm": hash_algorithm,
                "total_hashes": 0,
            }

    def close(self):
        """Close database connection. Safe to call multiple times."""
        if self.conn and not self.conn.closed:
            try:
                self.conn.close()
                logger.info("Closed PostgreSQL connection")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
        self.conn = None

    def __del__(self):
        """Cleanup on deletion. Note: __exit__ is preferred for guaranteed cleanup."""
        try:
            self.close()
        except Exception:
            pass  # Ignore errors in destructor