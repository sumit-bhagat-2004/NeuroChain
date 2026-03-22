"""
Routes — API route definitions for the Cognitive Graph Engine.
"""

from fastapi import APIRouter, Body, Query
from typing import Optional
from app.controllers.node_controller import (
    create_node_handler,
    get_graph_handler,
    get_node_details_handler,
)
from app.controllers.node_analytics_controller import (
    get_contributor_stats_handler,
    get_contributors_leaderboard_handler,
    get_nodes_analysis_handler,
    get_node_conclusion_handler,
    get_node_ai_analysis_handler,
    get_node_stats_handler,
)


router = APIRouter(tags=["nodes"])


@router.post("/node", status_code=201)
async def create_node(
    text: str = Body(...),
    source: Optional[str] = Body(None),
    author_wallet: Optional[str] = Body(None),
):
    """
    Create a new cognitive graph node from text input.

    This endpoint tracks thought evolution instead of blocking duplicates:
    - Similar thoughts are merged together
    - Evolution history is recorded
    - Creativity scores are calculated
    - Contributors are tracked

    Request body:
        {
            "text": "Your thought here",
            "source": "meet_voice|meet_chat|manual (optional)",
            "author_wallet": "username or wallet address (optional)"
        }

    Response:
        {
            "node": {...},
            "edges": [...],
            "action": "created" | "merged",
            "merge_count": 0,
            "creativity_score": 1.0,
            "contributors": ["user1", "user2"],
            "evolution_analysis": {...}
        }
    """
    return await create_node_handler(text, source=source, contributor=author_wallet)


@router.post("/api/nodes/", status_code=201)
async def create_node_from_extension(
    text: str = Body(...),
    source: Optional[str] = Body(None),
    author_wallet: Optional[str] = Body(None),
):
    """
    Create a new cognitive graph node from extension input.

    Runs the full 6-layer thought-evolution pipeline:
    1. Embedding generation (Snowflake Arctic)
    2. Enhanced similarity search
    3. Merge-or-create decision
    4. Edge creation via connection service
    5. CI pipeline trigger
    6. Blockchain anchoring (fire-and-forget)

    Request body: {"text": "...", "source": "meet_voice|meet_chat", "author_wallet": "..."}
    Response: {"node": {...}, "edges": [...], "action": "created"|"merged", ...}
    """
    return await create_node_handler(text, source=source, contributor=author_wallet)


@router.get("/api/nodes/")
async def list_nodes():
    """
    List all cognitive graph nodes and their edges.

    Returns nodes created via POST /node or POST /api/nodes/ (not debate nodes).

    Response:
        {
            "nodes": [...],
            "edges": [...]
        }
    """
    return await get_graph_handler()


@router.get("/graph")
async def get_graph():
    """
    Retrieve the full knowledge graph (all nodes + edges).

    Response: {"nodes": [...], "edges": [...]}
    """
    return await get_graph_handler()



@router.get("/node/{node_id}")
async def get_node_details(node_id: str):
    """
    Retrieve a single node by ID with its connections.

    Response: {"node": {...}, "edges": [...]}
    """
    return await get_node_details_handler(node_id)


# ==================== ANALYTICS ENDPOINTS ====================


@router.get("/nodes/stats")
async def get_node_stats():
    """
    Get knowledge graph statistics.

    Response:
    {
        "total_nodes": 156,
        "total_evolutions": 342,
        "unique_contributors": 12,
        "contributors": ["user1", "user2", ...],
        "avg_evolutions_per_node": 2.2,
        "avg_creativity_score": 0.76
    }
    """
    return await get_node_stats_handler()


@router.get("/nodes/contributor/{contributor_name}/stats")
async def get_contributor_stats(contributor_name: str):
    """
    Get comprehensive statistics for a specific contributor.

    Shows credibility and innovation metrics:
    - Credibility: consistency, quality, influence, engagement
    - Innovation: novelty, creativity, diversity, catalyst

    Response:
    {
        "speaker_name": "alice",
        "total_contributions": 24,
        "nodes_created": 12,
        "nodes_merged": 12,
        "credibility": {
            "consistency_score": 0.88,
            "quality_score": 0.79,
            "influence_score": 0.71,
            "engagement_depth": 0.82,
            "overall_credibility": 0.80
        },
        "innovation": {
            "novelty_score": 0.50,
            "creativity_average": 0.85,
            "diversity_score": 0.68,
            "catalyst_score": 0.47,
            "overall_innovation": 0.64
        },
        "overall_score": 0.72,
        "rank": 1
    }
    """
    return await get_contributor_stats_handler(contributor_name)


@router.get("/nodes/leaderboard")
async def get_contributors_leaderboard(limit: int = Query(default=10, ge=1, le=100)):
    """
    Get ranked list of top contributors.

    Query params:
    - limit: Number of contributors to return (1-100, default 10)

    Shows contributors ranked by overall score (credibility + innovation).
    Each contributor gets a badge based on their strengths:
    - thought_leader: High influence
    - innovator: High novelty
    - mediator: High engagement
    - catalyst: Triggers many evolutions

    Response:
    {
        "contributors": [
            {
                "rank": 1,
                "speaker_name": "alice",
                "overall_score": 0.87,
                "credibility_score": 0.85,
                "innovation_score": 0.89,
                "total_contributions": 28,
                "badge": "innovator"
            },
            ...
        ],
        "total": 15
    }
    """
    return await get_contributors_leaderboard_handler(limit)


@router.get("/nodes/analysis")
async def get_nodes_analysis():
    """
    Get comprehensive analysis of all nodes in the knowledge graph.

    Categorizes nodes by:
    - Top nodes (by overall importance)
    - High engagement nodes (most evolved)
    - Active nodes (highest evolution velocity)
    - Creative nodes (highest creativity scores)
    - Diverse nodes (most contributors)

    Each node includes:
    - Health metrics: engagement, diversity, evolution velocity
    - Dominance metrics: content volume, time span, merge count
    - Importance score

    Response:
    {
        "total_nodes": 156,
        "top_nodes": [...],
        "high_engagement_nodes": [...],
        "active_nodes": [...],
        "creative_nodes": [...],
        "diverse_nodes": [...]
    }
    """
    return await get_nodes_analysis_handler()


@router.get("/nodes/conclusion")
async def get_node_conclusion():
    """
    Generate comprehensive conclusion and analysis for the knowledge graph.

    Provides:
    - Top contributors (ranked with badges)
    - Top nodes (by importance)
    - High engagement nodes
    - Creative nodes (high creativity scores)
    - Emerging trends
    - Key insights
    - Overall quality score

    Response:
    {
        "total_nodes": 156,
        "total_contributions": 342,
        "unique_speakers": 12,
        "debate_duration_minutes": 450.5,
        "top_speakers": [
            {
                "rank": 1,
                "speaker_name": "alice",
                "overall_score": 0.87,
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
                "topic_preview": "Full accumulated text...",
                "trend_type": "emerging",
                "velocity": 12.5,
                "speakers_involved": ["alice", "bob"],
                "description": "Rapidly evolving topic..."
            },
            ...
        ],
        "insights": [
            "Top contributor: alice with 28 contributions and an innovator badge",
            "Average creativity score: 0.76",
            ...
        ],
        "overall_quality_score": 0.81
    }
    """
    return await get_node_conclusion_handler()


@router.get("/nodes/ai-analysis")
async def get_node_ai_analysis():
    """
    Generate AI-powered knowledge graph analysis with deep insights and recommendations.

    Uses Snowflake Cortex LLM (llama3.1-70b) to analyze the entire knowledge graph.

    Unlike /nodes/conclusion which provides statistical analysis, this endpoint:
    - Reads and understands the actual node content
    - Provides nuanced insights about ideas
    - Recommends the best framework/stance based on evidence
    - Generates creative connections not explicitly mentioned
    - Synthesizes different viewpoints
    - Identifies strongest and weakest ideas
    - Spots emerging patterns
    - Offers actionable recommendations

    Response:
    {
        "summary": "A 2-3 sentence summary of the knowledge graph themes",
        "key_insights": [
            "Insight 1: Key pattern or finding",
            "Insight 2: Another important observation",
            "Insight 3: Third key insight"
        ],
        "best_stance": "Based on the evidence and ideas, what appears to be the most coherent framework? Explanation with reasoning.",
        "creative_ideas": [
            "Creative idea 1: A novel connection not explicitly mentioned",
            "Creative idea 2: Another innovative perspective",
            "Creative idea 3: A third creative synthesis"
        ],
        "synthesis": "A comprehensive synthesis connecting different nodes into a unified framework",
        "strongest_arguments": [
            "Strong argument 1 from the graph",
            "Strong argument 2 from the graph"
        ],
        "weakest_arguments": [
            "Weak argument 1 that lacks support",
            "Weak argument 2 with logical flaws"
        ],
        "emerging_patterns": [
            "Pattern 1: A recurring theme across nodes",
            "Pattern 2: Another observable pattern"
        ],
        "recommendations": [
            "Recommendation 1: Actionable suggestion for expanding the graph",
            "Recommendation 2: Another practical recommendation",
            "Recommendation 3: A third strategic recommendation"
        ],
        "metadata": {
            "total_nodes": 156,
            "unique_contributors": 12,
            "total_evolutions": 342,
            "average_creativity": 0.76,
            "analysis_model": "llama3.1-70b"
        }
    }
    """
    return await get_node_ai_analysis_handler()

