from src.ai_insights.application.ports.web_content_fetcher import WebContentFetcher
from src.ai_insights.application.ports.data_loader import DataLoader


class WebScraper:
    def __init__(self, url: str):
        self.url = url

    def _fetch(self, fetcher: WebContentFetcher):
        """
        Fetches content from the web page using the provided fetcher.
        """
        return fetcher.fetch(self.url)

    def _write(self, data_loader: DataLoader):
        """
        Writes the scraped content to a file or database using the provided data loader.
        """

        pass

    def scrape(self, fetcher: WebContentFetcher, data_loader: DataLoader):
        """
        Scrapes the web page using the provided fetcher and parameters.
        """
        content = self._fetch(fetcher)
        self._write(data_loader)
        return content
