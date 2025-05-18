#!/usr/bin/env python3
import os
import json
import time
import requests
from typing import List, Optional
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup

# --- DTO for minimal brawler export ---
@dataclass
class BrawlerMinimalDTO:
    id: str
    url: str
    best_build: str

# --- Helper ---
def safe_text(elem) -> str:
    return elem.get_text(strip=True) if elem else ''

# --- Fetcher para BrawlHub ---
class BrawlHubFetcher:
    def __init__(self, base_url: str = "https://brawlhub.co"):
        self.base_url = base_url.rstrip('/')
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    def get_all_urls(self) -> List[str]:
        idx_url = f"{self.base_url}/brawlers-brawl-stars/"
        resp = requests.get(idx_url, headers=self.headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        urls = set()
        for a in soup.select('a[href*="/brawlers/"]'):
            href = a.get('href', '')
            if '/brawlers/' in href and '-brawl-stars' in href:
                full = href if href.startswith('http') else self.base_url + href
                urls.add(full.rstrip('/'))
        return sorted(urls)

    def fetch_best_build(self, soup: BeautifulSoup) -> str:
        txt = soup.select_one('.elementor-widget-text-editor .elementor-widget-container')
        return safe_text(txt)

    def fetch_brawler_minimal(self, url: str) -> Optional[BrawlerMinimalDTO]:
        try:
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            b_id = url.rstrip('/').split('/')[-1].replace('-brawl-stars','')
            best = self.fetch_best_build(soup)
            return BrawlerMinimalDTO(id=b_id, url=url, best_build=best)
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def fetch_all_minimal(self) -> List[BrawlerMinimalDTO]:
        results: List[BrawlerMinimalDTO] = []
        for url in self.get_all_urls():
            b = self.fetch_brawler_minimal(url)
            if b and b.best_build:
                results.append(b)
                print(f"Scraped minimal for {b.id}")
            time.sleep(0.5)
        return results

# --- JSON writer for minimal data ---
class JSONDataWriter:
    def __init__(self, output_path: str):
        self.output_path = output_path

    def write(self, data: List[BrawlerMinimalDTO]):
        serializable = [asdict(d) for d in data]
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)

# --- Main ---
if __name__ == '__main__':
    OUT = os.path.join(os.path.dirname(__file__), '../../../../../data/raw/brawlhub_minimal.json')
    fetcher = BrawlHubFetcher()
    writer = JSONDataWriter(output_path=OUT)
    data = fetcher.fetch_all_minimal()
    writer.write(data)
    print(f"Finished: {len(data)} minimal entries scraped.")
