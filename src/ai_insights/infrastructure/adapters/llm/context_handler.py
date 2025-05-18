import os
import requests
import json
import glob
from dotenv import load_dotenv

load_dotenv(override=True)

import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime, timezone
from urllib.parse import quote

from src.ai_insights.infrastructure.adapters.llm.ssem_embedder import SSEMEmbedder
from src.ai_insights.infrastructure.adapters.llm.rag import RAGRetriever

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

    def __init__(self, game=None, user_id=None, base_data_path: str = 'data', rag_enabled: bool = True):
        self.user_id = user_id
        
        abs_base_data_path = os.path.abspath(base_data_path)
        self.raw_data_path = os.path.join(abs_base_data_path, 'raw') # For legacy fallback
        self.processed_data_path = os.path.join(abs_base_data_path, 'processed')
        self.rag_indexes_dir = os.path.join(self.processed_data_path, 'rag_indexes') # Standardized

        self.mappings = {"brawlstars": "brawl", "clashroyale": "royale"}
        self.game_suffix = self.mappings.get(str(game).lower(), str(game).lower())

        self.rag_enabled = rag_enabled
        self.embedder = None
        self.rag_retriever = None

        if self.rag_enabled:
            print(f"ContextHandler: RAG Mode Enabled for game '{self.game_suffix}'. Initializing...")
            try:
                # Assuming SSEMEmbedder uses 'all-MiniLM-L6-v2' by default or takes model name
                self.embedder = SSEMEmbedder() # Ensure consistent model
                self.rag_retriever = RAGRetriever(
                    game_suffix=self.game_suffix,
                    base_rag_index_path=self.rag_indexes_dir,
                    embedder=self.embedder
                )
                if self.rag_retriever.index is None or self.rag_retriever.index.ntotal == 0 : # Check if RAGRetriever failed to load
                    print("ContextHandler: RAGRetriever failed to load index. Disabling RAG for this session.")
                    self.rag_enabled = False

            except Exception as e:
                print(f"ContextHandler: Error initializing RAG components: {e}. Disabling RAG.")
                self.rag_enabled = False
        
        print(f"ContextHandler initialized. Game: '{self.game_suffix}', User: '{self.user_id}', RAG Active: {self.rag_enabled and bool(self.rag_retriever and self.rag_retriever.index and self.rag_retriever.index.ntotal > 0)}")

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

    def _load_json_file(self, file_path: str) -> any: # Keep for legacy or direct loads
        if not os.path.exists(file_path): return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
        except Exception as e: print(f"Warning: Error loading {file_path}: {e}"); return None


    def _get_legacy_data_fallback(self) -> list:
        """Loads all data if RAG is disabled or fails (simplified)."""

        print("ContextHandler: Loading data using legacy method (all files as fallback)...")
        aggregated_community_items = []
        if not os.path.isdir(self.raw_data_path):
            print(
                f"Warning: Raw data path does not exist or is not a directory: {self.raw_data_path}"
            )
            return []  # Return empty list if path is invalid

        print(self.raw_data_path)

        pattern = os.path.join(self.raw_data_path, f"*_{self.game_suffix}.json")
        file_paths = glob.glob(pattern)
        print(f"Found community files: {file_paths}")

        for file_path in file_paths:
            content = self._load_json_file(file_path)
            aggregated_community_items.append(content)
        print(
            f"Total community items loaded from '_brawl' files: {len(aggregated_community_items)}"
        )
        return aggregated_community_items
    
    def _derive_performance_summary(self, battlelog_data: dict, player_api_tag: str) -> str:
        # ... (implementation from previous response, ensure it's robust) ...
        if not battlelog_data or not battlelog_data.get("items"): return "No recent battle data."
        items = battlelog_data["items"]
        summary_parts = []
        for i, battle_event in enumerate(items):
            battle = battle_event.get("battle", {})
            mode = battle.get("mode", "N/A")
            result = battle.get("result", "N/A")
            b_name = "N/A"
            # Try to find player's brawler
            if battle.get("teams"):
                for team in battle["teams"]:
                    for p_in_team in team:
                        if p_in_team.get("tag") == player_api_tag:
                            b_name = p_in_team.get("brawler", {}).get("name", "N/A")
                            break
                    if b_name != "N/A": break
            elif battle.get("players"): # Solo modes
                p_entry = next((p for p in battle["players"] if p.get("tag") == player_api_tag), None)
                if p_entry: b_name = p_entry.get("brawler", {}).get("name", "N/A")
            summary_parts.append(f"{mode} ({result}) w/ {b_name}")
        return "; ".join(summary_parts) if summary_parts else "Could not summarize battlelog."


    # def context_for_llm(self) -> dict:
    #     if self.game == "brawl":
    #         player_data, battle_logs = self._brawlstars_get()

    #     if self.game == "royale":
    #         # TODO clash royale api
    #         pass

    #     community_data = self._load_and_aggregate_community_data()

    #     context = {
    #         "player_data": [player_data],
    #         "battle_logs": [battle_logs],
    #         "community_data": community_data,
    #     }

    #     return context



    def context_for_llm(self, task_types: list) -> dict:
        if self.game_suffix == "brawl": # Assuming self.game_suffix is 'brawl' or 'royale'
            profile_api_data, battlelog_api_data = self._brawlstars_get()
        
        if not profile_api_data:
            print(f"Critical: Could not fetch player profile for {self.user_id}. Aborting.")
            return {}

        player_api_tag = profile_api_data.get("tag", "") # Usually includes '#'
        player_context_live = {
            "username": profile_api_data.get("name", "N/A"),
            "trophies": profile_api_data.get("trophies", 0),
            "highestTrophies": profile_api_data.get("highestTrophies", 0),
            "xpLevel": profile_api_data.get("expLevel", 0),
            "clubName": (profile_api_data.get("club", {}) or {}).get("name", "No Club"),
            "primaryBrawlers": [ # Top 5 brawlers by trophies
                {"name": b.get("name"), "trophies": b.get("trophies"), "power": b.get("power")}
                for b in sorted(profile_api_data.get("brawlers", []), key=lambda x: x.get("trophies", 0), reverse=True)[:5]
            ],
            "recentPerformanceSummary": self._derive_performance_summary(battlelog_api_data, player_api_tag),
            "identifiedPlayStyle": [] # Placeholder - requires inference logic
        }

        retrieved_community_for_prompt = []
        retrieved_characters_for_prompt = []
        retrieved_meta_for_prompt = {}
        retrieved_creators_for_prompt = []
        rag_actually_used = False

        if self.rag_enabled and self.rag_retriever:
            query_parts = [
                f"Player: {player_context_live['username']}, Trophies: {player_context_live['trophies']}.",
                f"Primary Brawlers: {', '.join(b['name'] for b in player_context_live['primaryBrawlers'])}.",
                f"Requested insights: {', '.join(task_types)} for game {self.game_suffix}."
            ]
            rag_query = " ".join(query_parts)
            
            # Retrieve more items initially, then filter/categorize
            # The items returned by retrieve are the original_content dicts from metadata
            retrieved_items_from_rag = self.rag_retriever.retrieve(rag_query, top_k=100) 
            rag_actually_used = bool(retrieved_items_from_rag) 

            for item_dict in retrieved_items_from_rag:
                data_type = "unknown" # Default
                if "role" in item_dict and "rarity" in item_dict: data_type = "character_info"
                elif "dominantBrawlers" in item_dict or "gameVersion" in item_dict: data_type = "meta_info"
                elif "platform" in item_dict and "styleFocus" in item_dict: data_type = "creator_info"
                elif "summary" in item_dict and "topic" in item_dict: data_type = f"community_{self.game_suffix}"
                
                if data_type.startswith("community"): retrieved_community_for_prompt.append(item_dict)
                elif data_type == "character_info": retrieved_characters_for_prompt.append(item_dict)
                elif data_type == "meta_info" and not retrieved_meta_for_prompt: retrieved_meta_for_prompt = item_dict # take first/best
                elif data_type == "creator_info": retrieved_creators_for_prompt.append(item_dict)
            
            print(f"ContextHandler RAG: Community({len(retrieved_community_for_prompt)}), Chars({len(retrieved_characters_for_prompt)}), Meta({1 if retrieved_meta_for_prompt else 0}), Creators({len(retrieved_creators_for_prompt)})")


        # Fallback logic if RAG didn't fetch enough or is disabled
        if not rag_actually_used:
            if rag_actually_used: print("ContextHandler: RAG results were sparse, augmenting with legacy data.")
            else: print("ContextHandler: RAG disabled or failed, using legacy data loading.")
            
            legacy_data = self._get_legacy_data_fallback()
            if not retrieved_community_for_prompt: retrieved_community_for_prompt = legacy_data["community_items"]
            if not retrieved_characters_for_prompt: retrieved_characters_for_prompt = legacy_data["character_items"]
            if not retrieved_meta_for_prompt: retrieved_meta_for_prompt = legacy_data["meta_item"]
            if "creator_lookalike" in task_types and not retrieved_creators_for_prompt:
                retrieved_creators_for_prompt = legacy_data["creator_items"]
        
        # Prepare final context pieces with limits
        final_community_context = [
            {"source": item.get("source_file", item.get("source", "N/A")), 
             "topic": item.get("topic", item.get("title", "N/A")),
             "summary": item.get("summary", str(item)[:200])}
            for item in retrieved_community_for_prompt[:7] # Limit
        ]
        final_character_data = retrieved_characters_for_prompt[:10] # Limit
        final_meta_data = retrieved_meta_for_prompt
        final_creator_data = retrieved_creators_for_prompt[:5]


        final_llm_context = {
            "meta": {"timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                     "targetPlayerId": self.user_id, "game": self.game_suffix, "rag_active": rag_actually_used},
            "playerContext": player_context_live,
            "gameContext": {
                "currentMetaSummary": final_meta_data.get("summary", "N/A"),
                "dominantBrawlersInMeta": final_meta_data.get("dominantBrawlers", []),
                "weakBrawlersInMeta": final_meta_data.get("weakBrawlers", []),
                "characterData": final_character_data, # Now RAG-influenced or all
                "activeEvents": final_meta_data.get("activeEvents", [])
            },
            "communityContext": final_community_context,
            "tasks": task_types # Pass original task_types through
        }

        if "creator_lookalike" in task_types:
            final_llm_context["creatorProfilesForMatching"] = [
                {"creatorName": c.get("creatorName"), "platform": c.get("platform"), 
                 "styleFocus": c.get("styleFocus"), "mainBrawlers": c.get("mainBrawlers")}
                for c in final_creator_data
            ]

        context = {
            'player_data': profile_api_data,
            'battle_logs':  battlelog_api_data,
            'community_data': final_llm_context
        }

        return context