import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "http://brawlstars.fandom.com"
CATEGORY_PAGE = "/wiki/Category:Brawlers"
OUTPUT_DIR = "/Users/danielmunoz/Desktop/Supercell_AI_Insights/data/raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "brawlers_details.json")

def scrape_brawler_links():
    resp = requests.get(BASE_URL + CATEGORY_PAGE)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    container = soup.find("div", class_="category-page__members")
    anchors = container.select("a.category-page__member-link")
    return [
        (a["title"], urljoin(BASE_URL, a["href"]))
        for a in anchors
        if not a["title"].startswith("Category:")
    ]

def scrape_brawler_details(name, url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    content = soup.find("div", class_="mw-parser-output")

    ps = [p.get_text(strip=True)
          for p in content.find_all("p")
          if p.get_text(strip=True)]
    descripcion = ps[0] if ps else ""

    tips = {}

    h2 = None
    for header in content.find_all("h2"):
        span = header.find("span", class_="mw-headline")
        if span and span.get_text(strip=True) == "Tips":
            h2 = header
            break

    if h2:
        sib = h2.next_sibling
        current = None
        while sib:
            if sib.name == "h2":
                break

            if sib.name == "h3":
                current = sib.get_text(strip=True)
                tips[current] = []

            elif sib.name == "ul" and current:
                for li in sib.find_all("li"):
                    tips[current].append(li.get_text(strip=True))

            sib = sib.next_sibling

    return {
    "name": name,
    "url": url,
    "description": descripcion or "",
    "Game Modes and Maps": tips.get("Game Modes and Maps", ""),
    "Recommended Build": tips.get("Recommended Build", ""),
    "Strategies": tips.get("Strategies", ""),
    "Other": tips.get("Other", "")
}
if __name__ == "__main__":

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    links = scrape_brawler_links()
    all_data = [scrape_brawler_details(name, url) for name, url in links]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Guardado {len(all_data)} brawlers en {OUTPUT_FILE}")