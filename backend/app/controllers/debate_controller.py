"""
Debate controller — Request handlers for debate transcription API.
"""

from typing import List
from fastapi import HTTPException

from app.models.debate import (
    TranscriptionRequest,
    TranscriptionResponse,
    DebateNode,
    DebateNodeDetails,
)
from app.services.debate_service import (
    process_transcription,
    get_debate_node_details,
    get_all_debate_nodes_list,
)
from app.utils.logger import logger


async def add_transcription_handler(
    request: TranscriptionRequest
) -> TranscriptionResponse:
    """
    POST /debate/transcription
    
    Add a new transcription. Will either:
    - Merge with existing node (if similarity > 0.75)
    - Create new node (if different from all existing)
    
    Args:
        request: Transcription request
        
    Returns:
        TranscriptionResponse indicating action taken
        
    Raises:
        HTTPException: 400 if validation fails, 500 otherwise
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text must be non-empty"
            )
        
        if not request.speaker or not request.speaker.strip():
            raise HTTPException(
                status_code=400,
                detail="Speaker must be provided"
            )
        
        logger.info(
            f"Adding transcription from {request.speaker}: "
            f"{request.text[:50]}..."
        )
        
        response = await process_transcription(request)
        
        logger.info(
            f"Transcription processed: {response.action} "
            f"(node: {response.node_id})"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Failed to add transcription: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


async def get_debate_node_handler(node_id: str) -> DebateNodeDetails:
    """
    GET /debate/node/{id}
    
    Get full details of a debate node including merge history.
    
    Args:
        node_id: Node ID
        
    Returns:
        DebateNodeDetails
        
    Raises:
        HTTPException: 404 if not found
    """
    try:
        node = await get_debate_node_details(node_id)
        
        if not node:
            raise HTTPException(
                status_code=404,
                detail=f"Debate node not found: {node_id}"
            )
        
        return DebateNodeDetails(
            id=node.id,
            primary_text=node.primary_text,
            accumulated_text=node.accumulated_text,
            created_at=node.created_at,
            last_updated=node.last_updated,
            merge_count=node.merge_count,
            speakers=node.speakers,
            merge_history=node.merge_history,
        )
        
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Failed to fetch debate node {node_id}: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


async def get_all_debate_nodes_handler() -> dict:
    """
    GET /debate/nodes
    
    Get all debate nodes (without embeddings).
    
    Returns:
        Dict with nodes array
    """
    try:
        nodes = await get_all_debate_nodes_list()
        
        return {
            "nodes": [
                {
                    "id": node.id,
                    "primary_text": node.primary_text,
                    "accumulated_text": node.accumulated_text,
                    "created_at": node.created_at,
                    "last_updated": node.last_updated,
                    "merge_count": node.merge_count,
                    "speakers": node.speakers,
                    "merge_history": [
                        {
                            "merged_at": m.merged_at,
                            "similarity_score": m.similarity_score,
                            "merged_speaker": m.merged_speaker,
                            "merged_text": m.merged_text[:100] + "..."  # Truncate
                        }
                        for m in node.merge_history
                    ],
                }
                for node in nodes
            ],
            "total": len(nodes),
        }
        
    except Exception as error:
        logger.error(f"Failed to fetch debate nodes: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


async def get_debate_stats_handler() -> dict:
    """
    GET /debate/stats
    
    Get debate statistics.
    
    Returns:
        Dict with stats
    """
    try:
        nodes = await get_all_debate_nodes_list()
        
        total_merges = sum(node.merge_count for node in nodes)
        all_speakers = set()
        for node in nodes:
            all_speakers.update(node.speakers)
        
        return {
            "total_nodes": len(nodes),
            "total_merges": total_merges,
            "unique_speakers": len(all_speakers),
            "speakers": list(all_speakers),
            "avg_merges_per_node": (
                total_merges / len(nodes) if nodes else 0
            ),
        }
        
    except Exception as error:
        logger.error(f"Failed to fetch debate stats: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )