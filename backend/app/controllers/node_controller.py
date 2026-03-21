"""
Node controller — Request handlers for the Cognitive Graph API.
"""

import asyncio
from uuid import uuid4
from fastapi import HTTPException

from app.models.node import GraphNode
from app.models.types import NodeResponse, EdgeResponse, CreateNodeResponse, SimilarityBreakdown
from app.services.embedding_service import generate_embedding
from app.services.snowflake_service import (
    insert_node,
    update_node,
    fetch_candidates_by_vector,
    get_all_nodes,
    get_all_edges,
    get_node_by_id,
    get_edges_by_node_id,
)
from app.services.connection_service import create_connections
from app.services.ci_service import run_ci_pipeline
from app.services.enhanced_similarity_service import find_best_match_enhanced
from app.services.thought_evolution_service import (
    should_merge_thought,
    merge_thoughts,
    create_new_thought,
)
from app.config import settings
from app.utils.time_utils import now_timestamp
from app.utils.logger import logger
from app.services.websocket_manager import manager
import httpx



async def create_node_handler(text: str, source: str = None, contributor: str = None) -> CreateNodeResponse:
    """
    POST /node — Create a new node or merge with existing thought.

    Pipeline:
    1. Generate embedding via Snowflake Arctic
    2. Find similar existing thoughts using enhanced similarity
    3. Decide: merge or create new?
        - If highly similar (≥0.50), merge and track evolution
        - Otherwise, create new node
    4. Store/update the node in Snowflake
    5. Fetch candidate nodes via vector similarity search
    6. Score candidates and create qualifying edges
    7. Trigger CI pipeline (async, non-blocking)
    8. Broadcast to WebSocket clients
    9. Return with similarity breakdown and evolution info

    Args:
        text: Input text
        source: Where input came from (meet_voice, meet_chat, manual, etc.)
        contributor: Optional contributor identifier (wallet address, username, etc.)

    Returns:
        CreateNodeResponse with node, edges, similarity breakdown, and evolution info

    Raises:
        HTTPException: 400 if text is empty, 502 if embedding fails, 500 otherwise
    """
    try:
        # Validate input
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text must be non-empty")

        trimmed_text = text.strip()
        logger.info(f"Processing thought from {contributor or 'anonymous'} via {source or 'api'}: \"{trimmed_text[:80]}...\"")

        # 1. Generate embedding
        embedding = await generate_embedding(trimmed_text)

        # 2. Find similar thoughts - get all nodes as candidates for best matching
        all_nodes = await get_all_nodes()
        logger.info(f"Checking against {len(all_nodes)} existing thoughts")

        # 3. Find best match using enhanced similarity (threshold=0.50)
        similar_node, similarity_result = find_best_match_enhanced(
            trimmed_text,
            embedding,
            all_nodes,
            threshold=0.50,  # Low threshold to catch related thoughts
        )

        # Build similarity breakdown (always return this)
        similarity_breakdown = None
        if similarity_result:
            similarity_breakdown = SimilarityBreakdown(
                semantic=similarity_result.semantic,
                keyword=similarity_result.keyword,
                fuzzy=similarity_result.fuzzy,
                edit_distance=similarity_result.edit_distance,
                length_ratio=similarity_result.length_ratio,
                token_overlap=similarity_result.token_overlap,
                composite_score=similarity_result.composite_score,
                confidence=similarity_result.confidence,
            )
            logger.info(f"Similarity check: {similarity_result.to_dict()}")

        # 4. Decide: merge or create new?
        node_action = "created"
        node = None

        if similar_node and similarity_result:
            should_merge, merge_reason = should_merge_thought(similarity_result)

            if should_merge:
                # Merge with existing thought
                logger.info(f"Merging thought (reason: {merge_reason}, score: {similarity_result.composite_score:.3f})")
                node = merge_thoughts(
                    similar_node,
                    trimmed_text,
                    embedding,
                    similarity_result,
                    contributor,
                )
                await update_node(node)
                node_action = "merged"
                logger.info(f"Thought merged into node {node.id} (merge_count={node.merge_count})")
            else:
                # Create new thought
                logger.info(f"Creating new thought (distinct from similar, score: {similarity_result.composite_score:.3f})")
                node = create_new_thought(trimmed_text, embedding, contributor)
                await insert_node(node)
                logger.info(f"New thought created: {node.id}")
        else:
            # No similar thoughts found - create new
            logger.info("No similar thoughts found - creating new thought")
            node = create_new_thought(trimmed_text, embedding, contributor)
            await insert_node(node)
            logger.info(f"New thought created: {node.id}")

        # Anchor on blockchain (fire-and-forget)
        asyncio.create_task(_anchor_on_chain(node.id, node.text, node.embedding))

        # 5. Fetch candidate nodes via vector similarity for connections
        candidates = await fetch_candidates_by_vector(
            embedding,
            settings.candidate_limit,
            node.id
        )
        logger.info(f"Found {len(candidates)} candidate nodes for connections")

        # 6. Create connections (score + threshold + max-3)
        edges = await create_connections(
            node,
            candidates,
            settings.score_threshold,
            settings.max_edges_per_node,
            settings.time_decay_halflife
        )
        logger.info(f"Created {len(edges)} edges for node {node.id}")

        # 7. Trigger CI pipeline asynchronously (fire-and-forget)
        asyncio.create_task(run_ci_pipeline(node.id, settings.time_decay_halflife))

        # 8. Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "node_created" if node_action == "created" else "node_merged",
            "node": {
                "id": node.id,
                "text": node.text,
                "timestamp": node.timestamp,
                "merge_count": node.merge_count,
                "creativity_score": node.creativity_score,
            },
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "score": e.score,
                    "semantic": e.semantic,
                    "keyword": e.keyword,
                    "time": e.time,
                }
                for e in edges
            ],
        })

        # 9. Return response with similarity breakdown and evolution info
        return CreateNodeResponse(
            node=NodeResponse(
                id=node.id,
                text=node.text,
                timestamp=node.timestamp,
                primary_text=node.primary_text,
                accumulated_text=node.accumulated_text,
                merge_count=node.merge_count,
                creativity_score=node.creativity_score,
                contributors=node.contributors,
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
            action=node_action,
            merge_count=node.merge_count,
            creativity_score=node.creativity_score,
            contributors=node.contributors,
            evolution_analysis={
                "evolution_count": len(node.evolution_history),
                "latest_evolution": node.evolution_history[-1].dict() if node.evolution_history else None,
            } if node.evolution_history else None,
            similarity_breakdown=similarity_breakdown,
        )

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Failed to create/merge thought: {error}")

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
                    primary_text=n.primary_text,
                    accumulated_text=n.accumulated_text,
                    merge_count=n.merge_count,
                    creativity_score=n.creativity_score,
                    contributors=n.contributors,
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
                primary_text=node.primary_text,
                accumulated_text=node.accumulated_text,
                merge_count=node.merge_count,
                creativity_score=node.creativity_score,
                contributors=node.contributors,
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
