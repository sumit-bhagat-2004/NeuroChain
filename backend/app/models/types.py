"""
Types — Supporting types and response models.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ScoringBreakdown(BaseModel):
    """Multi-factor scoring breakdown."""
    score: float
    semantic: float
    keyword: float
    time: float


class CandidateNode(BaseModel):
    """Node candidate with pre-computed similarity."""
    id: str
    text: str
    timestamp: int
    embedding: List[float]
    similarity: float  # Cosine similarity from vector search


class NodeResponse(BaseModel):
    """API response for node details (without embedding)."""
    id: str
    text: str
    timestamp: int


class EdgeResponse(BaseModel):
    """API response for edge."""
    source: str
    target: str
    score: float
    semantic: float
    keyword: float
    time: float


class SimilarityBreakdown(BaseModel):
    """
    6-step enhanced similarity breakdown.

    Shows how similar the new thought is to existing thoughts
    using multiple similarity methods.
    """
    semantic: float = 0.0  # Cosine similarity of embeddings (meaning)
    keyword: float = 0.0  # Jaccard similarity of keywords
    fuzzy: float = 0.0  # Character n-gram matching (typos)
    edit_distance: float = 0.0  # Levenshtein ratio (minor edits)
    length_ratio: float = 0.0  # Length comparison (filters very different lengths)
    token_overlap: float = 0.0  # Word-level similarity
    composite_score: float = 0.0  # Weighted average of all methods
    confidence: str = "none"  # "strong" | "moderate" | "weak" | "none"


class CreateNodeResponse(BaseModel):
    """
    Response for POST /node with thought evolution tracking.

    Includes information about whether this was a new thought or
    an evolution of an existing thought.
    """
    node: NodeResponse
    edges: List[EdgeResponse]

    # Evolution tracking fields
    action: str = "created"  # "created" | "merged"
    merge_count: int = 0  # Number of evolutions
    creativity_score: float = 1.0  # Overall creativity [0, 1]
    contributors: List[str] = []  # All contributors
    evolution_analysis: Optional[Dict[str, Any]] = None  # Detailed analysis

    # Similarity breakdown (6-step check)
    similarity_breakdown: Optional[SimilarityBreakdown] = None  # Detailed similarity metrics


class GraphResponse(BaseModel):
    """Response for GET /graph."""
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]


class NodeDetailsResponse(BaseModel):
    """Response for GET /node/:id."""
    node: NodeResponse
    edges: List[EdgeResponse]
