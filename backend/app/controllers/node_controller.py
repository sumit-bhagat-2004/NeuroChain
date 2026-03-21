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
from app.services.enhanced_similarity_service import (
    find_best_match_enhanced,
)
from app.services.snowflake_service import (
    insert_node,
    update_node,
    fetch_candidates_by_vector,
    get_all_nodes,
    get_all_edges,
    get_node_by_id,
    get_edges_by_node_id,
)
from app.services.thought_evolution_service import (
    should_merge_thought,
    merge_thoughts,
    create_new_thought,
    analyze_thought_evolution,
)
from app.tasks.workers import trigger_full_graph_reevaluation
from app.config import settings
from app.utils.time_utils import now_timestamp
from app.utils.logger import logger
from app.services.websocket_manager import manager
import httpx



async def create_node_handler(text: str, source: str = None, contributor: str = None) -> CreateNodeResponse:
    """
    POST /node — Create or evolve a thought node.

    Instead of blocking duplicates, this endpoint tracks thought evolution:
    - Similar thoughts are merged together
    - Evolution history is tracked
    - Creativity scores are calculated
    - Contributors are recorded

    Pipeline:
    1. Generate embedding via Snowflake Arctic
    2. Find similar thoughts using enhanced similarity
    3. If similar thought exists: MERGE (track evolution)
    4. If no similar thought: CREATE new node
    5. Fetch candidate nodes and create edges
    6. Trigger CI pipeline and background re-evaluation
    7. Return node with evolution info

    Args:
        text: Input text
        contributor: Optional contributor identifier (wallet address, username, etc.)

    Returns:
        CreateNodeResponse with node, edges, and evolution info

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

        # 2. Find similar thoughts using enhanced similarity
        all_nodes = await get_all_nodes()

        similar_node, similarity_result = find_best_match_enhanced(
            trimmed_text,
            embedding,
            all_nodes,
            threshold=0.50,  # Lower threshold - we want to track evolution, not block
        )

        node_action = "created"
        is_evolution = False

        #3. Decide: merge or create?
        if similar_node and similarity_result:
            # Check if we should merge
            should_merge, merge_reason = should_merge_thought(similarity_result)

            if should_merge:
                # MERGE - Track thought evolution
                logger.info(
                    f"Merging thought with {similar_node.id} "
                    f"(reason: {merge_reason}, "
                    f"similarity: {similarity_result.composite_score:.3f}, "
                    f"creativity: {1 - similarity_result.composite_score:.3f})"
                )

                node = merge_thoughts(
                    similar_node,
                    trimmed_text,
                    embedding,
                    similarity_result,
                    contributor,
                )

                # Update in database
                await update_node(node)
                node_action = "merged"
                is_evolution = True
            else:
                # CREATE - Distinct thought
                logger.info(f"Creating new thought (distinct from existing, reason: {merge_reason})")
                node = create_new_thought(trimmed_text, embedding, contributor)
                await insert_node(node)
        else:
            # CREATE - First thought or no similar thoughts found
            logger.info("Creating first thought")
            node = create_new_thought(trimmed_text, embedding, contributor)
            await insert_node(node)

        logger.info(f"Thought {node_action}: {node.id}")

        # Anchor on blockchain (fire-and-forget)
        asyncio.create_task(_anchor_on_chain(node.id, node.text, node.embedding))

        # 5. Fetch candidate nodes via vector similarity for edges
        candidates = await fetch_candidates_by_vector(
            embedding,
            settings.candidate_limit,
            node.id
        )
        logger.info(f"Found{len(candidates)} candidate nodes for edges")

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

        # 6. Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "node_created",
            "node": {
                "id": node.id,
                "text": node.text,
                "timestamp": node.timestamp,
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

        # 7. Return response (exclude raw embedding for brevity)
        # 8. Trigger full graph re-evaluation in background (continuous compute)
        logger.info(f"Triggering background re-evaluation for node {node.id}")
        trigger_full_graph_reevaluation.schedule(args=(node.id,), delay=5)

        # 9. Analyze thought evolution
        evolution_analysis = analyze_thought_evolution(node)

        # 10. Prepare similarity breakdown for response
        from app.models.types import SimilarityBreakdown

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

        # 11. Return response with evolution info and similarity breakdown
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
            # Add evolution tracking info
            action=node_action,  # "created" or "merged"
            merge_count=node.merge_count,
            creativity_score=node.creativity_score,
            contributors=node.contributors,
            evolution_analysis=evolution_analysis,
            # Add 6-step similarity breakdown
            similarity_breakdown=similarity_breakdown,
        )

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Failed to process thought: {error}")

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
