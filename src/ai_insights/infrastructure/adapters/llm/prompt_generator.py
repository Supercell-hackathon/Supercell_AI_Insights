import json

class PromptGenerator:
    def __init__(self):
        """
        Initializes the Prompt Generator.
        """
        pass

    def player_description(self, player_data: list) -> str:
        prompt_parts = []
        prompt_parts.append("Provide expert Brawl Stars advice.")
        
        prompt_parts.append("\n--- Requested Tasks ---")
        prompt_parts.append("Create player description, provide an engaging narrative (2-3 sentences) and a catchy title.")

        prompt_parts.append("\n--- Player Data ---")
        prompt_parts.append(player_data) 

        prompt_parts.append("\n--- Response Format ---")
        prompt_parts.append("Please provide your entire response as a single JSON object.")
        prompt_parts.append("Example structure for performance summary: {'player description': content}")
        
        prompt_parts = [str(element) for element in prompt_parts]

        return ''.join(prompt_parts)

    def performance_summary(self, player_description: str, battle_log: list) -> str:
        prompt_parts = []
        prompt_parts.append("Provide expert Brawl Stars advice.")
        
        prompt_parts.append("\n--- Requested Tasks ---")
        prompt_parts.append("Create a recent performance summary for the player using their recent battle logs and player description")

        prompt_parts.append("\n--- Player Description ---")
        prompt_parts.append(player_description) 

        prompt_parts.append("\n--- Player Battlelog ---")
        prompt_parts.append(battle_log) 

        prompt_parts.append("\n--- Response Format ---")
        prompt_parts.append("Please provide your entire response as a single JSON object.")
        prompt_parts.append("Example structure for performance summary: {'performance_summary': content}")

        prompt_parts = [str(element) for element in prompt_parts]
        
        return ''.join(prompt_parts)
    
    def recommendations(self, player_description: str, performance_summary: str, community_data: list) -> str:
        prompt_parts = []
        prompt_parts.append("Provide expert Brawl Stars advice.")
        
        prompt_parts.append("\n--- Requested Tasks ---")
        prompt_parts.append("Make recommendations for the player using their description, recent battle logs and community data.")
        prompt_parts.append("Take into account the player playing style, recent balance changes and current meta")
        prompt_parts.append("For (brawler/character/deck/troops/etc depending on the game) recommendations, provide: name, detailed reasoning, suggested game modes, and 1-2 concise tips for each.")

        prompt_parts.append("\n--- Player Description ---")
        prompt_parts.append(player_description) 

        prompt_parts.append("\n--- Performance Summary ---")
        prompt_parts.append(performance_summary) 

        prompt_parts.append("\n--- Community Data ---")
        prompt_parts.append(community_data) 

        prompt_parts.append("\n--- Response Format ---")
        prompt_parts.append("Please provide your entire response as a single JSON object.")
        prompt_parts.append("Example structure for performance summary: {'Recommendations': content}")

        prompt_parts = [str(element) for element in prompt_parts]
        
        return ''.join(prompt_parts)
                       

    def generate_prompt(self, context: dict, requested_task: str) -> str:
        """
        Creates an effective, task-specific prompt for the LLM from context.
        This example creates one large prompt for multiple tasks. 
        Alternatively, you might generate one prompt per task.

        Args:
            llm_input (dict): The formatted context (like 'llm_input.json').

        Returns:
            str: The text prompt to be sent to the LLM.
        """

        if requested_task=='player_description':
            return self.player_description(player_data=context['player_data'])
        
        elif requested_task=='performance_summary':
            return self.performance_summary(player_description=context["player_description"],
                                            battle_log=context["battle_logs"])

        elif requested_task=='recommendations':
            return self.recommendations(player_description=context["player_description"],
                                        performance_summary=context["performance_summary"],
                                        community_data=context["community_data"])

        else:
            return 'Invalid task'
        

# # Example Usage
# if __name__ == "__main__":
#     generator = PromptGenerator()
#     # Assume mcp_output from mcp_handler.py example is available
#     sample_mcp_data = { # Simplified from mcp_output for brevity
#         "meta": {"llmInstructions": "Be a Brawl Stars coach."},
#         "playerContext": {"username": "TestPlayer", "trophies": 100},
#         "gameContext": {"currentMetaSummary": "Aggro is in."},
#         "tasks": [
#             {"type": "character_recommendation", "parameters": {"recommendation_count": 1, "focus": "aggressive brawlers"}},
#             {"type": "player_description", "parameters": {"tone": "heroic"}}
#         ]
#     }
#     prompt = generator.generate_prompt_from_mcp(sample_mcp_data)
#     print("\nGenerated Prompt:")
#     print(prompt)
