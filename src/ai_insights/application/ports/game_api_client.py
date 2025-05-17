from abc import ABC, abstractmethod


class GameAPIClient(ABC):
    """
    Abstract base class for interacting with a game API.
    """

    @abstractmethod
    def get(self):
        """
        Sends a request to the game API and returns the response.
        """
        pass
