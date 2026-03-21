"""
Debate service — Handles transcription processing with smart merge logic.
"""

from typing import List, Optional, Tuple
from uuid import uuid4

from app.models.debate import (
    DebateNode,
    TranscriptionSegment,
    MergeRecord,
    TranscriptionRequest,
    TranscriptionResponse,
)
from app.services.embedding_service import generate_embedding
from app.services.scoring_service import cosine_similarity
from app.services.debate_snowflake_service import (
    insert_debate_node,
    update_debate_node,
    get_all_debate_nodes,
    get_debate_node_by_id,
)
from app.utils.time_utils import now_timestamp
from app.utils.logger import logger
from app.config import settings


# Merge threshold - if similarity > this, merge instead of create
MERGE_SIMILARITY_THRESHOLD = 0.75


async def process_transcription(
    request: TranscriptionRequest
) -> TranscriptionResponse:
    """
    Process a new transcription with smart merge logic.
    
    Flow:
    1. Generate embedding for the new text
    2. Find all existing debate nodes
    3. Compare similarity with each node
    4. If similarity > threshold with any node: MERGE
    5. Otherwise: CREATE new node
    
    Args:
        request: Transcription request
        
    Returns:
        TranscriptionResponse with action taken
    """
    text = request.text.strip()
    speaker = request.speaker
    timestamp = request.timestamp or now_timestamp()
    
    logger.info(f"Processing transcription from {speaker}: {text[:50]}...")
    
    # 1. Generate embedding for new text
    embedding = await generate_embedding(text)
    
    # 2. Get all existing debate nodes
    existing_nodes = await get_all_debate_nodes()
    
    if not existing_nodes:
        # No existing nodes - create first one
        logger.info("No existing nodes, creating first debate node")
        return await _create_new_debate_node(text, speaker, embedding, timestamp)
    
    # 3. Find best matching node
    best_match, best_similarity = await _find_best_match(
        embedding,
        existing_nodes
    )
    
    # 4. Decide: merge or create?
    if best_similarity >= MERGE_SIMILARITY_THRESHOLD:
        # MERGE with existing node
        logger.info(
            f"Merging with node {best_match.id} "
            f"(similarity: {best_similarity:.3f})"
        )
        return await _merge_into_node(
            best_match,
            text,
            speaker,
            embedding,
            timestamp,
            best_similarity
        )
    else:
        # CREATE new node
        logger.info(
            f"Creating new node (best similarity: {best_similarity:.3f} "
            f"< threshold: {MERGE_SIMILARITY_THRESHOLD})"
        )
        return await _create_new_debate_node(text, speaker, embedding, timestamp)


async def _find_best_match(
    embedding: List[float],
    nodes: List[DebateNode]
) -> Tuple[Optional[DebateNode], float]:
    """
    Find the most similar existing node.
    
    Args:
        embedding: New text embedding
        nodes: Existing debate nodes
        
    Returns:
        Tuple of (best_matching_node, similarity_score)
    """
    best_node = None
    best_score = 0.0
    
    for node in nodes:
        similarity = cosine_similarity(embedding, node.embedding)
        
        if similarity > best_score:
            best_score = similarity
            best_node = node
    
    return best_node, best_score


async def _create_new_debate_node(
    text: str,
    speaker: str,
    embedding: List[float],
    timestamp: int
) -> TranscriptionResponse:
    """
    Create a new debate node.
    
    Args:
        text: Transcription text
        speaker: Speaker identifier
        embedding: Text embedding
        timestamp: Creation timestamp
        
    Returns:
        TranscriptionResponse with 'created' action
    """
    node = DebateNode(
        id=str(uuid4()),
        primary_text=text,
        accumulated_text=text,
        embedding=embedding,
        created_at=timestamp,
        last_updated=timestamp,
        merge_count=0,
        merge_history=[],
        speakers=[speaker],
    )
    
    await insert_debate_node(node)
    
    logger.info(f"Created new debate node: {node.id}")
    
    return TranscriptionResponse(
        action="created",
        node_id=node.id,
        similarity_score=None,
        merge_count=0,
        accumulated_length=len(text),
    )


async def _merge_into_node(
    existing_node: DebateNode,
    new_text: str,
    speaker: str,
    new_embedding: List[float],
    timestamp: int,
    similarity: float
) -> TranscriptionResponse:
    """
    Merge new transcription into existing node.
    
    The merge strategy:
    1. Append new text to accumulated_text
    2. Update embedding (use new embedding - represents current state)
    3. Add speaker if not already present
    4. Record merge in history
    5. Update timestamps
    
    Args:
        existing_node: Node to merge into
        new_text: New transcription text
        speaker: New speaker
        new_embedding: New text embedding
        timestamp: Merge timestamp
        similarity: Similarity score
        
    Returns:
        TranscriptionResponse with 'merged' action
    """
    # Create merge record
    merge_record = MergeRecord(
        merged_at=timestamp,
        similarity_score=similarity,
        merged_text=new_text,
        merged_speaker=speaker,
    )
    
    # Update node fields
    updated_node = DebateNode(
        id=existing_node.id,
        primary_text=existing_node.primary_text,  # Keep original
        accumulated_text=f"{existing_node.accumulated_text}\n\n[{speaker}]: {new_text}",
        embedding=new_embedding,  # Update to latest embedding
        created_at=existing_node.created_at,
        last_updated=timestamp,
        merge_count=existing_node.merge_count + 1,
        merge_history=existing_node.merge_history + [merge_record],
        speakers=list(set(existing_node.speakers + [speaker])),  # Deduplicate
    )
    
    # Save to database
    await update_debate_node(updated_node)
    
    logger.info(
        f"Merged into node {existing_node.id} "
        f"(merge count: {updated_node.merge_count})"
    )
    
    return TranscriptionResponse(
        action="merged",
        node_id=existing_node.id,
        similarity_score=similarity,
        merge_count=updated_node.merge_count,
        accumulated_length=len(updated_node.accumulated_text),
    )


async def get_debate_node_details(node_id: str) -> Optional[DebateNode]:
    """
    Get full details of a debate node.
    
    Args:
        node_id: Node ID
        
    Returns:
        DebateNode or None if not found
    """
    return await get_debate_node_by_id(node_id)


async def get_all_debate_nodes_list() -> List[DebateNode]:
    """
    Get all debate nodes.
    
    Returns:
        List of all debate nodes
    """
    return await get_all_debate_nodes()