from src.ai_insights.infrastructure.adapters.llm.api_service import ApiService

# Remember to set brawl api token

if __name__ == "__main__":
    api = ApiService(game='brawl', user_id='%239JVU8RC')
    api.get_ai_insights()

    