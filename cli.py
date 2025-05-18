from src.ai_insights.infrastructure.adapters.llm.api_service import ApiService

# Remember to set brawl api token

if __name__ == "__main__":
    api = ApiService(game='brawl', user_id='%239JVU8RC')
    insights = api.get_ai_insights()

    print(insights['player_description'], '\n\n\n\n')
    print(insights['performance_summary'], '\n\n\n\n')
    print(insights['recommendations'], '\n\n\n\n')

    