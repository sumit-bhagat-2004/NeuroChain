"""
Debate routes — API route definitions for debate transcription system.
"""

from fastapi import APIRouter, Query, Body
from typing import Optional
from app.models.debate import TranscriptionRequest, CreateDebateSessionRequest
from app.controllers.debate_controller import (
    add_transcription_handler,
    get_debate_node_handler,
    get_all_debate_nodes_handler,
    get_debate_stats_handler,
    create_debate_session_handler,
    get_debate_session_handler,
    get_all_sessions_handler,
)
from app.controllers.debate_analytics_controller import (
    get_speaker_stats_handler,
    get_leaderboard_handler,
    get_topics_analysis_handler,
    get_debate_conclusion_handler,
    get_ai_analysis_handler,
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
async def get_all_debate_nodes(session_id: str = Query(..., description="Session ID to filter nodes")):
    """
    Get all debate nodes for a specific session.

    Query params:
    - session_id: Required debate session ID (ensures privacy)

    Response:
    {
        "nodes": [...],
        "total": 15,
        "session_id": "uuid"
    }
    """
    return await get_all_debate_nodes_handler(session_id)


@router.get("/stats")
async def get_debate_stats(session_id: str = Query(..., description="Session ID to filter stats")):
    """
    Get debate statistics for a specific session.

    Query params:
    - session_id: Required debate session ID (ensures privacy)

    Response:
    {
        "total_nodes": 15,
        "total_merges": 42,
        "unique_speakers": 6,
        "speakers": ["Speaker A", "Speaker B", ...],
        "avg_merges_per_node": 2.8,
        "session_id": "uuid"
    }
    """
    return await get_debate_stats_handler(session_id)


# ==================== SESSION MANAGEMENT ENDPOINTS ====================


@router.post("/create", status_code=201)
async def create_debate_session(request: CreateDebateSessionRequest):
    """
    Create a new debate session with topic, creators, and participants.

    This initializes a debate session with metadata that can be referenced
    when adding transcriptions (via debate_id field).

    Request body:
    {
        "topic_name": "AI Ethics in Healthcare",
        "creator_wallet": "0x1234...",
        "creator_names": ["Alice", "Bob"],
        "participants": [
            {
                "name": "Charlie",
                "wallet_address": "0x5678..."
            },
            {
                "name": "Diana",
                "wallet_address": "0x9abc..."
            }
        ]
    }

    Response:
    {
        "session_id": "uuid-generated-in-backend",
        "topic_name": "AI Ethics in Healthcare",
        "creator_wallet": "0x1234...",
        "creator_names": ["Alice", "Bob"],
        "participants": [
            {
                "name": "Charlie",
                "wallet_address": "0x5678..."
            },
            {
                "name": "Diana",
                "wallet_address": "0x9abc..."
            }
        ],
        "created_at": 1234567890,
        "status": "active",
        "message": "Debate session created successfully"
    }
    """
    return await create_debate_session_handler(request)


@router.get("/session/{session_id}")
async def get_debate_session(session_id: str):
    """
    Get details of a specific debate session.

    Response:
    {
        "session_id": "uuid",
        "topic_name": "AI Ethics in Healthcare",
        "creator_wallet": "0x1234...",
        "creator_names": ["Alice", "Bob"],
        "participants": [...],
        "created_at": 1234567890,
        "status": "active"
    }
    """
    return await get_debate_session_handler(session_id)


@router.get("/sessions")
async def get_all_sessions():
    """
    Get all debate sessions.

    Response:
    {
        "sessions": [
            {
                "session_id": "uuid",
                "topic_name": "AI Ethics in Healthcare",
                "creator_wallet": "0x1234...",
                "creator_names": ["Alice", "Bob"],
                "participants": [...],
                "created_at": 1234567890,
                "status": "active",
                "total_contributions": 5
            },
            ...
        ],
        "total": 10
    }
    """
    return await get_all_sessions_handler()


# ==================== ANALYTICS ENDPOINTS ====================


@router.get("/speaker/{speaker_name}/stats")
async def get_speaker_stats(speaker_name: str, session_id: str = Query(..., description="Session ID to filter stats")):
    """
    Get comprehensive statistics for a specific speaker in a session.

    Shows credibility and innovation metrics:
    - Credibility: consistency, quality, influence, engagement
    - Innovation: novelty, creativity, diversity, catalyst

    Query params:
    - session_id: Required debate session ID (ensures privacy)

    Response:
    {
        "speaker_name": "Alice",
        "total_contributions": 15,
        "nodes_created": 8,
        "nodes_merged": 7,
        "credibility": {
            "consistency_score": 0.85,
            "quality_score": 0.72,
            "influence_score": 0.68,
            "engagement_depth": 0.79,
            "overall_credibility": 0.76
        },
        "innovation": {
            "novelty_score": 0.53,
            "creativity_average": 0.81,
            "diversity_score": 0.65,
            "catalyst_score": 0.44,
            "overall_innovation": 0.61
        },
        "overall_score": 0.685,
        "rank": 2
    }
    """
    return await get_speaker_stats_handler(speaker_name, session_id)


@router.get("/leaderboard")
async def get_leaderboard(session_id: str = Query(..., description="Session ID to filter leaderboard"), limit: int = Query(default=10, ge=1, le=100)):
    """
    Get ranked list of top speakers in a session.

    Query params:
    - session_id: Required debate session ID (ensures privacy)
    - limit: Number of speakers to return (1-100, default 10)

    Shows speakers ranked by overall score (credibility + innovation).
    Each speaker gets a badge based on their strengths:
    - thought_leader: High influence
    - innovator: High novelty
    - mediator: High engagement
    - catalyst: Triggers many evolutions

    Response:
    {
        "speakers": [
            {
                "rank": 1,
                "speaker_name": "Alice",
                "overall_score": 0.85,
                "credibility_score": 0.82,
                "innovation_score": 0.88,
                "total_contributions": 25,
                "badge": "innovator"
            },
            ...
        ],
        "total": 15
    }
    """
    return await get_leaderboard_handler(limit, session_id)


@router.get("/topics/analysis")
async def get_topics_analysis(session_id: str = Query(..., description="Session ID to filter analysis")):
    """
    Get comprehensive analysis of debate topics in a session.

    Categorizes topics by:
    - Top topics (by overall importance)
    - Controversial topics (most debated)
    - Active topics (highest evolution velocity)
    - Diverse topics (most speakers)

    Query params:
    - session_id: Required debate session ID (ensures privacy)

    Each topic includes:
    - Health metrics: controversy, speaker diversity, evolution velocity
    - Dominance metrics: content volume, time span, merge count
    - Importance score

    Response:
    {
        "total_topics": 42,
        "top_topics": [...],
        "controversial_topics": [...],
        "active_topics": [...],
        "diverse_topics": [...]
    }
    """
    return await get_topics_analysis_handler(session_id)


@router.get("/conclusion")
async def get_debate_conclusion(session_id: str = Query(..., description="Session ID to filter conclusion")):
    """
    Generate comprehensive debate conclusion and analysis for a session.

    Query params:
    - session_id: Required debate session ID (ensures privacy)

    Provides:
    - Top speakers (ranked with badges)
    - Top topics (by importance)
    - Controversial topics (most debated)
    - Consensus topics (high agreement)
    - Emerging trends
    - Key insights
    - Overall debate quality score

    Response:
    {
        "total_nodes": 42,
        "total_contributions": 156,
        "unique_speakers": 12,
        "debate_duration_minutes": 180.5,
        "top_speakers": [
            {
                "rank": 1,
                "speaker_name": "Alice",
                "overall_score": 0.85,
                "badge": "innovator",
                ...
            },
            ...
        ],
        "top_topics": [...],
        "controversial_topics": [...],
        "consensus_topics": [...],
        "trends": [
            {
                "topic_id": "uuid",
                "topic_preview": "AI will transform...",
                "trend_type": "emerging",
                "velocity": 8.5,
                "speakers_involved": ["Alice", "Bob"],
                "description": "Rapidly evolving topic..."
            },
            ...
        ],
        "insights": [
            "Top contributor: Alice with 25 contributions and an innovator badge",
            "Most debated topic: 'AI ethics...' with 15 merges",
            ...
        ],
        "overall_quality_score": 0.78
    }
    """
    return await get_debate_conclusion_handler(session_id)


@router.get("/ai-analysis")
async def get_ai_analysis(session_id: str = Query(..., description="Session ID to filter analysis")):
    """
    Generate AI-powered debate analysis with deep insights and recommendations for a session.

    Query params:
    - session_id: Required debate session ID (ensures privacy)

    Uses Snowflake Cortex LLM (llama3.1-70b) to analyze the debate.

    Unlike /conclusion which provides statistical analysis, this endpoint:
    - Reads and understands the actual debate content
    - Provides nuanced insights about arguments
    - Recommends the best stance based on evidence
    - Generates creative ideas not explicitly mentioned
    - Synthesizes different viewpoints
    - Identifies strongest and weakest arguments
    - Spots emerging patterns
    - Offers actionable recommendations

    Response:
    {
        "summary": "A 2-3 sentence summary of the entire debate",
        "key_insights": [
            "Insight 1: Key pattern or finding from the debate",
            "Insight 2: Another important observation",
            "Insight 3: Third key insight"
        ],
        "best_stance": "Based on the evidence and arguments presented, what appears to be the most defensible position? Explanation with reasoning.",
        "creative_ideas": [
            "Creative idea 1: A novel solution or approach not explicitly mentioned",
            "Creative idea 2: Another innovative perspective",
            "Creative idea 3: A third creative synthesis"
        ],
        "synthesis": "A comprehensive synthesis that bridges different viewpoints and proposes a path forward",
        "strongest_arguments": [
            "Strong argument 1 from the debate",
            "Strong argument 2 from the debate"
        ],
        "weakest_arguments": [
            "Weak argument 1 that lacks support",
            "Weak argument 2 with logical flaws"
        ],
        "emerging_patterns": [
            "Pattern 1: A recurring theme or approach",
            "Pattern 2: Another observable pattern"
        ],
        "recommendations": [
            "Recommendation 1: Actionable suggestion for moving forward",
            "Recommendation 2: Another practical recommendation",
            "Recommendation 3: A third strategic recommendation"
        ],
        "metadata": {
            "total_nodes": 42,
            "unique_speakers": 12,
            "total_contributions": 156,
            "analysis_model": "llama3.1-70b",
            "session_id": null
        }
    }
    """
    return await get_ai_analysis_handler(session_id)


