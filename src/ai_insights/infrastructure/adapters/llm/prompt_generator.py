import json

PLAYER_DESCRIPTION_PROMPT='''         
    Provide expert Brawl Stars advice.
    
    --- Requested Tasks ---
    Create player description, provide an engaging narrative (2-3 sentences) and a catchy title.

    --- Player Data ---
    {player_data}

    --- Response Format ---
    Please provide your entire response as a single JSON object.
    Example structure for performance summary: {{'player description': content}}'''

PERFORMANCE_SUMMARY_PROMPT='''         
    Provide expert Brawl Stars advice.
    
    --- Requested Tasks ---
    Create a recent performance summary for the player using their recent battle logs and player description

    --- Player Description ---
    {player_description}

    --- Player Battlelog ---
    {battle_logs}

    --- Response Format ---
    Please provide your entire response as a single JSON object.
    Example structure for performance summary: {{'player description': content}}'''

RECOMMENDATIONS_PROMPT='''         
    Provide expert Brawl Stars advice.
    
    --- Requested Tasks ---
    Make 3 concise recommendations for the player using their description, recent battle logs and community data.
    Take into account the player playing style, recent balance changes and current meta, to help the player win.
    For each recommendation, provide: brawler name, detailed reasoning, 
    suggested game modes, 1 concise tip, and a confidence score

    --- Player Description ---
    {player_description}

    --- Performance Summary ---
    {performance_summary}

    --- Community Data ---"
    {community_data}

    --- Response Format ---
    Please provide your entire response as a single JSON object.
    Example structure for performance summary: {{'player description': content}}'''


class PromptGenerator:
    def __init__(self):
        """
        Initializes the Prompt Generator.
        """
        pass
                       

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
            player_data_str = str(context['player_data'])
            return PLAYER_DESCRIPTION_PROMPT.format(player_data=player_data_str)
        
        elif requested_task=='performance_summary':
            battle_logs_str = str(context['battle_logs'])
            return PERFORMANCE_SUMMARY_PROMPT.format(player_description=context['player_description'],
                                                   battle_logs=battle_logs_str) 

        elif requested_task=='recommendations':
            community_data_str = str(context['community_data'])
            return RECOMMENDATIONS_PROMPT.format(player_description=context['player_description'],
                                                performance_summary=context["performance_summary"],
                                                community_data=community_data_str)

        else:
            return 'Invalid task'
