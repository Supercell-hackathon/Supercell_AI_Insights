from abc import ABC, abstractmethod


class DataLoader(ABC):
    """
    Abstract base class for loading data.
    """

    @abstractmethod
    def load(self):
        """
        Loads data from a source.
        """
        pass
