"""
Debate Snowflake service — Database operations for debate nodes.
"""

import asyncio
from functools import wraps
from typing import List, Optional, Dict, Any
import snowflake.connector
from snowflake.connector import DictCursor
import json

from app.config import settings
from app.models.debate import DebateNode, MergeRecord
from app.utils.logger import logger


# Share connection with main snowflake service
from app.services.snowflake_service import _get_connection, async_snowflake, _execute_query, _execute_non_query


@async_snowflake
def _initialize_debate_tables_sync() -> None:
    """Create debate-specific tables."""
    conn = _get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"USE DATABASE {settings.snowflake_database}")
        cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")

        # Create debate_nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debate_nodes (
                id STRING PRIMARY KEY,
                primary_text STRING,
                accumulated_text STRING,
                embedding VECTOR(FLOAT, 768),
                created_at NUMBER,
                last_updated NUMBER,
                merge_count NUMBER,
                merge_history STRING,  -- JSON array
                speakers STRING        -- JSON array
            )
        """)

        conn.commit()
        logger.info("Debate tables initialized successfully")
    finally:
        cursor.close()


async def initialize_debate_tables() -> None:
    """Initialize debate tables (async)."""
    await _initialize_debate_tables_sync()


@async_snowflake
def _insert_debate_node_sync(node: DebateNode) -> None:
    """Insert debate node into database."""
    embedding_str = "[" + ",".join(str(x) for x in node.embedding) + "]"
    merge_history_json = json.dumps([m.model_dump() for m in node.merge_history])
    speakers_json = json.dumps(node.speakers)

    sql = """
        INSERT INTO debate_nodes (
            id, primary_text, accumulated_text, embedding,
            created_at, last_updated, merge_count,
            merge_history, speakers
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    _execute_non_query(sql, [
        node.id,
        node.primary_text,
        node.accumulated_text,
        embedding_str,
        node.created_at,
        node.last_updated,
        node.merge_count,
        merge_history_json,
        speakers_json,
    ])


async def insert_debate_node(node: DebateNode) -> None:
    """Insert debate node (async)."""
    await _insert_debate_node_sync(node)


@async_snowflake
def _update_debate_node_sync(node: DebateNode) -> None:
    """Update existing debate node."""
    embedding_str = "[" + ",".join(str(x) for x in node.embedding) + "]"
    merge_history_json = json.dumps([m.model_dump() for m in node.merge_history])
    speakers_json = json.dumps(node.speakers)

    sql = """
        UPDATE debate_nodes
        SET
            accumulated_text = %s,
            embedding = %s,
            last_updated = %s,
            merge_count = %s,
            merge_history = %s,
            speakers = %s
        WHERE id = %s
    """

    _execute_non_query(sql, [
        node.accumulated_text,
        embedding_str,
        node.last_updated,
        node.merge_count,
        merge_history_json,
        speakers_json,
        node.id,
    ])


async def update_debate_node(node: DebateNode) -> None:
    """Update debate node (async)."""
    await _update_debate_node_sync(node)


@async_snowflake
def _get_all_debate_nodes_sync() -> List[DebateNode]:
    """Fetch all debate nodes."""
    sql = """
        SELECT
            id, primary_text, accumulated_text, embedding,
            created_at, last_updated, merge_count,
            merge_history, speakers
        FROM debate_nodes
        ORDER BY created_at ASC
    """
    
    results = _execute_query(sql)

    nodes = []
    for row in results:
        # Parse JSON fields
        merge_history_data = json.loads(row['MERGE_HISTORY']) if row['MERGE_HISTORY'] else []
        speakers_data = json.loads(row['SPEAKERS']) if row['SPEAKERS'] else []
        embedding_list = row['EMBEDDING'] if isinstance(row['EMBEDDING'], list) else []

        merge_history = [MergeRecord(**m) for m in merge_history_data]

        nodes.append(DebateNode(
            id=row['ID'],
            primary_text=row['PRIMARY_TEXT'],
            accumulated_text=row['ACCUMULATED_TEXT'],
            embedding=embedding_list,
            created_at=row['CREATED_AT'],
            last_updated=row['LAST_UPDATED'],
            merge_count=row['MERGE_COUNT'],
            merge_history=merge_history,
            speakers=speakers_data,
        ))

    return nodes


async def get_all_debate_nodes() -> List[DebateNode]:
    """Fetch all debate nodes (async)."""
    return await _get_all_debate_nodes_sync()


@async_snowflake
def _get_debate_node_by_id_sync(node_id: str) -> Optional[DebateNode]:
    """Fetch specific debate node by ID."""
    sql = """
        SELECT
            id, primary_text, accumulated_text, embedding,
            created_at, last_updated, merge_count,
            merge_history, speakers
        FROM debate_nodes
        WHERE id = ?
    """
    
    results = _execute_query(sql, [node_id])

    if not results:
        return None

    row = results[0]
    
    # Parse JSON fields
    merge_history_data = json.loads(row['MERGE_HISTORY']) if row['MERGE_HISTORY'] else []
    speakers_data = json.loads(row['SPEAKERS']) if row['SPEAKERS'] else []
    embedding_list = row['EMBEDDING'] if isinstance(row['EMBEDDING'], list) else []

    merge_history = [MergeRecord(**m) for m in merge_history_data]

    return DebateNode(
        id=row['ID'],
        primary_text=row['PRIMARY_TEXT'],
        accumulated_text=row['ACCUMULATED_TEXT'],
        embedding=embedding_list,
        created_at=row['CREATED_AT'],
        last_updated=row['LAST_UPDATED'],
        merge_count=row['MERGE_COUNT'],
        merge_history=merge_history,
        speakers=speakers_data,
    )


async def get_debate_node_by_id(node_id: str) -> Optional[DebateNode]:
    """Fetch specific debate node (async)."""
    return await _get_debate_node_by_id_sync(node_id)