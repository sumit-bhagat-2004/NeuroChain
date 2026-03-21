"""
Snowflake service — Database operations with async wrappers.
FIXED: Uses Snowflake Cortex embedding function directly (like rag_service repo)
"""

import asyncio
from functools import wraps
from typing import List, Optional, Dict, Any
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
            database=settings.snowflake_database,
            schema=settings.snowflake_schema,
        )
        logger.info("Snowflake connection established")

    return _connection


def _execute_query(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Execute SQL query and return results as list of dicts."""
    conn = _get_connection()
    cursor = conn.cursor(DictCursor)

    try:
        cursor.execute(sql, params or {})
        return cursor.fetchall()
    finally:
        cursor.close()


def _execute_non_query(sql: str, params: Optional[Dict[str, Any]] = None) -> None:
    """Execute SQL command without returning results (INSERT, UPDATE, DELETE)."""
    conn = _get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(sql, params or {})
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
    """
    Insert node into database with evolution tracking fields.

    Uses SELECT with EMBED_TEXT_768 - Snowflake handles VECTOR conversion automatically.
    """
    import json as json_module

    sql = """
        INSERT INTO nodes (
            id, text, timestamp, embedding,
            primary_text, accumulated_text, merge_count,
            evolution_history, contributors, creativity_score, last_updated
        )
        SELECT
            %(id)s,
            %(text)s,
            %(timestamp)s,
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m-v1.5', %(text_for_embedding)s),
            %(primary_text)s,
            %(accumulated_text)s,
            %(merge_count)s,
            PARSE_JSON(%(evolution_history)s),
            PARSE_JSON(%(contributors)s),
            %(creativity_score)s,
            %(last_updated)s
    """

    params = {
        'id': node.id,
        'text': node.text,
        'timestamp': node.timestamp,
        'text_for_embedding': node.text,
        'primary_text': node.primary_text or node.text,
        'accumulated_text': node.accumulated_text or node.text,
        'merge_count': node.merge_count,
        'evolution_history': json_module.dumps([e.dict() for e in node.evolution_history]),
        'contributors': json_module.dumps(node.contributors),
        'creativity_score': node.creativity_score,
        'last_updated': node.last_updated or node.timestamp,
    }

    _execute_non_query(sql, params)


async def insert_node(node: GraphNode) -> None:
    """Insert node into database (async)."""
    await _insert_node_sync(node)


@async_snowflake
def _update_node_sync(node: GraphNode) -> None:
    """
    Update existing node with evolution tracking data.

    Updates text, embedding, and all evolution fields.
    """
    import json as json_module

    sql = """
        UPDATE nodes
        SET
            text = %(text)s,
            embedding = SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m-v1.5', %(text_for_embedding)s),
            accumulated_text = %(accumulated_text)s,
            merge_count = %(merge_count)s,
            evolution_history = PARSE_JSON(%(evolution_history)s),
            contributors = PARSE_JSON(%(contributors)s),
            creativity_score = %(creativity_score)s,
            last_updated = %(last_updated)s
        WHERE id = %(id)s
    """

    params = {
        'id': node.id,
        'text': node.text,
        'text_for_embedding': node.text,
        'accumulated_text': node.accumulated_text,
        'merge_count': node.merge_count,
        'evolution_history': json_module.dumps([e.dict() for e in node.evolution_history]),
        'contributors': json_module.dumps(node.contributors),
        'creativity_score': node.creativity_score,
        'last_updated': node.last_updated,
    }

    _execute_non_query(sql, params)


async def update_node(node: GraphNode) -> None:
    """Update node in database (async)."""
    await _update_node_sync(node)


@async_snowflake
def _insert_edge_sync(edge: GraphEdge) -> None:
    """Insert edge into database."""
    sql = """
        INSERT INTO edges (source, target, score, semantic, keyword, time)
        VALUES (%(source)s, %(target)s, %(score)s, %(semantic)s, %(keyword)s, %(time)s)
    """

    params = {
        'source': edge.source,
        'target': edge.target,
        'score': edge.score,
        'semantic': edge.semantic,
        'keyword': edge.keyword,
        'time': edge.time,
    }

    _execute_non_query(sql, params)


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
    # Convert embedding to JSON for comparison
    embedding_json = json.dumps(embedding)

    sql = """
        SELECT
            id,
            text,
            timestamp,
            embedding,
            VECTOR_COSINE_SIMILARITY(
                embedding,
                PARSE_JSON(%(embedding_json)s)::VECTOR(FLOAT, 768)
            ) AS similarity
        FROM nodes
        WHERE id != %(exclude_id)s
        ORDER BY similarity DESC
        LIMIT %(limit)s
    """

    params = {
        'embedding_json': embedding_json,
        'exclude_id': exclude_id,
        'limit': limit,
    }

    results = _execute_query(sql, params)

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
    sql = "SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m-v1.5', %(text)s) AS embedding"

    results = _execute_query(sql, {'text': text})

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
    """Fetch all nodes from database with evolution tracking."""
    import json as json_module

    sql = """
        SELECT
            id, text, timestamp, embedding,
            primary_text, accumulated_text, merge_count,
            evolution_history, contributors, creativity_score, last_updated
        FROM nodes
    """
    results = _execute_query(sql)

    nodes = []
    for row in results:
        embedding_list = row['EMBEDDING'] if isinstance(row['EMBEDDING'], list) else []

        # Parse JSON fields
        evolution_history_data = row.get('EVOLUTION_HISTORY')
        evolution_history = []
        if evolution_history_data:
            if isinstance(evolution_history_data, str):
                evolution_history_data = json_module.loads(evolution_history_data)
            from app.models.node import ThoughtEvolution
            evolution_history = [ThoughtEvolution(**e) for e in evolution_history_data]

        contributors_data = row.get('CONTRIBUTORS')
        contributors = []
        if contributors_data:
            if isinstance(contributors_data, str):
                contributors = json_module.loads(contributors_data)
            else:
                contributors = contributors_data if isinstance(contributors_data, list) else []

        nodes.append(GraphNode(
            id=row['ID'],
            text=row['TEXT'],
            timestamp=row['TIMESTAMP'],
            embedding=embedding_list,
            primary_text=row.get('PRIMARY_TEXT'),
            accumulated_text=row.get('ACCUMULATED_TEXT'),
            merge_count=row.get('MERGE_COUNT', 0),
            evolution_history=evolution_history,
            contributors=contributors,
            creativity_score=row.get('CREATIVITY_SCORE', 0.0),
            last_updated=row.get('LAST_UPDATED', row['TIMESTAMP']),
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
    """Fetch specific node by ID with evolution tracking."""
    import json as json_module

    sql = """
        SELECT
            id, text, timestamp, embedding,
            primary_text, accumulated_text, merge_count,
            evolution_history, contributors, creativity_score, last_updated
        FROM nodes
        WHERE id = %(id)s
    """
    results = _execute_query(sql, {'id': node_id})

    if not results:
        return None

    row = results[0]
    embedding_list = row['EMBEDDING'] if isinstance(row['EMBEDDING'], list) else []

    # Parse JSON fields
    evolution_history_data = row.get('EVOLUTION_HISTORY')
    evolution_history = []
    if evolution_history_data:
        if isinstance(evolution_history_data, str):
            evolution_history_data = json_module.loads(evolution_history_data)
        from app.models.node import ThoughtEvolution
        evolution_history = [ThoughtEvolution(**e) for e in evolution_history_data]

    contributors_data = row.get('CONTRIBUTORS')
    contributors = []
    if contributors_data:
        if isinstance(contributors_data, str):
            contributors = json_module.loads(contributors_data)
        else:
            contributors = contributors_data if isinstance(contributors_data, list) else []

    return GraphNode(
        id=row['ID'],
        text=row['TEXT'],
        timestamp=row['TIMESTAMP'],
        embedding=embedding_list,
        primary_text=row.get('PRIMARY_TEXT'),
        accumulated_text=row.get('ACCUMULATED_TEXT'),
        merge_count=row.get('MERGE_COUNT', 0),
        evolution_history=evolution_history,
        contributors=contributors,
        creativity_score=row.get('CREATIVITY_SCORE', 0.0),
        last_updated=row.get('LAST_UPDATED', row['TIMESTAMP']),
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
        WHERE source = %(id)s OR target = %(id)s
    """
    results = _execute_query(sql, {'id': node_id})

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
        SET score = %(score)s, semantic = %(semantic)s, keyword = %(keyword)s, time = %(time)s
        WHERE source = %(source)s AND target = %(target)s
    """

    params = {
        'score': score,
        'semantic': semantic,
        'keyword': keyword,
        'time': time,
        'source': source,
        'target': target,
    }

    _execute_non_query(sql, params)


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
    sql = "DELETE FROM edges WHERE source = %(source)s AND target = %(target)s"
    _execute_non_query(sql, {'source': source, 'target': target})


async def delete_edge(source: str, target: str) -> None:
    """Delete edge from database (async)."""
    await _delete_edge_sync(source, target)


@async_snowflake
def _count_edges_for_node_sync(node_id: str) -> int:
    """Count edges for a node (both incoming and outgoing)."""
    sql = "SELECT COUNT(*) as count FROM edges WHERE source = %(id)s OR target = %(id)s"
    results = _execute_query(sql, {'id': node_id})

    if results:
        return results[0]['COUNT']

    return 0


async def count_edges_for_node(node_id: str) -> int:
    """Count edges for a node (async)."""
    return await _count_edges_for_node_sync(node_id)