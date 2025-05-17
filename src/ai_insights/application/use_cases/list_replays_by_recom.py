"""Module for getting replays based on a recommendation.

This module contains the function to retrieve replays from a repository
based on a recommendation. It fetches data from a game's API (e.g., Brawl Stars),
processes it, and then fetches the relevant replays from a repository.
"""

from src.ai_insights.application.dtos.replay import ReplayDTO
from src.ai_insights.application.ports.repository import Repository
from src.ai_insights.application.ports.game_api_client import GameAPIClient


def list_replays_by_recom(
    request: str,
    game_api_client: GameAPIClient,
    replays_repo: Repository,
):
    """
    Lists replays based on a recommendation.

    The recommendation has an associated character. The function first fetches
    data from the game's API (e.g., Brawl Stars) using the provided game_api_client
    and the specific request, containing the recommendation.
    Then it retrieves the relevant replays from the
    replays repository. The relevant replays are those that match the character
    associated with the recommendation and the recommendation's description.
    """
    api_response = game_api_client.get(request)
    relevant_replays = replays_repo.get(filters=api_response)
    # build replay DTOs
    replay_dtos = [
        ReplayDTO(
            id=replay["id"],
            title=replay["title"],
            character_id=replay["character_id"],
            replay_description=replay["replay_description"],
            embedding=replay["embedding"],
            video_path=replay["video_path"],
        )
        for replay in relevant_replays
    ]

    return replay_dtos
