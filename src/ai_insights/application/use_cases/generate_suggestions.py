from src.ai_insights.application.ports.llm_service import LLMService


def generate_suggestions(prompt, llm: LLMService) -> str:
    """
    Generates suggestions based on the provided prompt using the LLM service.

    Args:
        prompt (str): The input prompt for the LLM.
        llm (LLMService): An instance of a class implementing the LLMService interface.

    Returns:
        str: The generated suggestions from the LLM.
    """
    response = llm.generate_response(prompt)
    return response
