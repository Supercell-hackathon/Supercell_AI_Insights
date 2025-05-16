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
    @abstractmethod
    def write(self, data):
        """
        Writes data to a destination.
        """
        pass
