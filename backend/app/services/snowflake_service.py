"""
Snowflake service — Database operations with async wrappers.
"""

import asyncio
from functools import wraps
from typing import List, Optional, Dict, Any, Tuple
import snowflake.connector
from snowflake.connector import DictCursor
import json

from app.config import settings
from app.models.node import GraphNode
from app.models.edge import GraphEdge
from app.models.types import CandidateNode
from app.utils.logger import logger


# Global connection instance (singleton)
_connection: Optional[snowflake.connector.SnowflakeConnection] = None


def async_snowflake(func):
    """Decorator to run synchronous Snowflake operations in thread pool."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper


def _get_connection() -> snowflake.connector.SnowflakeConnection:
    """Get or create Snowflake connection (singleton)."""
    global _connection

    if _connection is None or _connection.is_closed():
        logger.info("Creating Snowflake connection...")
        _connection = snowflake.connector.connect(
            account=settings.snowflake_account,
            user=settings.snowflake_username,
            password=settings.snowflake_password,
            warehouse=settings.snowflake_warehouse,
        )
        logger.info("Snowflake connection established")

    return _connection


def _execute_query(sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """Execute SQL query and return results as list of dicts."""
    conn = _get_connection()
    cursor = conn.cursor(DictCursor)

    try:
        cursor.execute(sql, params or [])
        return cursor.fetchall()
    finally:
        cursor.close()


def _execute_non_query(sql: str, params: Optional[List[Any]] = None) -> None:
    """Execute SQL command without returning results (INSERT, UPDATE, DELETE)."""
    conn = _get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(sql, params or [])
        conn.commit()
    finally:
        cursor.close()


# ─── Async Wrappers ─────────────────────────────────────────────────────────────

@async_snowflake
def _initialize_tables_sync() -> None:
    """Create database, schema, and tables if they don't exist."""
    conn = _get_connection()
    cursor = conn.cursor()

    try:
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.snowflake_database}")
        cursor.execute(f"USE DATABASE {settings.snowflake_database}")

        # Create schema if not exists
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.snowflake_schema}")
        cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")

        # Create nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id STRING PRIMARY KEY,
                text STRING,
                timestamp NUMBER,
                embedding VECTOR(FLOAT, 768)
            )
        """)

        # Create edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                source STRING,
                target STRING,
                score FLOAT,
                semantic FLOAT,
                keyword FLOAT,
                time FLOAT,
                PRIMARY KEY (source, target)
            )
        """)

        conn.commit()
        logger.info("Tables initialized successfully")
    finally:
        cursor.close()


async def initialize_tables() -> None:
    """Initialize database tables (async)."""
    await _initialize_tables_sync()


@async_snowflake
def _insert_node_sync(node: GraphNode) -> None:
    """Insert node into database."""
    # Convert embedding to JSON array string
    embedding_json = json.dumps(node.embedding)

    # Use TO_VECTOR(PARSE_JSON()) to properly convert to VECTOR type
    sql = """
        INSERT INTO nodes (id, text, timestamp, embedding)
        VALUES (?, ?, ?, TO_VECTOR(PARSE_JSON(?), 768, 'FLOAT'))
    """

    _execute_non_query(sql, [node.id, node.text, node.timestamp, embedding_json])


async def insert_node(node: GraphNode) -> None:
    """Insert node into database (async)."""
    await _insert_node_sync(node)


@async_snowflake
def _insert_edge_sync(edge: GraphEdge) -> None:
    """Insert edge into database."""
    sql = """
        INSERT INTO edges (source, target, score, semantic, keyword, time)
        VALUES (?, ?, ?, ?, ?, ?)
    """

    _execute_non_query(sql, [
        edge.source,
        edge.target,
        edge.score,
        edge.semantic,
        edge.keyword,
        edge.time,
    ])


async def insert_edge(edge: GraphEdge) -> None:
    """Insert edge into database (async)."""
    await _insert_edge_sync(edge)


@async_snowflake
def _fetch_candidates_by_vector_sync(
    embedding: List[float],
    limit: int,
    exclude_id: str
) -> List[CandidateNode]:
    """Fetch candidate nodes via vector similarity search."""
    # Convert embedding to JSON array string
    embedding_json = json.dumps(embedding)

    sql = """
        SELECT
            id,
            text,
            timestamp,
            embedding,
            VECTOR_COSINE_SIMILARITY(embedding, TO_VECTOR(PARSE_JSON(?), 768, 'FLOAT')) AS similarity
        FROM nodes
        WHERE id != ?
        ORDER BY similarity DESC
        LIMIT ?
    """

    results = _execute_query(sql, [embedding_json, exclude_id, limit])

    candidates = []
    for row in results:
        # Parse embedding array from Snowflake
        embedding_list = row['EMBEDDING'] if isinstance(row['EMBEDDING'], list) else []

        candidates.append(CandidateNode(
            id=row['ID'],
            text=row['TEXT'],
            timestamp=row['TIMESTAMP'],
            embedding=embedding_list,
            similarity=float(row['SIMILARITY'])
        ))

    return candidates


async def fetch_candidates_by_vector(
    embedding: List[float],
    limit: int,
    exclude_id: str
) -> List[CandidateNode]:
    """Fetch candidate nodes via vector similarity search (async)."""
    return await _fetch_candidates_by_vector_sync(embedding, limit, exclude_id)


@async_snowflake
def _generate_embedding_via_snowflake_sync(text: str) -> List[float]:
    """Generate embedding via Snowflake Cortex."""
    sql = "SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m-v1.5', ?) AS embedding"

    results = _execute_query(sql, [text])

    if not results or 'EMBEDDING' not in results[0]:
        raise RuntimeError(f"Failed to generate embedding for text: {text[:50]}...")

    embedding = results[0]['EMBEDDING']

    # Ensure it's a list of floats
    if isinstance(embedding, str):
        embedding = json.loads(embedding)

    return embedding


async def generate_embedding_via_snowflake(text: str) -> List[float]:
    """Generate embedding via Snowflake Cortex (async)."""
    return await _generate_embedding_via_snowflake_sync(text)


@async_snowflake
def _get_all_nodes_sync() -> List[GraphNode]:
    """Fetch all nodes from database."""
    sql = "SELECT id, text, timestamp, embedding FROM nodes"
    results = _execute_query(sql)

    nodes = []
    for row in results:
        embedding_list = row['EMBEDDING'] if isinstance(row['EMBEDDING'], list) else []
        nodes.append(GraphNode(
            id=row['ID'],
            text=row['TEXT'],
            timestamp=row['TIMESTAMP'],
            embedding=embedding_list,
        ))

    return nodes


async def get_all_nodes() -> List[GraphNode]:
    """Fetch all nodes from database (async)."""
    return await _get_all_nodes_sync()


@async_snowflake
def _get_all_edges_sync() -> List[GraphEdge]:
    """Fetch all edges from database."""
    sql = "SELECT source, target, score, semantic, keyword, time FROM edges"
    results = _execute_query(sql)

    edges = []
    for row in results:
        edges.append(GraphEdge(
            source=row['SOURCE'],
            target=row['TARGET'],
            score=row['SCORE'],
            semantic=row['SEMANTIC'],
            keyword=row['KEYWORD'],
            time=row['TIME'],
        ))

    return edges


async def get_all_edges() -> List[GraphEdge]:
    """Fetch all edges from database (async)."""
    return await _get_all_edges_sync()


@async_snowflake
def _get_node_by_id_sync(node_id: str) -> Optional[GraphNode]:
    """Fetch specific node by ID."""
    sql = "SELECT id, text, timestamp, embedding FROM nodes WHERE id = ?"
    results = _execute_query(sql, [node_id])

    if not results:
        return None

    row = results[0]
    embedding_list = row['EMBEDDING'] if isinstance(row['EMBEDDING'], list) else []

    return GraphNode(
        id=row['ID'],
        text=row['TEXT'],
        timestamp=row['TIMESTAMP'],
        embedding=embedding_list,
    )


async def get_node_by_id(node_id: str) -> Optional[GraphNode]:
    """Fetch specific node by ID (async)."""
    return await _get_node_by_id_sync(node_id)


@async_snowflake
def _get_edges_by_node_id_sync(node_id: str) -> List[GraphEdge]:
    """Fetch all edges connected to a node."""
    sql = """
        SELECT source, target, score, semantic, keyword, time
        FROM edges
        WHERE source = ? OR target = ?
    """
    results = _execute_query(sql, [node_id, node_id])

    edges = []
    for row in results:
        edges.append(GraphEdge(
            source=row['SOURCE'],
            target=row['TARGET'],
            score=row['SCORE'],
            semantic=row['SEMANTIC'],
            keyword=row['KEYWORD'],
            time=row['TIME'],
        ))

    return edges


async def get_edges_by_node_id(node_id: str) -> List[GraphEdge]:
    """Fetch all edges connected to a node (async)."""
    return await _get_edges_by_node_id_sync(node_id)


@async_snowflake
def _update_edge_score_sync(
    source: str,
    target: str,
    score: float,
    semantic: float,
    keyword: float,
    time: float
) -> None:
    """Update edge score and breakdown."""
    sql = """
        UPDATE edges
        SET score = ?, semantic = ?, keyword = ?, time = ?
        WHERE source = ? AND target = ?
    """

    _execute_non_query(sql, [score, semantic, keyword, time, source, target])


async def update_edge_score(
    source: str,
    target: str,
    score: float,
    semantic: float,
    keyword: float,
    time: float
) -> None:
    """Update edge score and breakdown (async)."""
    await _update_edge_score_sync(source, target, score, semantic, keyword, time)


@async_snowflake
def _delete_edge_sync(source: str, target: str) -> None:
    """Delete edge from database."""
    sql = "DELETE FROM edges WHERE source = ? AND target = ?"
    _execute_non_query(sql, [source, target])


async def delete_edge(source: str, target: str) -> None:
    """Delete edge from database (async)."""
    await _delete_edge_sync(source, target)


@async_snowflake
def _count_edges_for_node_sync(node_id: str) -> int:
    """Count edges for a node (both incoming and outgoing)."""
    sql = "SELECT COUNT(*) as count FROM edges WHERE source = ? OR target = ?"
    results = _execute_query(sql, [node_id, node_id])

    if results:
        return results[0]['COUNT']

    return 0


async def count_edges_for_node(node_id: str) -> int:
    """Count edges for a node (async)."""
    return await _count_edges_for_node_sync(node_id)