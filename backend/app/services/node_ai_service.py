"""
AI-powered node analysis service — Uses LLM to analyze node graph and generate insights.
"""

from typing import List, Dict
import json

from app.models.node import GraphNode
from app.services.snowflake_service import _get_connection
from app.utils.logger import logger


def analyze_nodes_with_ai(all_nodes: List[GraphNode]) -> Dict:
    """
    Use Snowflake Cortex LLM to analyze the entire node graph and provide insights.

    Args:
        all_nodes: All graph nodes

    Returns:
        Dict with AI-generated insights, best stances, and creative ideas
    """
    if not all_nodes:
        return {
            "summary": "No node data available for analysis.",
            "key_insights": [],
            "best_stance": "No stance can be determined without node data.",
            "creative_ideas": [],
            "synthesis": "No synthesis available.",
        }

    logger.info(f"Starting AI analysis of {len(all_nodes)} graph nodes")

    # Build comprehensive context
    context = _build_node_context(all_nodes)

    # Create prompt for LLM
    prompt = _build_node_analysis_prompt(context, all_nodes)

    # Call Snowflake Cortex LLM
    try:
        analysis_result = _call_cortex_llm(prompt)
        logger.info("AI analysis completed successfully")
        return analysis_result
    except Exception as error:
        logger.error(f"AI analysis failed: {error}")
        return _generate_fallback_node_analysis(all_nodes)


def _build_node_context(all_nodes: List[GraphNode]) -> str:
    """
    Build a comprehensive context string from all nodes.

    Args:
        all_nodes: All graph nodes

    Returns:
        Context string with all node content
    """
    context_parts = []

    # Add each node with its full accumulated text
    for i, node in enumerate(all_nodes, 1):
        contributors_list = ", ".join(node.contributors) if node.contributors else "Anonymous"
        context_parts.append(
            f"NODE {i}:\n"
            f"Contributors: {contributors_list}\n"
            f"Merge Count: {node.merge_count}\n"
            f"Creativity Score: {node.creativity_score:.2f}\n"
            f"Content:\n{node.accumulated_text or node.text}\n"
            f"---"
        )

    return "\n\n".join(context_parts)


def _build_node_analysis_prompt(context: str, all_nodes: List[GraphNode]) -> str:
    """
    Build the prompt for LLM analysis.

    Args:
        context: Node context string
        all_nodes: All graph nodes

    Returns:
        Formatted prompt string
    """
    # Get summary stats
    total_nodes = len(all_nodes)
    all_contributors = set()
    total_merges = 0
    avg_creativity = 0
    for node in all_nodes:
        all_contributors.update(node.contributors)
        total_merges += node.merge_count
        avg_creativity += node.creativity_score
    avg_creativity = avg_creativity / total_nodes if total_nodes > 0 else 0

    prompt = f"""You are an expert knowledge graph analyst. Analyze the following thought network with {total_nodes} nodes, {len(all_contributors)} contributors, {total_merges} total evolutions, and {avg_creativity:.2f} average creativity.

**KNOWLEDGE GRAPH CONTENT:**

{context}

**YOUR TASK:**

Provide a comprehensive analysis in JSON format with the following structure:

{{
    "summary": "A 2-3 sentence summary of the entire knowledge graph and its themes",
    "key_insights": [
        "Insight 1: Key pattern or finding from the graph",
        "Insight 2: Another important observation",
        "Insight 3: Third key insight"
    ],
    "best_stance": "Based on the evidence and ideas presented, what appears to be the most coherent position or framework? Explain your reasoning in 3-4 sentences.",
    "creative_ideas": [
        "Creative idea 1: A novel connection or synthesis not explicitly mentioned",
        "Creative idea 2: Another innovative perspective",
        "Creative idea 3: A third creative insight"
    ],
    "synthesis": "A comprehensive synthesis that connects different nodes and proposes a unified framework (3-4 sentences)",
    "strongest_arguments": [
        "Strong argument 1 from the graph",
        "Strong argument 2 from the graph"
    ],
    "weakest_arguments": [
        "Weak argument 1 that lacks support or coherence",
        "Weak argument 2 with logical flaws"
    ],
    "emerging_patterns": [
        "Pattern 1: A recurring theme or approach across nodes",
        "Pattern 2: Another observable pattern"
    ],
    "recommendations": [
        "Recommendation 1: Actionable suggestion for expanding the knowledge graph",
        "Recommendation 2: Another practical recommendation",
        "Recommendation 3: A third strategic recommendation"
    ]
}}

IMPORTANT: Return ONLY valid JSON. Do not include any text before or after the JSON object."""

    return prompt


def _call_cortex_llm(prompt: str) -> Dict:
    """
    Call Snowflake Cortex LLM to analyze the nodes.

    Args:
        prompt: The analysis prompt

    Returns:
        Dict with analysis results
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        # Use Snowflake Cortex COMPLETE function with llama3.1-70b model
        sql = """
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'llama3.1-70b',
                [
                    {
                        'role': 'system',
                        'content': 'You are an expert knowledge graph analyst. Always return valid JSON.'
                    },
                    {
                        'role': 'user',
                        'content': %(prompt)s
                    }
                ],
                {
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
            ) AS analysis
        """

        cursor.execute(sql, {'prompt': prompt})
        result = cursor.fetchone()

        if result and result[0]:
            response_text = result[0]

            # Try to extract JSON from response
            try:
                # The response might be wrapped in markdown code blocks
                if "```json" in response_text:
                    start = response_text.find("```json") + 7
                    end = response_text.find("```", start)
                    response_text = response_text[start:end].strip()
                elif "```" in response_text:
                    start = response_text.find("```") + 3
                    end = response_text.find("```", start)
                    response_text = response_text[start:end].strip()

                analysis = json.loads(response_text)
                return analysis
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                logger.error(f"Raw response: {response_text}")
                raise

        raise Exception("No response from Cortex LLM")

    except Exception as error:
        logger.error(f"Cortex LLM call failed: {error}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _generate_fallback_node_analysis(all_nodes: List[GraphNode]) -> Dict:
    """
    Generate a basic analysis when AI is unavailable.

    Args:
        all_nodes: All graph nodes

    Returns:
        Dict with fallback analysis
    """
    # Get basic stats
    all_contributors = set()
    total_merges = 0
    avg_creativity = 0
    for node in all_nodes:
        all_contributors.update(node.contributors)
        total_merges += node.merge_count
        avg_creativity += node.creativity_score
    avg_creativity = avg_creativity / len(all_nodes) if all_nodes else 0

    most_merged = max(all_nodes, key=lambda n: n.merge_count) if all_nodes else None
    most_creative = max(all_nodes, key=lambda n: n.creativity_score) if all_nodes else None

    return {
        "summary": f"Knowledge graph with {len(all_nodes)} nodes, {len(all_contributors)} contributors, and {total_merges} evolutions. Average creativity: {avg_creativity:.2f}",
        "key_insights": [
            f"Most evolved node has {most_merged.merge_count} merges" if most_merged else "No highly evolved nodes",
            f"Most creative node has creativity score {most_creative.creativity_score:.2f}" if most_creative else "No creativity data",
            f"{len(all_contributors)} unique contributors participated in the knowledge graph",
            "AI analysis temporarily unavailable - showing basic statistics only"
        ],
        "best_stance": "Unable to determine best stance without AI analysis. Please review the node content manually.",
        "creative_ideas": [
            "Consider connecting related nodes to form knowledge clusters",
            "Explore cross-pollination between high-creativity nodes",
            "Implement structured frameworks to organize the knowledge graph"
        ],
        "synthesis": "This is a fallback analysis. The full AI-powered analysis is temporarily unavailable. Please try again later or review the detailed analytics endpoints for statistical insights.",
        "strongest_arguments": ["AI analysis required to identify strongest arguments"],
        "weakest_arguments": ["AI analysis required to identify weakest arguments"],
        "emerging_patterns": ["AI analysis required to identify emerging patterns"],
        "recommendations": [
            "Use the /nodes/conclusion endpoint for statistical analysis",
            "Review individual node content for detailed insights",
            "Try the AI analysis again when the service is available"
        ]
    }
