from abc import ABC, abstractmethod


class WebContentFetcher(ABC):
    """
    Abstract base class for fetching web content.
    """

    @abstractmethod
    def fetch(self):
        """
        Fetches content from a web page.
        """
        pass
