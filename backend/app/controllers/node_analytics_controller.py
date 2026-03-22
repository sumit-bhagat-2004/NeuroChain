"""
Node analytics controller — Handlers for node analytics endpoints.
"""

from fastapi import HTTPException
from typing import Optional

from app.models.debate_analytics import (
    SpeakerStats,
    SpeakerRanking,
    TopicStats,
    DebateConclusion,
)
from app.services.snowflake_service import get_all_nodes
from app.services.node_analytics_service import (
    calculate_contributor_stats,
    calculate_node_topic_stats,
    generate_node_conclusion,
)
from app.services.node_ai_service import analyze_nodes_with_ai
from app.utils.logger import logger


async def get_contributor_stats_handler(contributor_name: str) -> SpeakerStats:
    """
    GET /nodes/contributor/{contributor_name}/stats

    Get comprehensive statistics for a specific contributor.

    Args:
        contributor_name: Contributor identifier

    Returns:
        SpeakerStats with credibility and innovation metrics

    Raises:
        HTTPException: 404 if contributor not found, 500 otherwise
    """
    try:
        logger.info(f"Calculating stats for contributor: {contributor_name}")

        # Get all nodes
        all_nodes = await get_all_nodes()

        # Check if contributor exists
        all_contributors = set()
        for node in all_nodes:
            all_contributors.update(node.contributors)

        if contributor_name not in all_contributors:
            raise HTTPException(
                status_code=404,
                detail=f"Contributor not found: {contributor_name}"
            )

        # Calculate contributor stats
        stats = calculate_contributor_stats(contributor_name, all_nodes)

        logger.info(
            f"Contributor stats calculated: {contributor_name} - "
            f"Score: {stats.overall_score:.3f}, "
            f"Credibility: {stats.credibility.overall_credibility:.3f}, "
            f"Innovation: {stats.innovation.overall_innovation:.3f}"
        )

        return stats

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Failed to calculate contributor stats: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


async def get_contributors_leaderboard_handler(limit: int = 10) -> dict:
    """
    GET /nodes/leaderboard

    Get ranked list of top contributors.

    Args:
        limit: Number of top contributors to return (default 10)

    Returns:
        Dict with contributors array and total count

    Raises:
        HTTPException: 500 on error
    """
    try:
        logger.info(f"Generating leaderboard (limit: {limit})")

        # Get all nodes
        all_nodes = await get_all_nodes()

        # Get all unique contributors
        all_contributors = set()
        for node in all_nodes:
            all_contributors.update(node.contributors)

        # Calculate stats for all contributors
        contributor_stats_list = [
            calculate_contributor_stats(contributor, all_nodes)
            for contributor in all_contributors
        ]

        # Sort by overall score
        contributor_stats_list.sort(key=lambda s: s.overall_score, reverse=True)

        # Assign ranks
        for i, stats in enumerate(contributor_stats_list, 1):
            stats.rank = i

        # Convert to rankings with badges
        rankings = []
        for stats in contributor_stats_list[:limit]:
            # Assign badges
            badge = None
            if stats.credibility.influence_score > 0.7:
                badge = "thought_leader"
            elif stats.innovation.novelty_score > 0.7:
                badge = "innovator"
            elif stats.credibility.engagement_depth > 0.7:
                badge = "mediator"
            elif stats.innovation.catalyst_score > 0.7:
                badge = "catalyst"

            rankings.append(SpeakerRanking(
                rank=stats.rank,
                speaker_name=stats.speaker_name,
                overall_score=stats.overall_score,
                credibility_score=stats.credibility.overall_credibility,
                innovation_score=stats.innovation.overall_innovation,
                total_contributions=stats.total_contributions,
                badge=badge,
            ))

        logger.info(f"Leaderboard generated with {len(rankings)} contributors")

        return {
            "contributors": rankings,
            "total": len(all_contributors),
        }

    except Exception as error:
        logger.error(f"Failed to generate leaderboard: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


async def get_nodes_analysis_handler() -> dict:
    """
    GET /nodes/analysis

    Get analysis of all nodes.

    Returns:
        Dict with node stats arrays

    Raises:
        HTTPException: 500 on error
    """
    try:
        logger.info("Analyzing nodes")

        # Get all nodes
        all_nodes = await get_all_nodes()

        # Calculate node stats for all nodes
        node_stats_list = [
            calculate_node_topic_stats(node, all_nodes)
            for node in all_nodes
        ]

        # Sort by importance
        node_stats_list.sort(key=lambda t: t.importance_score, reverse=True)

        # Assign ranks
        for i, stats in enumerate(node_stats_list, 1):
            stats.rank = i

        # Categorize nodes
        top_nodes = node_stats_list[:10]

        high_engagement_nodes = sorted(
            node_stats_list,
            key=lambda t: t.health.controversy_score,
            reverse=True
        )[:10]

        active_nodes = sorted(
            node_stats_list,
            key=lambda t: t.health.evolution_velocity,
            reverse=True
        )[:10]

        creative_nodes = sorted(
            all_nodes,
            key=lambda n: n.creativity_score,
            reverse=True
        )[:10]
        creative_node_stats = [calculate_node_topic_stats(node, all_nodes) for node in creative_nodes]

        diverse_nodes = sorted(
            node_stats_list,
            key=lambda t: len(t.speakers),
            reverse=True
        )[:10]

        logger.info(f"Node analysis completed for {len(all_nodes)} nodes")

        return {
            "total_nodes": len(all_nodes),
            "top_nodes": top_nodes,
            "high_engagement_nodes": high_engagement_nodes,
            "active_nodes": active_nodes,
            "creative_nodes": creative_node_stats,
            "diverse_nodes": diverse_nodes,
        }

    except Exception as error:
        logger.error(f"Failed to analyze nodes: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


async def get_node_conclusion_handler() -> DebateConclusion:
    """
    GET /nodes/conclusion

    Generate comprehensive conclusion for the node graph.

    Returns:
        DebateConclusion with full analysis

    Raises:
        HTTPException: 500 on error
    """
    try:
        logger.info("Generating node graph conclusion")

        # Get all nodes
        all_nodes = await get_all_nodes()

        # Generate conclusion
        conclusion = generate_node_conclusion(all_nodes)

        logger.info(
            f"Node conclusion generated: "
            f"{conclusion.total_nodes} nodes, "
            f"{conclusion.unique_speakers} contributors, "
            f"quality: {conclusion.overall_quality_score:.3f}"
        )

        return conclusion

    except Exception as error:
        logger.error(f"Failed to generate node conclusion: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


async def get_node_ai_analysis_handler() -> dict:
    """
    GET /nodes/ai-analysis

    Generate AI-powered node graph analysis with insights and recommendations.

    Uses Snowflake Cortex LLM to analyze the entire knowledge graph and provide:
    - Comprehensive summary
    - Key insights
    - Best stance/framework recommendation
    - Creative ideas and synthesis
    - Strongest/weakest arguments
    - Emerging patterns
    - Actionable recommendations

    Returns:
        Dict with AI-generated analysis

    Raises:
        HTTPException: 500 on error
    """
    try:
        logger.info("Starting AI-powered node graph analysis")

        # Get all nodes
        all_nodes = await get_all_nodes()

        if not all_nodes:
            raise HTTPException(
                status_code=404,
                detail="No nodes found for analysis"
            )

        # Generate AI analysis
        analysis = analyze_nodes_with_ai(all_nodes)

        # Add metadata
        analysis["metadata"] = {
            "total_nodes": len(all_nodes),
            "unique_contributors": len(set(
                contributor
                for node in all_nodes
                for contributor in node.contributors
            )),
            "total_evolutions": sum(node.merge_count for node in all_nodes),
            "average_creativity": sum(node.creativity_score for node in all_nodes) / len(all_nodes),
            "analysis_model": "llama3.1-70b",
        }

        logger.info("AI-powered node analysis completed successfully")

        return analysis

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Failed to generate AI analysis: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(error)}"
        )


async def get_node_stats_handler() -> dict:
    """
    GET /nodes/stats

    Get node graph statistics.

    Returns:
        Dict with stats

    Raises:
        HTTPException: 500 on error
    """
    try:
        all_nodes = await get_all_nodes()

        total_evolutions = sum(node.merge_count for node in all_nodes)
        all_contributors = set()
        for node in all_nodes:
            all_contributors.update(node.contributors)

        # Calculate average creativity
        avg_creativity = sum(node.creativity_score for node in all_nodes) / len(all_nodes) if all_nodes else 0

        return {
            "total_nodes": len(all_nodes),
            "total_evolutions": total_evolutions,
            "unique_contributors": len(all_contributors),
            "contributors": list(all_contributors),
            "avg_evolutions_per_node": (
                total_evolutions / len(all_nodes) if all_nodes else 0
            ),
            "avg_creativity_score": round(avg_creativity, 4),
        }

    except Exception as error:
        logger.error(f"Failed to fetch node stats: {error}")
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
