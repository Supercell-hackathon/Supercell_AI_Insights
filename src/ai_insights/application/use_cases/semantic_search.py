"""Module providing semantic search functionality for recommendations and replay descriptions.

This module implements semantic search capabilities using embeddings to filter
replays based on their description's similarity with a text, which is
the recommendations made by our system. It handles:
- Similarity calculations
- Threshold-based filtering of results
"""

from typing import Dict, Any, List
from sklearn.metrics.pairwise import cosine_similarity

from src.ai_insights.application.dtos.insight_dtos import (
    RecommendedCharacterDTO,
)
from src.ai_insights.application.dtos.replay import ReplayDTO


def semantic_search(
    recommendation: RecommendedCharacterDTO,
    replays: List[ReplayDTO],
    treshold: Dict[str, Any],
) -> List[ReplayDTO]:
    """x
    Perform semantic search to find relevant replays based on the recommendation.

    Args:
        recommendation: The recommendation object containing the embedding
        replays: List of replay objects to search through
        treshold: Threshold for filtering relevant replays based on cosine similarity
    Returns:
        List of relevant replays that match the recommendation.
    """

    relevant_replays = [
        replay
        for replay in replays
        if cosine_similarity(recommendation.embedding.vector, replay.embedding.vector)
        > treshold
    ]

    return relevant_replays
