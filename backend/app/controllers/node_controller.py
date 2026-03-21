"""
Node controller — Request handlers for the Cognitive Graph API.
"""

import asyncio
from uuid import uuid4
from fastapi import HTTPException

from app.models.node import GraphNode
from app.models.types import NodeResponse, EdgeResponse, CreateNodeResponse
from app.services.embedding_service import generate_embedding
from app.services.snowflake_service import (
    insert_node,
    fetch_candidates_by_vector,
    get_all_nodes,
    get_all_edges,
    get_node_by_id,
    get_edges_by_node_id,
)
from app.services.connection_service import create_connections
from app.services.ci_service import run_ci_pipeline
from app.config import settings
from app.utils.time_utils import now_timestamp
from app.utils.logger import logger
import httpx



async def create_node_handler(text: str) -> CreateNodeResponse:
    """
    POST /node — Create a new node from text input.

    Pipeline:
    1. Generate embedding via Snowflake Arctic
    2. Store the node in Snowflake
    3. Fetch candidate nodes via vector similarity search
    4. Score candidates and create qualifying edges
    5. Trigger CI pipeline (async, non-blocking)
    6. Return the new node and its edges

    Args:
        text: Input text

    Returns:
        CreateNodeResponse with node and edges

    Raises:
        HTTPException: 400 if text is empty, 502 if embedding fails, 500 otherwise
    """
    try:
        # Validate input
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text must be non-empty")

        trimmed_text = text.strip()
        logger.info(f"Creating node for text: \"{trimmed_text[:80]}...\"")

        # 1. Generate embedding
        embedding = await generate_embedding(trimmed_text)

        # 2. Create and store node
        node = GraphNode(
            id=str(uuid4()),
            text=trimmed_text,
            timestamp=now_timestamp(),
            embedding=embedding,
        )

        await insert_node(node)
        logger.info(f"Node stored: {node.id}")

        # Anchor on blockchain (fire-and-forget)
        asyncio.create_task(_anchor_on_chain(node.id, node.text, node.embedding))

        # 3. Fetch candidate nodes via vector similarity
        candidates = await fetch_candidates_by_vector(
            embedding,
            settings.candidate_limit,
            node.id
        )
        logger.info(f"Found {len(candidates)} candidate nodes")

        # 4. Create connections (score + threshold + max-3)
        edges = await create_connections(
            node,
            candidates,
            settings.score_threshold,
            settings.max_edges_per_node,
            settings.time_decay_halflife
        )
        logger.info(f"Created {len(edges)} edges for node {node.id}")

        # 5. Trigger CI pipeline asynchronously (fire-and-forget)
        asyncio.create_task(run_ci_pipeline(node.id, settings.time_decay_halflife))

        # 6. Return response (exclude raw embedding for brevity)
        return CreateNodeResponse(
            node=NodeResponse(
                id=node.id,
                text=node.text,
                timestamp=node.timestamp,
            ),
            edges=[
                EdgeResponse(
                    source=e.source,
                    target=e.target,
                    score=e.score,
                    semantic=e.semantic,
                    keyword=e.keyword,
                    time=e.time,
                )
                for e in edges
            ],
        )

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Failed to create node: {error}")

        # Differentiate embedding failures from other errors
        message = str(error)
        status_code = 502 if "embedding" in message.lower() else 500

        raise HTTPException(status_code=status_code, detail=message)


async def get_graph_handler() -> dict:
    """
    GET /graph — Retrieve the entire cognitive graph.

    Returns all nodes (without embeddings) and all edges.

    Returns:
        Dict with nodes and edges arrays
    """
    try:
        nodes, edges = await asyncio.gather(
            get_all_nodes(),
            get_all_edges()
        )

        # Strip embeddings from response
        return {
            "nodes": [
                NodeResponse(
                    id=n.id,
                    text=n.text,
                    timestamp=n.timestamp,
                )
                for n in nodes
            ],
            "edges": [
                EdgeResponse(
                    source=e.source,
                    target=e.target,
                    score=e.score,
                    semantic=e.semantic,
                    keyword=e.keyword,
                    time=e.time,
                )
                for e in edges
            ],
        }

    except Exception as error:
        logger.error(f"Failed to fetch graph: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


async def get_node_details_handler(node_id: str) -> dict:
    """
    GET /node/:id — Retrieve a specific node and its connections.

    Args:
        node_id: Node ID

    Returns:
        Dict with node and edges

    Raises:
        HTTPException: 400 if ID invalid, 404 if not found
    """
    try:
        if not node_id or not isinstance(node_id, str):
            raise HTTPException(status_code=400, detail="Node ID is required")

        node = await get_node_by_id(node_id)

        if not node:
            raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")

        edges = await get_edges_by_node_id(node_id)

        # Strip embedding from response
        return {
            "node": NodeResponse(
                id=node.id,
                text=node.text,
                timestamp=node.timestamp,
            ),
            "edges": [
                EdgeResponse(
                    source=e.source,
                    target=e.target,
                    score=e.score,
                    semantic=e.semantic,
                    keyword=e.keyword,
                    time=e.time,
                )
                for e in edges
            ],
        }

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Failed to fetch node {node_id}: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

async def _anchor_on_chain(node_id: str, text: str, embedding: list[float]):
    """Fire-and-forget blockchain anchoring."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/anchor",
                json={
                    "node_id": node_id,
                    "text": text,
                    "embedding": embedding,
                },
                timeout=10.0,
            )
            logger.info(f"Blockchain anchor response: {response.status_code} — {response.text}")
    except Exception as e:
        logger.warning(f"Blockchain anchoring failed (non-fatal): {e}")
