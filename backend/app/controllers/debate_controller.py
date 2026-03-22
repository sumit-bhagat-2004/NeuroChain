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
    CreateDebateSessionRequest,
    DebateSessionResponse,
)
from app.services.debate_service import (
    process_transcription,
    get_debate_node_details,
    get_all_debate_nodes_list,
)
from app.services.debate_session_service import (
    create_debate_session,
    get_session_by_id,
    get_all_sessions,
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


async def create_debate_session_handler(
    request: CreateDebateSessionRequest
) -> DebateSessionResponse:
    """
    POST /debate/creator

    Create a new debate session with topic, creators, and participants.

    Args:
        request: CreateDebateSessionRequest with session details

    Returns:
        DebateSessionResponse with created session

    Raises:
        HTTPException: 400 if validation fails, 500 otherwise
    """
    try:
        # Validate input
        if not request.topic_name or not request.topic_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Topic name must be non-empty"
            )

        if not request.creator_wallet or not request.creator_wallet.strip():
            raise HTTPException(
                status_code=400,
                detail="Creator wallet must be provided"
            )

        if not request.creator_names:
            raise HTTPException(
                status_code=400,
                detail="At least one creator name must be provided"
            )

        if not request.participants:
            raise HTTPException(
                status_code=400,
                detail="At least one participant must be provided"
            )

        logger.info(
            f"Creating debate session: '{request.topic_name}' - "
            f"Creator: {request.creator_wallet} - "
            f"Participants: {len(request.participants)}"
        )

        # Create the session
        response = await create_debate_session(request)

        logger.info(
            f"Debate session created: {response.session_id} - "
            f"Topic: '{response.topic_name}'"
        )

        return response

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Failed to create debate session: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


async def get_debate_session_handler(session_id: str) -> DebateSessionResponse:
    """
    GET /debate/session/{session_id}

    Get details of a debate session.

    Args:
        session_id: Session ID

    Returns:
        DebateSessionResponse

    Raises:
        HTTPException: 404 if not found
    """
    try:
        session = await get_session_by_id(session_id)

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Debate session not found: {session_id}"
            )

        return DebateSessionResponse(
            session_id=session.session_id,
            topic_name=session.topic_name,
            creator_wallet=session.creator_wallet,
            creator_names=session.creator_names,
            participants=session.participants,
            created_at=session.created_at,
            status=session.status,
        )

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Failed to fetch debate session {session_id}: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


async def get_all_sessions_handler() -> dict:
    """
    GET /debate/sessions

    Get all debate sessions.

    Returns:
        Dict with sessions array
    """
    try:
        sessions = await get_all_sessions()

        return {
            "sessions": [
                {
                    "session_id": s.session_id,
                    "topic_name": s.topic_name,
                    "creator_wallet": s.creator_wallet,
                    "creator_names": s.creator_names,
                    "participants": [p.dict() for p in s.participants],
                    "created_at": s.created_at,
                    "status": s.status,
                    "total_contributions": s.total_contributions,
                }
                for s in sessions
            ],
            "total": len(sessions),
        }

    except Exception as error:
        logger.error(f"Failed to fetch debate sessions: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
