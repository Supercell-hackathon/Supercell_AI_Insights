import os
import requests
import json
import glob
from dotenv import load_dotenv
load_dotenv(override=True)


class ContextHandler:
    def __init__(self, game=None, user_id=None):
        self.user_id = user_id
        abs_base_data_path = os.path.abspath('data')
        self.raw_data_path = os.path.join(abs_base_data_path, 'raw')
        self.processed_data_path = os.path.join(abs_base_data_path, 'processed')
        self.mappings = {'brawlstars': 'brawl',
                         'clashroyale': 'royale'}
        self.game = self.mappings.get(game,game)
    
    def _brawlstars_get(self, params: dict = None):
        token = os.getenv("BRAWLSTARS_TOKEN")
        api = os.getenv("BRAWLSTARS_API")
        headers = {
            'Authorization': f"Bearer {token}",
            'Accept': 'application/json',
            'User-Agent': 'ColabBrawlClient/1.0'
        }

        player_data = requests.get(api + f'/v1/players/{self.user_id}', headers=headers, params=params)
        battlelog = requests.get(api + f'/v1/players/{self.user_id}/battlelog', headers=headers, params=params)
        
        player_data.raise_for_status()
        battlelog.raise_for_status()

        return player_data.json(), battlelog.json()

    def _load_json_file(self, file_path: str) -> any:
        """Helper to load a single JSON file. Returns None on error."""
        if not os.path.exists(file_path):
            print(f"Warning: File not found at {file_path}")
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
            print(f"Warning: Raw data path does not exist or is not a directory: {self.raw_data_path}")
            return [] # Return empty list if path is invalid
        
        print(self.raw_data_path)

        pattern = os.path.join(self.raw_data_path, f'*_{self.game}.json')
        file_paths = glob.glob(pattern)
        print(f"Found community files: {file_paths}")

        for file_path in file_paths:
            content = self._load_json_file(file_path)
            aggregated_community_items.append(content)
        print(f"Total community items loaded from '_brawl' files: {len(aggregated_community_items)}")
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

        if self.game=="brawl":
            player_data, battle_logs = self._brawlstars_get()
        
        if self.game=="royale":
            # TODO clash royale api
            pass
  
        community_data = self._load_and_aggregate_community_data()

        context = {'player_data': [player_data],
                   'battle_logs': [battle_logs],
                   'community_data': community_data}

        return context

        


    

'''

    def _derive_performance_summary(self, battlelog_items: list, player_api_tag: str) -> str:
        """Derives a performance summary string from battlelog items."""
        if not battlelog_items:
            return "No recent battle data available."
        
        performance_summaries = []
        for i, battle_event in enumerate(battlelog_items[:5]): # Look at last 5 battles
            battle_detail = battle_event.get("battle", {})
            mode = battle_detail.get("mode", "Unknown Mode")
            result = battle_detail.get("result", "unknown_result")
            
            brawler_used_name = None
            # Try to find player's brawler in team-based modes
            if battle_detail.get("teams"):
                for team in battle_detail["teams"]:
                    for player in team:
                        if player.get("tag") == player_api_tag:
                            brawler_used_name = player.get("brawler", {}).get("name")
                            break
                    if brawler_used_name:
                        break
            # Fallback for solo modes (Showdown) or if not found above
            if not brawler_used_name and battle_detail.get("players"):
                 player_entry = next((p for p in battle_detail["players"] if p.get("tag") == player_api_tag), None)
                 if player_entry:
                     brawler_used_name = player_entry.get("brawler", {}).get("name")
            
            # If event structure contains brawler (less common for specific player result)
            if not brawler_used_name:
                brawler_used_name = battle_event.get("event", {}).get("brawlerName", "Unknown Brawler")


            performance_summaries.append(f"Battle {i+1} ({mode}): {result} with {brawler_used_name}")
        
        return "; ".join(performance_summaries) if performance_summaries else "Could not summarize recent battles."
'''
''' 
    def structure_context_for_llm(self, task_types: list) -> dict:
        """
        Fetches player data via API, loads community and general game data from files,
        and structures it for the LLM. Uses self.user_id and self.game set during init.

        Args:
            task_types (list): A list of strings indicating requested insight types.

        Returns:
            dict: The formatted context for the LLM, or empty dict if essential data is missing.
        """
        if not self.user_id or not self.game:
            print("Error: User ID or game not set in ContextHandler. Cannot structure context.")
            return {}

        # 1. Get Player-Specific Data (from API)
        api_player_data = self.get_player_data()
        if not api_player_data or api_player_data.get("profile") is None:
            print(f"Error: Failed to retrieve valid profile data for user {self.user_id}. Aborting.")
            return {}
        
        player_profile_api = api_player_data["profile"] # This is the dict from profile.json()
        battlelog_api_items = (api_player_data.get("battlelog") or {}).get("items", [])


        # 2. Load General Game Data (from files in self.processed_data_path)
        general_game_data = self._load_general_game_data()
        character_data_list = general_game_data.get("characterData", [])
        current_meta_dict = general_game_data.get("currentMeta", {})
        all_creator_list = general_game_data.get("creatorData", [])


        # 3. Load Community Data (from files in self.raw_data_path ending with _brawl.json)
        community_data_list = self._load_and_join_community_brawl_data()


        # 4. Assemble the context for the LLM
        # --- Player Context Details ---
        # Ensure player_profile_api is not None before accessing keys
        username = player_profile_api.get("name", "N/A")
        trophies = player_profile_api.get("trophies", 0)
        highest_trophies = player_profile_api.get("highestTrophies", 0)
        xp_level = player_profile_api.get("expLevel", 0) # API uses expLevel
        club_info = player_profile_api.get("club", {})
        club_name = club_info.get("name", "No Club") if isinstance(club_info, dict) else "No Club"

        api_brawlers = player_profile_api.get("brawlers", []) # List of player's brawlers
        # Sort by trophies to get "most used" or primary brawlers
        sorted_player_brawlers = sorted(api_brawlers, key=lambda b: b.get("trophies", 0), reverse=True)
        primary_brawlers_for_context = [
            {
                "name": b.get("name"),
                "level": b.get("power"), # Brawl Stars API uses 'power' for level
                "trophies": b.get("trophies"),
                "rank": b.get("rank")
            } for b in sorted_player_brawlers
        ][:5] # Top 5 brawlers by trophies

        # This needs more sophisticated logic, potentially an LLM call or NLP processing
        # on battlelog descriptions or other player data. For now, a placeholder.
        identified_play_style_tags = ["objective-focused", "versatile"] # Placeholder

        player_api_tag = player_profile_api.get("tag") # Get the player's tag for battlelog matching
        recent_performance_summary = self._derive_performance_summary(battlelog_api_items, player_api_tag)


        # --- Construct the final mcp_context dictionary ---
        mcp_context = {
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "targetPlayerId": self.user_id, # The original ID, may not include '#'
                "playerApiTag": player_api_tag, # The tag as returned by API (usually includes '#')
                "game": self.game,
                "llmInstructions": "You are an expert game coach and analyst. Analyze the provided player, game, and community data to give personalized advice for the specified tasks. Respond in JSON format with clear, actionable insights."
            },
            "playerContext": {
                "username": username,
                "trophies": trophies,
                "highestTrophies": highest_trophies,
                "xpLevel": xp_level,
                "clubName": club_name,
                "primaryBrawlers": primary_brawlers_for_context,
                "identifiedPlayStyle": identified_play_style_tags,
                "recentPerformanceSummary": recent_performance_summary,
                "allPlayerBrawlers": [ # List of all brawlers the player has unlocked
                     {"name": b.get("name"), "trophies": b.get("trophies"), "rank": b.get("rank"), "power": b.get("power")}
                     for b in api_brawlers
                ]
            },
            "gameContext": {
                "gameVersion": current_meta_dict.get("gameVersion", "N/A"), # If you store this
                "currentMetaSummary": current_meta_dict.get("summary", "General meta insights."),
                "dominantBrawlersInMeta": current_meta_dict.get("dominantBrawlers", []),
                "weakBrawlersInMeta": current_meta_dict.get("weakBrawlers", []),
                "popularCompositions": current_meta_dict.get("popularCompositions", {}),
                "characterData": character_data_list, # Full list of all characters in the game
                "activeEvents": current_meta_dict.get("activeEvents", [])
            },
            "communityContext": [
                {
                    "source": item.get("source", "community_feed"),
                    "topic": item.get("topic", "N/A"),
                    "summary": item.get("summary", "N/A"),
                    "fullText": item.get("raw_text") # Assuming your brawl files have this
                }
                for item in community_data_list
            ][:15], # Limit overall community items
            "tasks": []
        }

        # Populate tasks based on task_types
        if "character_recommendation" in task_types:
            mcp_context["tasks"].append({
                "type": "character_recommendation",
                "parameters": {
                    "recommendation_count": 3,
                    "focus": "Brawlers that synergize with the player's primary brawlers, fit their playstyle, perform well in the current meta, and cover weaknesses highlighted in their performance summary."
                }
            })
        
        if "player_description" in task_types:
            mcp_context["tasks"].append({
                "type": "player_description",
                "parameters": {
                    "tone": "insightful_and_encouraging",
                    "length": "2-3 sentences",
                    "highlight": "Key strengths based on brawler stats and trophies, and potential areas for growth based on meta and performance notes."
                }
            })

        if "creator_lookalike" in task_types:
            mcp_context["creatorProfilesForMatching"] = [
                {
                    "creatorName": c.get("creatorName"),
                    "platform": c.get("platform"),
                    "styleFocus": c.get("styleFocus"),
                    "mainBrawlers": c.get("mainBrawlers")
                } for c in all_creator_list # Use the general list loaded
            ][:10] # Limit number of creators to consider
            mcp_context["tasks"].append({
                "type": "creator_lookalike",
                "parameters": {
                    "match_count": 2,
                    "basis_for_match": "Align with player's primary brawlers, identified playstyle, and trophy range."
                }
            })
        else: # Ensure key is not present if task not requested
             mcp_context.pop("creatorProfilesForMatching", None)
             
        return mcp_context
''' 