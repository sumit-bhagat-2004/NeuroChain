"""
Debate routes — API route definitions for debate transcription system.
"""

from fastapi import APIRouter
from app.models.debate import TranscriptionRequest
from app.controllers.debate_controller import (
    add_transcription_handler,
    get_debate_node_handler,
    get_all_debate_nodes_handler,
    get_debate_stats_handler,
)


router = APIRouter(prefix="/debate", tags=["debate"])


@router.post("/transcription", status_code=201)
async def add_transcription(request: TranscriptionRequest):
    """
    Add a new debate transcription.
    
    The system will automatically:
    - Check similarity with existing nodes
    - Merge if similarity > 0.75 (like git merge)
    - Create new node if content is different
    
    Request body:
    {
        "speaker": "Speaker A",
        "text": "I believe that AI will transform education...",
        "debate_id": "optional-debate-session-id",
        "timestamp": 1234567890  // optional
    }
    
    Response:
    {
        "action": "merged" | "created",
        "node_id": "uuid",
        "similarity_score": 0.82,  // if merged
        "merge_count": 3,
        "accumulated_length": 1500
    }
    """
    return await add_transcription_handler(request)


@router.get("/node/{node_id}")
async def get_debate_node(node_id: str):
    """
    Get full details of a debate node.
    
    Shows:
    - Primary text (first transcription)
    - Accumulated text (all merged transcriptions)
    - Merge history (who merged what and when)
    - Speaker list
    
    Response:
    {
        "id": "uuid",
        "primary_text": "...",
        "accumulated_text": "...",
        "created_at": 1234567890,
        "last_updated": 1234567900,
        "merge_count": 3,
        "speakers": ["Speaker A", "Speaker B"],
        "merge_history": [...]
    }
    """
    return await get_debate_node_handler(node_id)


@router.get("/nodes")
async def get_all_debate_nodes():
    """
    Get all debate nodes.
    
    Response:
    {
        "nodes": [...],
        "total": 15
    }
    """
    return await get_all_debate_nodes_handler()


@router.get("/stats")
async def get_debate_stats():
    """
    Get debate statistics.
    
    Response:
    {
        "total_nodes": 15,
        "total_merges": 42,
        "unique_speakers": 6,
        "speakers": ["Speaker A", "Speaker B", ...],
        "avg_merges_per_node": 2.8
    }
    """
    return await get_debate_stats_handler()