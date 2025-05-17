from context_handler import ContextHandler
from prompt_generator import PromptGenerator
from llm_connector import LLMConnector
from insight_generator import InsightGenerator

# |--- Calls ---> MCPHandler.structure_context_for_llm()
# |                 (Input: aggregated_player_context, task_types)
# |                 (Output: mcp_llm_input_data)
# |
# |--- Calls ---> PromptGenerator.generate_prompt_from_mcp()
# |                 (Input: mcp_llm_input_data)
# |                 (Output: llm_prompt_text)
# |
# |--- Calls ---> LLMConnector.send_prompt()
# |                 (Input: llm_prompt_text)
# |                 (Output: raw_llm_response_json_string)
# |
# |--- Calls ---> InsightGenerator.process_llm_output() (Orchestrator)
#                   (Input: raw_llm_response_json_string, player_id, mcp_llm_input_data["tasks"])
#                   |
#                   |--- Calls (internally) ---> CharacterRecommender.format_recommendations() (if requested)
#                   |--- Calls (internally) ---> PlayerDescriber.format_description() (if requested)
#                   |--- Calls (internally) ---> CreatorMatcher.format_matches() (if requested)
#                   |
#                   (Output: final_player_insights dictionary)


class ApiService:
    def __init__(self, game=None, user_id=None, llm_provider = "google", model = None):
        self.game = game
        self.user_id = user_id
        self.llm_provider = llm_provider
        self.model = model
    
    def get_ai_insights(self):
        handler = ContextHandler(game=self.game, user_id=self.user_id)
        context = handler.context_for_llm()

        llm_connector = LLMConnector()

        prompt_generator = PromptGenerator()
        player_description_prompt = prompt_generator.generate_prompt(requested_task='player_description', context=context)
        context['player_description'] = llm_connector.get_llm_response(player_description_prompt)

        performance_summary_prompt = prompt_generator.generate_prompt(requested_task='performance_summary', context=context)
        context['performance_summary'] = llm_connector.get_llm_response(performance_summary_prompt)
 
        recommendations_prompt = prompt_generator.generate_prompt(requested_task='recommendations', context=context)
        context['recommendations'] = llm_connector.get_llm_response(recommendations_prompt)


        print(context['player_description'])
        print(context['performance_summary'])
        print(context['recommendations'])

        return 0


if __name__ == "__main__":
    api = ApiService(game='brawl', user_id='%239JVU8RC')
    api.get_ai_insights()

    
