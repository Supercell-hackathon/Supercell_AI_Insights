from abc import ABC, abstractmethod


class Repository(ABC):
    """
    Abstract base class for a repository.
    """

    @abstractmethod
    def write(self, data):
        """
        Writes data to the repository.
        """
        pass
