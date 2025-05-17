from abc import ABC, abstractmethod
from typing import Any, Dict


class GameAPIClient(ABC):
    """
    Abstract base class for interacting with a game API.
    """

    @abstractmethod
    def get(self, endpoint: str):
        """
        Sends a request to the game API and returns the response.

        Args:
            endpoint (str): The API endpoint to send the request to.

        Returns:
            Dict: The response from the API.
        """
        pass

    @abstractmethod
    def retrieve_data(self, data: Dict, filters: Any) -> Dict:
        """
        Retrieves specific data from the responseq of the game API.

        Args:
            data (Dict): The data to retrieve.

        Returns:
            Dict: The retrieved data.
        """
        pass
