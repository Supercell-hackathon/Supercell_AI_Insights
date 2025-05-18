from src.ai_insights.infrastructure.adapters.llm.context_handler import ContextHandler
from src.ai_insights.infrastructure.adapters.llm.prompt_generator import PromptGenerator
from src.ai_insights.infrastructure.adapters.llm.llm_connector import LLMConnector

class ApiService:
    def __init__(self, game=None, user_id=None, llm_provider = "google", model = None):
        self.game = game
        self.user_id = user_id
        self.llm_provider = llm_provider
        self.model = model
    
    def get_ai_insights(self):
        handler = ContextHandler(game=self.game, user_id=self.user_id, rag_enabled=True)
        tasks = ["character_recommendation", "player_description", "creator_lookalike"]
        llm_ready_context = handler.context_for_llm(task_types=tasks)

        print("\n--- Final Context for LLM ---")
        if llm_ready_context:
            # print(f"\nContext generated. RAG Active reported: {llm_ready_context.get('meta', {}).get('rag_active')}")
            print(f"Number of community items in context: {len(llm_ready_context.get('communityContext', []))}")
            print(f"Number of characters in context: {len(llm_ready_context.get('gameContext', {}).get('characterData', []))}")
        else:
            print("Failed to generate context.")

        llm_connector = LLMConnector()

        prompt_generator = PromptGenerator()
        player_description_prompt = prompt_generator.generate_prompt(requested_task='player_description', context=llm_ready_context)
        llm_ready_context['player_description'] = llm_connector.get_llm_response(player_description_prompt)

        performance_summary_prompt = prompt_generator.generate_prompt(requested_task='performance_summary', context=llm_ready_context)
        llm_ready_context['performance_summary'] = llm_connector.get_llm_response(performance_summary_prompt)
 
        recommendations_prompt = prompt_generator.generate_prompt(requested_task='recommendations', context=llm_ready_context)
        llm_ready_context['recommendations'] = llm_connector.get_llm_response(recommendations_prompt)

        ai_insights = {}
        ai_insights['player_description'] = llm_ready_context['player_description']
        ai_insights['performance_summary'] = llm_ready_context['performance_summary']
        ai_insights['recommendations'] = llm_ready_context['recommendations']

        return ai_insights
