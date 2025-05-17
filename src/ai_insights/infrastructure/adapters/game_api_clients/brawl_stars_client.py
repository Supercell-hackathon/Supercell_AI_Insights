import os
import requests

from typing import Any, Dict, Optional
from dotenv import load_dotenv

from src.ai_insights.application.ports.game_api_client import GameAPIClient


class BrawlStarsClient(GameAPIClient):
    """
    Brawl Stars API client for fetching game data.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def get(self, endpoint: str) -> Dict[str, Any]:
        """
        Sends a request to the Brawl Stars API and returns the response.
        """
        token = self.api_key
        if not token:
            raise RuntimeError("BRAWL_STARS_API_KEY not set in environment")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "ColabBrawlClient/1.0",
        }
        resp = requests.get("https://api.brawlstars.com" + endpoint, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def retrieve_data(self, data: Dict, filters: Any) -> Dict:
        """
        Retrieves specific data from the response of the Brawl Stars API.
        """
        filtered_data = data.copy()
        if "items" in filters:
            filtered_data = data["items"]
        print(filtered_data)
        if "tag" in filters:
            filtered_data = [player["tag"] for player in filtered_data]
        return {"ids": filtered_data}
