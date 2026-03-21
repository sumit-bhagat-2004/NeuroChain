"""
Debate models — Specialized models for debate transcriptions with merge history.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TranscriptionSegment(BaseModel):
    """A single transcription segment (speaker turn)."""
    
    speaker: str = Field(..., description="Speaker identifier (e.g., 'Speaker A', 'Judge', 'Team 1')")
    text: str = Field(..., description="Transcribed text")
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    duration: Optional[int] = Field(default=None, description="Duration in milliseconds")


class MergeRecord(BaseModel):
    """Record of a merge operation."""
    
    merged_at: int = Field(..., description="When the merge occurred")
    similarity_score: float = Field(..., description="Similarity score that triggered merge")
    merged_text: str = Field(..., description="Text that was merged in")
    merged_speaker: str = Field(..., description="Speaker of merged content")


class DebateNode(BaseModel):
    """A debate node that can accumulate related transcriptions."""
    
    id: str = Field(..., description="UUID v4")
    primary_text: str = Field(..., description="The first/primary transcription text")
    accumulated_text: str = Field(..., description="All merged transcriptions combined")
    embedding: List[float] = Field(
        ...,
        min_length=768,
        max_length=768,
        description="768-dimensional embedding vector"
    )
    created_at: int = Field(..., description="Unix timestamp in milliseconds")
    last_updated: int = Field(..., description="Last merge timestamp")
    merge_count: int = Field(default=0, description="Number of times this node has been merged")
    merge_history: List[MergeRecord] = Field(
        default_factory=list,
        description="History of all merges"
    )
    speakers: List[str] = Field(
        default_factory=list,
        description="All speakers who contributed to this node"
    )


class TranscriptionRequest(BaseModel):
    """Request to add a transcription."""
    
    speaker: str = Field(..., description="Speaker identifier")
    text: str = Field(..., min_length=1, description="Transcription text")
    debate_id: Optional[str] = Field(default=None, description="Optional debate session ID")
    timestamp: Optional[int] = Field(default=None, description="Optional custom timestamp")


class TranscriptionResponse(BaseModel):
    """Response after processing transcription."""
    
    action: str = Field(..., description="'merged' or 'created'")
    node_id: str = Field(..., description="The node ID (existing or new)")
    similarity_score: Optional[float] = Field(
        default=None,
        description="Similarity score if merged"
    )
    merge_count: int = Field(..., description="Total merges for this node")
    accumulated_length: int = Field(..., description="Total accumulated text length")


class DebateNodeDetails(BaseModel):
    """Detailed view of a debate node."""
    
    id: str
    primary_text: str
    accumulated_text: str
    created_at: int
    last_updated: int
    merge_count: int
    speakers: List[str]
    merge_history: List[MergeRecord]