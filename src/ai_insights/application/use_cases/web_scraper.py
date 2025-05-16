from src.ai_insights.application.ports.web_content_fetcher import WebContentFetcher
from src.ai_insights.application.ports.repository import Repository


class WebScraper:
    def __init__(self):
        self.url = None

    def _fetch(self, fetcher: WebContentFetcher):
        """
        Fetches content from the web page using the provided fetcher.
        """
        return fetcher.fetch(self.url)

    def _write(self, content, repo: Repository):
        """
        Writes the scraped content to a file or database using the provided data loader.
        """
        repo.write(content)

    def scrape(
        self,
        url: str,
        repo: Repository,
        fetcher: WebContentFetcher,
    ):
        """
        Scrapes the web page using the provided fetcher and parameters.
        """
        self.url = url
        content = self._fetch(fetcher)
        self._write(content, repo)
        return content
