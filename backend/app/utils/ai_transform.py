"""
AI response transformation utilities — Convert AI analysis to structured format.
"""

from typing import Dict, List, Any, Union


def transform_to_sections_format(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform flat AI analysis response into nested sections format.

    Converts from:
    {
      "summary": "...",
      "key_insights": ["..."],
      ...
    }

    To:
    {
      "sections": [
        {"title": "Summary", "content": "..."},
        {"title": "Key Insights", "content": ["..."]},
        ...
      ],
      "metadata": {...}
    }

    Args:
        analysis: Flat analysis dictionary from LLM

    Returns:
        Structured sections dictionary
    """
    sections = []

    # Define section mapping (title -> key in analysis dict)
    section_mapping = [
        ("Summary", "summary"),
        ("Key Insights", "key_insights"),
        ("Best Stance", "best_stance"),
        ("Creative Ideas", "creative_ideas"),
        ("Synthesis", "synthesis"),
        ("Strongest Arguments", "strongest_arguments"),
        ("Weakest Arguments", "weakest_arguments"),
        ("Emerging Patterns", "emerging_patterns"),
        ("Recommendations", "recommendations"),
    ]

    # Build sections array
    for title, key in section_mapping:
        if key in analysis:
            sections.append({
                "title": title,
                "content": analysis[key]
            })

    # Extract metadata if present
    metadata = analysis.get("metadata", {})

    return {
        "sections": sections,
        "metadata": metadata,
    }
