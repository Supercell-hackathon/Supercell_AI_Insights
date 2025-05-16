#!/usr/bin/env python3
import os
import json
from typing import List
from datetime import datetime, timedelta

from dateutil import tz
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from xml.etree.ElementTree import ParseError

from src.ai_insights.application.dtos.video_transcrpt import VideoTranscriptDto
from src.ai_insights.application.ports.web_content_fetcher import WebContentFetcher
from src.ai_insights.application.ports.data_loader import DataLoader
from src.ai_insights.application.use_cases.web_scraper import WebScraper


class YouTubeFetcher(WebContentFetcher):


    def __init__(self,
                 api_key: str,
                 days: int = 7,
                 max_results: int = 5,
                 languages: List[str] = ['es', 'en']):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.days = days
        self.max_results = max_results
        self.languages = languages

    def _published_after(self) -> str:
        dt = datetime.now(tz=tz.tzutc()) - timedelta(days=self.days)
        return dt.isoformat()

    def fetch(self, query: str) -> List[VideoTranscriptDto]:
        # 1) Buscar videos por query
        resp = (
            self.youtube.search()
                        .list(
                            part='snippet',
                            q=query,
                            type='video',
                            order='relevance',
                            publishedAfter=self._published_after(),
                            maxResults=self.max_results
                        )
                        .execute()
        )

        resultados: List[VideoTranscriptDto] = []
        for item in resp.get('items', []):
            vid = item['id']['videoId']
            title   = item['snippet']['title']
            creator = item['snippet']['channelTitle']

            try:
                segs = YouTubeTranscriptApi.get_transcript(vid, languages=self.languages)
                transcript = " ".join(s['text'] for s in segs)
            except (TranscriptsDisabled, NoTranscriptFound, ParseError):
                transcript = ""

            resultados.append(
                VideoTranscriptDto(
                    id=vid,
                    title=title,
                    creator=creator,
                    transcript=transcript
                )
            )

        return resultados


class JSONDataLoader(DataLoader):

    def __init__(self, output_path: str):
        self.output_path = output_path

    def write(self, data: List[VideoTranscriptDto]):
        lista = [dto.__dict__ for dto in data]
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)

    def load(self) -> List[VideoTranscriptDto]:
        if not os.path.exists(self.output_path):
            return []

        with open(self.output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return [VideoTranscriptDto(**item) for item in data]
    

if __name__ == '__main__':

    API_KEY  = 'AIzaSyDp9lF-YRQsJh2RQwN_yzOpEH3rMxq2duE'
    QUERY    = 'brawl stars meta'
    OUT_FILE = 'data/raw/weekly_videos.json'


    fetcher     = YouTubeFetcher(api_key=API_KEY, days=7, max_results=5)
    data_loader = JSONDataLoader(output_path=OUT_FILE)
    scraper     = WebScraper()           


    videos = scraper.scrape(fetcher=fetcher, data_loader=data_loader, query=QUERY)


    if(videos):
        print(f"Scraped {len(videos)} videos.")