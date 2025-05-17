from abc import ABC, abstractmethod


class LLMService(ABC):
    """
    Abstract base class for interacting with a Large Language Model (LLM).
    """

    @abstractmethod
    def generate_response(self):
        """
        Generates a response from the LLM based on the provided prompt.
        """
        pass
