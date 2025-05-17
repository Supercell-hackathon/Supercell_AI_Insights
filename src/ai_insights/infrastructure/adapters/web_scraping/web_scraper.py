#!/usr/bin/env python3
import os
import json
import re
import time
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup

# --- DTOs para datos de brawler ---
@dataclass
class BrawlerStatDTO:
    level: int
    health: str
    damage: str
    movement_speed: str
    reload_speed: str
    attack_range: str
    super_range: str
    super_damage: str
    super_charge_rate: str
    number_of_attacks: str
    super_refills: str
    speed_boost: Optional[str] = None
    damage_boost: Optional[str] = None
    shield_boost: Optional[str] = None

@dataclass
class GadgetDTO:
    name: str
    description: str
    image_url: Optional[str] = None

@dataclass
class StarPowerDTO:
    name: str
    description: str
    image_url: Optional[str] = None

@dataclass
class GearDTO:
    name: str
    description: str
    image_url: Optional[str] = None

@dataclass
class BrawlerDTO:
    id: str
    name: str
    url: str
    stats: BrawlerStatDTO
    best_build: str
    gadgets: List[GadgetDTO]
    star_powers: List[StarPowerDTO]
    gears: List[GearDTO]
    description: str
    image_url: Optional[str] = None

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

    def fetch_stats(self, soup: BeautifulSoup) -> BrawlerStatDTO:
        lvl_text = soup.find(text=re.compile(r'AT LVL', re.I)) or ''
        lvl_match = re.search(r'LVL\s*(\d+)', lvl_text)
        level = int(lvl_match.group(1)) if lvl_match else 1
        stats_map: Dict[str, str] = {}
        for block in soup.select('.elementor-widget'):
            title = safe_text(block.select_one('.elementor-heading-title'))
            val = safe_text(block.select_one('.elementor-widget-container .elementor-heading-title.elementor-size-large'))
            if title and val:
                stats_map[title] = val
        return BrawlerStatDTO(
            level=level,
            health=stats_map.get('HP',''),
            damage=stats_map.get('Max Dmg',''),
            movement_speed=stats_map.get('Movement Speed',''),
            reload_speed=stats_map.get('Reload Speed',''),
            attack_range=stats_map.get('Range',''),
            super_range=stats_map.get('Super Range',''),
            super_damage=stats_map.get('Super/Rng MG',''),
            super_charge_rate=stats_map.get('Super Charge Rate',''),
            number_of_attacks=stats_map.get('Number of Attack',''),
            super_refills=stats_map.get('Super Refills',''),
            speed_boost=stats_map.get('+Speed',''),
            damage_boost=stats_map.get('+Damage',''),
            shield_boost=stats_map.get('+Shield','')
        )

    def fetch_best_build(self, soup: BeautifulSoup) -> str:
        txt = soup.select_one('.elementor-widget-text-editor .elementor-widget-container')
        return safe_text(txt)

    def fetch_section_items(self, soup: BeautifulSoup, header_re: str, dto_cls) -> List:
        items = []
        hdr = soup.find(text=re.compile(header_re, re.I))
        if hdr:
            parent = hdr.find_parent()
            if parent:
                for section in parent.find_all_next('div', class_='elementor-widget-container'):
                    name_el = section.select_one('h3, strong, .elementor-heading-title')
                    desc_el = section.select_one('p, .elementor-text-editor')
                    img = section.select_one('img')
                    if name_el and desc_el:
                        items.append(dto_cls(
                            name=safe_text(name_el),
                            description=safe_text(desc_el),
                            image_url=img['src'] if img and img.has_attr('src') else None
                        ))
                        # stop after first two for gadgets/powers or five for gears by caller
                        if len(items) >= (2 if dto_cls in [GadgetDTO, StarPowerDTO] else 5):
                            break
        return items

    def fetch_brawler(self, url: str) -> Optional[BrawlerDTO]:
        try:
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            b_id = url.rstrip('/').split('/')[-1].replace('-brawl-stars','')
            name = safe_text(soup.select_one('h1.entry-title'))
            image_el = soup.select_one('img[alt*="portrait"]')
            image_url = image_el['src'] if image_el and image_el.has_attr('src') else None
            stats = self.fetch_stats(soup)
            best = self.fetch_best_build(soup)
            gadgets = self.fetch_section_items(soup, r'GADGET', GadgetDTO)
            stars = self.fetch_section_items(soup, r'STAR POWER', StarPowerDTO)
            gears = self.fetch_section_items(soup, r'GEAR', GearDTO)
            desc_el = soup.select_one('.elementor-text-editor p')
            description = safe_text(desc_el)
            return BrawlerDTO(
                id=b_id,
                name=name,
                url=url,
                stats=stats,
                best_build=best,
                gadgets=gadgets,
                star_powers=stars,
                gears=gears,
                description=description,
                image_url=image_url
            )
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def fetch_all(self) -> List[BrawlerDTO]:
        results: List[BrawlerDTO] = []
        for url in self.get_all_urls():
            b = self.fetch_brawler(url)
            if b:
                results.append(b)
                print(f"Scraped {b.name or b.id}")
            time.sleep(0.5)
        return results

# --- JSON loader ---
# --- JSON loader ---
from dataclasses import asdict

class JSONDataLoader:
    def __init__(self, output_path: str):
        self.output_path = output_path

    def write(self, data: List[BrawlerDTO]):
        # Convert nested dataclasses to dictionaries
        serializable = [asdict(d) for d in data]
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)

    def load(self) -> List[BrawlerDTO]:
        return []

# --- Main ---
if __name__ == '__main__':
    OUT = os.path.join(os.path.dirname(__file__), 'data/raw/brawlhub_brawlers.json')
    fetcher = BrawlHubFetcher()
    loader = JSONDataLoader(output_path=OUT)
    data = fetcher.fetch_all()
    loader.write(data)
    print(f"Finished: {len(data)} brawlers scraped.")
