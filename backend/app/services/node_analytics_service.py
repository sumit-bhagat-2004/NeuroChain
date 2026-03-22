"""
Node analytics service — Calculate credibility, innovation, and topic strength for nodes.
"""

from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import math

from app.models.node import GraphNode, ThoughtEvolution
from app.models.debate_analytics import (
    SpeakerStats,
    SpeakerCredibilityMetrics,
    SpeakerInnovationMetrics,
    TopicStats,
    TopicDebateHealth,
    TopicDominance,
    DebateConclusion,
    DebateTrend,
    SpeakerRanking,
)
from app.utils.logger import logger


# Weights for scoring algorithms
CREDIBILITY_WEIGHTS = {
    "consistency": 0.25,
    "quality": 0.30,
    "influence": 0.25,
    "engagement": 0.20,
}

INNOVATION_WEIGHTS = {
    "novelty": 0.30,
    "creativity": 0.35,
    "diversity": 0.20,
    "catalyst": 0.15,
}


def calculate_contributor_credibility(
    contributor: str,
    all_nodes: List[GraphNode],
    contributor_contribution_map: Dict[str, List[GraphNode]],
) -> SpeakerCredibilityMetrics:
    """
    Calculate credibility metrics for a contributor.

    Args:
        contributor: Contributor identifier
        all_nodes: All graph nodes
        contributor_contribution_map: Map of contributor -> nodes they contributed to

    Returns:
        SpeakerCredibilityMetrics
    """
    nodes_contributed = contributor_contribution_map.get(contributor, [])

    if not nodes_contributed:
        return SpeakerCredibilityMetrics(
            consistency_score=0.0,
            quality_score=0.0,
            influence_score=0.0,
            engagement_depth=0.0,
            overall_credibility=0.0,
        )

    # 1. Consistency: Ratio of new nodes created vs total contributions
    new_nodes_created = sum(
        1 for node in nodes_contributed
        if node.merge_count == 0 and contributor in node.contributors
    )
    total_contributions = len(nodes_contributed)
    consistency_score = new_nodes_created / max(total_contributions, 1)

    # 2. Quality: Average creativity score of nodes they contributed to
    avg_creativity = sum(node.creativity_score for node in nodes_contributed) / len(nodes_contributed)
    quality_score = avg_creativity  # Already normalized 0-1

    # 3. Influence: How many other contributors merged into nodes this contributor initiated
    influenced_contributors = set()
    for node in nodes_contributed:
        if node.contributors and node.contributors[0] == contributor:
            influenced_contributors.update(node.contributors[1:])

    influence_score = min(len(influenced_contributors) / max(len(all_nodes), 1), 1.0)

    # 4. Engagement depth: Average merge count of topics they engage with
    avg_merge_count = sum(node.merge_count for node in nodes_contributed) / len(nodes_contributed)
    max_merge_count = max((node.merge_count for node in all_nodes), default=1)
    engagement_depth = min(avg_merge_count / max(max_merge_count, 1), 1.0)

    # Calculate overall credibility (weighted average)
    overall_credibility = (
        CREDIBILITY_WEIGHTS["consistency"] * consistency_score +
        CREDIBILITY_WEIGHTS["quality"] * quality_score +
        CREDIBILITY_WEIGHTS["influence"] * influence_score +
        CREDIBILITY_WEIGHTS["engagement"] * engagement_depth
    )

    return SpeakerCredibilityMetrics(
        consistency_score=round(consistency_score, 4),
        quality_score=round(quality_score, 4),
        influence_score=round(influence_score, 4),
        engagement_depth=round(engagement_depth, 4),
        overall_credibility=round(overall_credibility, 4),
    )


def calculate_contributor_innovation(
    contributor: str,
    all_nodes: List[GraphNode],
    contributor_contribution_map: Dict[str, List[GraphNode]],
) -> SpeakerInnovationMetrics:
    """
    Calculate innovation metrics for a contributor.

    Args:
        contributor: Contributor identifier
        all_nodes: All graph nodes
        contributor_contribution_map: Map of contributor -> nodes they contributed to

    Returns:
        SpeakerInnovationMetrics
    """
    nodes_contributed = contributor_contribution_map.get(contributor, [])

    if not nodes_contributed:
        return SpeakerInnovationMetrics(
            novelty_score=0.0,
            creativity_average=0.0,
            diversity_score=0.0,
            catalyst_score=0.0,
            overall_innovation=0.0,
        )

    # 1. Novelty: % of new nodes created
    new_nodes = sum(
        1 for node in nodes_contributed
        if node.merge_count == 0 and node.contributors and node.contributors[0] == contributor
    )
    novelty_score = new_nodes / len(nodes_contributed)

    # 2. Creativity: Average creativity score of their contributions
    creativity_scores = [node.creativity_score for node in nodes_contributed]
    creativity_average = sum(creativity_scores) / len(creativity_scores) if creativity_scores else 0.0

    # 3. Diversity: Number of unique topics engaged with
    diversity_score = len(nodes_contributed) / max(len(all_nodes), 1)

    # 4. Catalyst: How many evolutions did they trigger?
    evolutions_triggered = sum(
        sum(
            1 for evolution in node.evolution_history
            if evolution.contributor == contributor
        )
        for node in all_nodes
    )
    total_evolutions = sum(len(node.evolution_history) for node in all_nodes)
    catalyst_score = evolutions_triggered / max(total_evolutions, 1)

    # Calculate overall innovation (weighted average)
    overall_innovation = (
        INNOVATION_WEIGHTS["novelty"] * novelty_score +
        INNOVATION_WEIGHTS["creativity"] * creativity_average +
        INNOVATION_WEIGHTS["diversity"] * diversity_score +
        INNOVATION_WEIGHTS["catalyst"] * catalyst_score
    )

    return SpeakerInnovationMetrics(
        novelty_score=round(novelty_score, 4),
        creativity_average=round(creativity_average, 4),
        diversity_score=round(diversity_score, 4),
        catalyst_score=round(catalyst_score, 4),
        overall_innovation=round(overall_innovation, 4),
    )


def calculate_contributor_stats(
    contributor: str,
    all_nodes: List[GraphNode],
) -> SpeakerStats:
    """
    Calculate comprehensive statistics for a contributor.

    Args:
        contributor: Contributor identifier
        all_nodes: All graph nodes

    Returns:
        SpeakerStats with all metrics
    """
    # Build contribution map
    contributor_contribution_map = defaultdict(list)
    for node in all_nodes:
        for contrib in node.contributors:
            contributor_contribution_map[contrib].append(node)

    nodes_contributed = contributor_contribution_map.get(contributor, [])

    if not nodes_contributed:
        return SpeakerStats(
            speaker_name=contributor,
            total_contributions=0,
            nodes_created=0,
            nodes_merged=0,
            unique_topics=0,
            first_contribution=0,
            last_contribution=0,
            active_duration_minutes=0.0,
            credibility=SpeakerCredibilityMetrics(
                consistency_score=0.0,
                quality_score=0.0,
                influence_score=0.0,
                engagement_depth=0.0,
                overall_credibility=0.0,
            ),
            innovation=SpeakerInnovationMetrics(
                novelty_score=0.0,
                creativity_average=0.0,
                diversity_score=0.0,
                catalyst_score=0.0,
                overall_innovation=0.0,
            ),
            overall_score=0.0,
        )

    # Basic stats
    total_contributions = len(nodes_contributed)
    nodes_created = sum(
        1 for node in nodes_contributed
        if node.contributors and node.contributors[0] == contributor and node.merge_count == 0
    )
    nodes_merged = total_contributions - nodes_created
    unique_topics = len(nodes_contributed)

    # Time-based stats
    timestamps = []
    for node in nodes_contributed:
        timestamps.append(node.timestamp)
        # Add evolution timestamps
        for evolution in node.evolution_history:
            if evolution.contributor == contributor:
                timestamps.append(evolution.evolved_at)

    first_contribution = min(timestamps) if timestamps else 0
    last_contribution = max(timestamps) if timestamps else 0
    active_duration_minutes = (last_contribution - first_contribution) / (1000 * 60)

    # Calculate credibility and innovation
    credibility = calculate_contributor_credibility(contributor, all_nodes, contributor_contribution_map)
    innovation = calculate_contributor_innovation(contributor, all_nodes, contributor_contribution_map)

    # Overall score (50% credibility + 50% innovation)
    overall_score = (credibility.overall_credibility + innovation.overall_innovation) / 2

    return SpeakerStats(
        speaker_name=contributor,
        total_contributions=total_contributions,
        nodes_created=nodes_created,
        nodes_merged=nodes_merged,
        unique_topics=unique_topics,
        first_contribution=first_contribution,
        last_contribution=last_contribution,
        active_duration_minutes=round(active_duration_minutes, 2),
        credibility=credibility,
        innovation=innovation,
        overall_score=round(overall_score, 4),
    )


def calculate_node_topic_stats(
    node: GraphNode,
    all_nodes: List[GraphNode],
) -> TopicStats:
    """
    Calculate comprehensive statistics for a node/topic.

    Args:
        node: The graph node
        all_nodes: All graph nodes (for relative comparisons)

    Returns:
        TopicStats with health and dominance metrics
    """
    # Health metrics
    # 1. Controversy: More merges = more engagement
    max_merges = max((n.merge_count for n in all_nodes), default=1)
    controversy_score = min(node.merge_count / max(max_merges, 1), 1.0)

    # 2. Contributor diversity: More contributors = better discussion
    max_contributors = max((len(n.contributors) for n in all_nodes), default=1)
    speaker_diversity = min(len(node.contributors) / max(max_contributors, 1), 1.0)

    # 3. Evolution velocity: Merges per hour
    time_span_ms = node.last_updated - node.timestamp
    time_span_hours = max(time_span_ms / (1000 * 60 * 60), 0.01)
    evolution_velocity = node.merge_count / time_span_hours

    # 4. Engagement level: Combined metric
    engagement_level = (controversy_score + speaker_diversity) / 2

    health = TopicDebateHealth(
        controversy_score=round(controversy_score, 4),
        speaker_diversity=round(speaker_diversity, 4),
        evolution_velocity=round(evolution_velocity, 4),
        engagement_level=round(engagement_level, 4),
    )

    # Dominance metrics
    content_volume = len(node.accumulated_text or node.text)
    time_span_minutes = time_span_ms / (1000 * 60)

    dominance = TopicDominance(
        content_volume=content_volume,
        time_span_minutes=round(time_span_minutes, 2),
        merge_count=node.merge_count,
        speaker_count=len(node.contributors),
        cross_references=0,  # Would need edge data
    )

    # Overall importance (weighted combination)
    importance_score = (
        0.4 * controversy_score +
        0.3 * speaker_diversity +
        0.2 * min(content_volume / 1000, 1.0) +
        0.1 * min(evolution_velocity / 10, 1.0)
    )

    # Determine top contributor
    contributor_merge_counts = defaultdict(int)
    for contrib in node.contributors:
        contributor_merge_counts[contrib] += 1
    for evolution in node.evolution_history:
        if evolution.contributor:
            contributor_merge_counts[evolution.contributor] += 1

    top_contributor = max(contributor_merge_counts.items(), key=lambda x: x[1])[0] if contributor_merge_counts else None

    # Use full accumulated text
    preview_text = node.accumulated_text or node.text

    return TopicStats(
        node_id=node.id,
        primary_text=node.primary_text or node.text,
        preview_text=preview_text,
        health=health,
        dominance=dominance,
        speakers=node.contributors,
        top_contributor=top_contributor,
        importance_score=round(importance_score, 4),
    )


def identify_node_trends(all_nodes: List[GraphNode]) -> List[DebateTrend]:
    """
    Identify emerging trends in the node graph.

    Args:
        all_nodes: All graph nodes

    Returns:
        List of DebateTrend
    """
    trends = []

    if not all_nodes:
        return trends

    # Sort by creation time
    sorted_by_time = sorted(all_nodes, key=lambda n: n.timestamp)
    recent_nodes = sorted_by_time[-10:] if len(sorted_by_time) > 10 else sorted_by_time

    # 1. Emerging trends (recent + high velocity)
    for node in recent_nodes:
        time_span_hours = max((node.last_updated - node.timestamp) / (1000 * 60 * 60), 0.01)
        velocity = node.merge_count / time_span_hours

        if velocity > 5.0:
            trends.append(DebateTrend(
                topic_id=node.id,
                topic_preview=node.accumulated_text or node.text,
                trend_type="emerging",
                velocity=round(velocity, 2),
                speakers_involved=node.contributors,
                description=f"Rapidly evolving topic with {node.merge_count} merges from {len(node.contributors)} contributors",
            ))

    # 2. High engagement topics
    high_engagement = sorted(all_nodes, key=lambda n: n.merge_count * len(n.contributors), reverse=True)[:5]
    for node in high_engagement:
        if node.merge_count > 3 and len(node.contributors) > 2:
            trends.append(DebateTrend(
                topic_id=node.id,
                topic_preview=node.accumulated_text or node.text,
                trend_type="controversial",
                velocity=0.0,
                speakers_involved=node.contributors,
                description=f"Highly engaged topic with {node.merge_count} contributions from {len(node.contributors)} contributors",
            ))

    # 3. High creativity topics
    high_creativity = sorted(all_nodes, key=lambda n: n.creativity_score, reverse=True)[:5]
    for node in high_creativity:
        if node.creativity_score > 0.7:
            trends.append(DebateTrend(
                topic_id=node.id,
                topic_preview=node.accumulated_text or node.text,
                trend_type="emerging",
                velocity=0.0,
                speakers_involved=node.contributors,
                description=f"Highly creative topic with creativity score {node.creativity_score:.2f}",
            ))

    return trends[:10]


def generate_node_conclusion(all_nodes: List[GraphNode]) -> DebateConclusion:
    """
    Generate comprehensive conclusion for the node graph.

    Args:
        all_nodes: All graph nodes

    Returns:
        DebateConclusion with full analysis
    """
    if not all_nodes:
        return DebateConclusion(
            total_nodes=0,
            total_contributions=0,
            unique_speakers=0,
            debate_duration_minutes=0.0,
            top_speakers=[],
            top_topics=[],
            controversial_topics=[],
            trends=[],
            consensus_topics=[],
            insights=[],
            overall_quality_score=0.0,
        )

    # Summary stats
    total_nodes = len(all_nodes)
    total_contributions = sum(node.merge_count for node in all_nodes)
    all_contributors = set()
    for node in all_nodes:
        all_contributors.update(node.contributors)
    unique_speakers = len(all_contributors)

    # Duration
    all_timestamps = [node.timestamp for node in all_nodes] + [node.last_updated for node in all_nodes]
    debate_duration_minutes = (max(all_timestamps) - min(all_timestamps)) / (1000 * 60)

    # Calculate contributor stats
    contributor_stats_list = [
        calculate_contributor_stats(contributor, all_nodes)
        for contributor in all_contributors
    ]

    # Rank contributors
    contributor_stats_list.sort(key=lambda s: s.overall_score, reverse=True)
    for i, stats in enumerate(contributor_stats_list, 1):
        stats.rank = i

    # Create contributor rankings with badges
    top_speakers = []
    for stats in contributor_stats_list[:10]:
        badge = None
        if stats.credibility.influence_score > 0.7:
            badge = "thought_leader"
        elif stats.innovation.novelty_score > 0.7:
            badge = "innovator"
        elif stats.credibility.engagement_depth > 0.7:
            badge = "mediator"
        elif stats.innovation.catalyst_score > 0.7:
            badge = "catalyst"

        top_speakers.append(SpeakerRanking(
            rank=stats.rank,
            speaker_name=stats.speaker_name,
            overall_score=stats.overall_score,
            credibility_score=stats.credibility.overall_credibility,
            innovation_score=stats.innovation.overall_innovation,
            total_contributions=stats.total_contributions,
            badge=badge,
        ))

    # Calculate topic stats
    topic_stats_list = [
        calculate_node_topic_stats(node, all_nodes)
        for node in all_nodes
    ]

    # Top topics by importance
    topic_stats_list.sort(key=lambda t: t.importance_score, reverse=True)
    for i, stats in enumerate(topic_stats_list, 1):
        stats.rank = i
    top_topics = topic_stats_list[:10]

    # High engagement topics
    controversial_topics = sorted(
        topic_stats_list,
        key=lambda t: t.health.controversy_score,
        reverse=True
    )[:5]

    # High creativity topics (consensus in terms of quality)
    consensus_topics = sorted(
        all_nodes,
        key=lambda n: n.creativity_score,
        reverse=True
    )[:5]
    consensus_topic_stats = [calculate_node_topic_stats(node, all_nodes) for node in consensus_topics]

    # Identify trends
    trends = identify_node_trends(all_nodes)

    # Generate insights
    insights = []
    if top_speakers:
        insights.append(
            f"Top contributor: {top_speakers[0].speaker_name} with {top_speakers[0].total_contributions} contributions "
            f"and a {top_speakers[0].badge or 'participant'} badge"
        )
    if controversial_topics:
        insights.append(
            f"Most engaged topic: '{controversial_topics[0].primary_text[:50]}...' "
            f"with {controversial_topics[0].dominance.merge_count} merges"
        )

    # Average creativity
    avg_creativity = sum(n.creativity_score for n in all_nodes) / len(all_nodes)
    insights.append(f"Average creativity score: {avg_creativity:.2f}")

    if len(all_contributors) > 5:
        insights.append(f"Diverse participation with {unique_speakers} unique contributors")
    if total_contributions > total_nodes * 3:
        insights.append(f"Very active graph with an average of {total_contributions / total_nodes:.1f} contributions per node")

    # Overall quality score
    contributor_diversity_score = min(unique_speakers / 10, 1.0)
    avg_engagement = sum(t.health.engagement_level for t in topic_stats_list) / len(topic_stats_list)
    avg_top_credibility = sum(s.credibility_score for s in top_speakers[:3]) / min(len(top_speakers), 3) if top_speakers else 0

    overall_quality_score = (
        0.3 * contributor_diversity_score +
        0.4 * avg_engagement +
        0.3 * avg_top_credibility
    )

    return DebateConclusion(
        total_nodes=total_nodes,
        total_contributions=total_contributions,
        unique_speakers=unique_speakers,
        debate_duration_minutes=round(debate_duration_minutes, 2),
        top_speakers=top_speakers,
        top_topics=top_topics,
        controversial_topics=controversial_topics,
        trends=trends,
        consensus_topics=consensus_topic_stats,
        insights=insights,
        overall_quality_score=round(overall_quality_score, 4),
    )
