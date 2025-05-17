from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class Repository(ABC):
    @abstractmethod
    def get(self, filters: Optional[Dict[str, Any]] = None):
        """
        Retrieve data, optionally filtered by specified criteria.

        Args:
            filters: Optional dictionary containing filter criteria

        Returns:
            Data retrieved from the repository, filtered by the specified criteria
        """
        pass
