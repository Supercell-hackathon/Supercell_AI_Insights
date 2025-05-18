import os
import requests
import json
import glob
from dotenv import load_dotenv

load_dotenv(override=True)


"""
from src.ai_insights.infrastructure.adapters.llm.ssem_embedder import (
    SSEMEmbedder
)


embedder = SSEMEmbedder()
my_json = "tu json en string"
list_of_jsons: List[str]
jsons_embeddings = embedder.generate_embeddings(list_of_jsons)

"""


class ContextHandler:
    def __init__(self, game=None, user_id=None):
        self.user_id = user_id
        abs_base_data_path = os.path.abspath("data")
        self.raw_data_path = os.path.join(abs_base_data_path, "raw")
        self.processed_data_path = os.path.join(abs_base_data_path, "processed")
        self.mappings = {"brawlstars": "brawl", "clashroyale": "royale"}
        self.game = self.mappings.get(game, game)

    def _brawlstars_get(self, params: dict = None):
        token = os.getenv("BRAWLSTARS_TOKEN")
        api = os.getenv("BRAWLSTARS_API")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "ColabBrawlClient/1.0",
        }

        player_data = requests.get(
            api + f"/v1/players/{self.user_id}", headers=headers, params=params
        )
        battlelog = requests.get(
            api + f"/v1/players/{self.user_id}/battlelog",
            headers=headers,
            params=params,
        )

        player_data.raise_for_status()
        battlelog.raise_for_status()

        return player_data.json(), battlelog.json()

    def _load_json_file(self, file_path: str) -> any:
        """Helper to load a single JSON file. Returns None on error."""
        if not os.path.exists(file_path):
            print(f"Warning: File not found at {file_path}")
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: Could not decode JSON from {file_path}. Error: {e}")
            return None
        except Exception as e:
            print(f"Warning: An unexpected error occurred loading {file_path}: {e}")
            return None

    def _load_and_aggregate_community_data(self) -> list:
        """
        Scans the self.raw_data_path for JSON files ending with '_{self.game}.json',
        loads them (assuming each file is a dictionary), and collects these
        dictionaries into a list.
        """
        aggregated_community_items = []
        if not os.path.isdir(self.raw_data_path):
            print(
                f"Warning: Raw data path does not exist or is not a directory: {self.raw_data_path}"
            )
            return []  # Return empty list if path is invalid

        print(self.raw_data_path)

        pattern = os.path.join(self.raw_data_path, f"*_{self.game}.json")
        file_paths = glob.glob(pattern)
        print(f"Found community files: {file_paths}")

        for file_path in file_paths:
            content = self._load_json_file(file_path)
            aggregated_community_items.append(content)
        print(
            f"Total community items loaded from '_brawl' files: {len(aggregated_community_items)}"
        )
        return aggregated_community_items

    def context_for_llm(self) -> dict:
        """
        Takes aggregated data and structures it for the LLM.

        Args:
            aggregated_player_context (dict): Data like 'player_context_for_mcp.json'.
            task_types (list): A list of strings indicating requested insight types
                               (e.g., ["character_recommendation", "player_description"]).

        Returns:
            dict: The formatted context.
        """

        if self.game == "brawl":
            player_data, battle_logs = self._brawlstars_get()

        if self.game == "royale":
            # TODO clash royale api
            pass

        community_data = self._load_and_aggregate_community_data()

        context = {
            "player_data": [player_data],
            "battle_logs": [battle_logs],
            "community_data": community_data,
        }

        return context
