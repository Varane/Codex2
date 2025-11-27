import csv
import json
import os
import random
import re
import string
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from catalog_manager import get_cached, get_known_oems, save_new_oem, save_scrape_result
from oem_resolver import resolve_oem

app = FastAPI(title="Part Price Aggregator")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

PRICE_REGEX = re.compile(r"\d+[\d,.]*")
OEM_PATTERN = re.compile(r"\b\d{5,12}\b")


# ----------------------------- Data loading -----------------------------

def load_json(path: str) -> Dict:
    try:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except (OSError, json.JSONDecodeError):
        return {}


def load_cars_data() -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    return load_json("cars.json")


CARS_DATA = load_cars_data()


# ----------------------------- Helpers -----------------------------

def normalize_text(value: str) -> str:
    table = str.maketrans({ch: " " for ch in string.punctuation})
    return re.sub(r"\s+", " ", value.lower().translate(table)).strip()


def parse_query_details(query: str) -> Tuple[str, str, str]:
    car = ""
    model = ""
    detail = ""
    normalized_query = normalize_text(query)

    for car_key in CARS_DATA.keys():
        if normalize_text(car_key) in normalized_query:
            car = car_key
            break

    if car:
        for model_key in CARS_DATA[car].keys():
            if normalize_text(model_key) in normalized_query:
                model = model_key
                break

    if car and model:
        systems = CARS_DATA.get(car, {}).get(model, {})
        for part_list in systems.values():
            for part in part_list:
                if normalize_text(part) in normalized_query:
                    detail = part
                    break
            if detail:
                break

    return car, model, detail


def clean_price_text(text: str) -> Optional[float]:
    if not text:
        return None
    text = text.replace("to", "-")
    matches = PRICE_REGEX.findall(text)
    if not matches:
        return None
    number_text = matches[0]
    number_text = number_text.replace(".", "").replace(",", ".")
    try:
        return float(number_text)
    except ValueError:
        return None


# ----------------------------- RRR scraper -----------------------------

class RrrScraper:
    def __init__(self) -> None:
        self.session = requests.Session()

    def _get(self, url: str) -> Optional[requests.Response]:
        for _ in range(3):
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            try:
                response = self.session.get(url, headers=headers, timeout=10)
                if response.status_code in (429, 503) or "DDOS" in response.text:
                    time.sleep(random.uniform(0.5, 1.3))
                    continue
                response.raise_for_status()
                return response
            except requests.RequestException:
                time.sleep(random.uniform(0.5, 1.3))
                continue
        return None

    def _parse_item(self, item: BeautifulSoup, base_url: str) -> Optional[Dict]:
        title_elem = item.select_one(".item-title, .title, [itemprop='name'], .part-name a, a.title")
        price_elem = item.select_one(
            ".price, .item-price, .search-item-price, span[itemprop='price']"
        )
        image_elem = item.select_one("[itemprop='image'], img")
        link_elem = item.select_one("[itemprop='url'], a[href*='autodalis'], .part-name a, a")

        price = clean_price_text(price_elem.get_text(" ", strip=True)) if price_elem else None
        if price is None:
            return None
        link_href = link_elem.get("href") if link_elem else None
        link = urljoin(base_url, link_href) if link_href else None
        image = image_elem.get("src") if image_elem else None
        title = title_elem.get_text(" ", strip=True) if title_elem else None

        return {"title": title, "price": price, "image": image, "link": link}

    def _parse_listings(self, soup: BeautifulSoup, target_oem: Optional[str] = None) -> List[Dict]:
        containers = soup.select(".search-item, .item, .item-block, .items-box")
        if not containers:
            containers = soup.select("article, li, div")
        results: List[Dict] = []
        for item in containers:
            item_text = item.get_text(" ", strip=True)
            if target_oem and target_oem not in item_text:
                # allow fuzzy detection of OEM-like strings
                possible_oems = OEM_PATTERN.findall(item_text)
                if target_oem not in possible_oems:
                    continue
            parsed = self._parse_item(item, "https://rrr.lt")
            if parsed:
                results.append(parsed)
        return results

    def _scrape_detail(self, link: str, target_oem: Optional[str]) -> Optional[Dict]:
        response = self._get(link)
        if not response:
            return None
        soup = BeautifulSoup(response.text, "lxml")
        text_blob = soup.get_text(" ", strip=True)
        if target_oem and target_oem not in text_blob:
            matches = OEM_PATTERN.findall(text_blob)
            if target_oem not in matches:
                return None
        price_elem = soup.select_one(".price, .item-price, .search-item-price, span[itemprop='price']")
        price = clean_price_text(price_elem.get_text(" ", strip=True)) if price_elem else None
        image_elem = soup.select_one("[itemprop='image'], img")
        image = image_elem.get("src") if image_elem else None
        if price:
            return {"title": None, "price": price, "image": image, "link": link}
        return None

    def search_direct(self, oem: str) -> List[Dict]:
        url = f"https://rrr.lt/paieska/?q={quote(oem)}"
        response = self._get(url)
        if not response:
            return []
        soup = BeautifulSoup(response.text, "lxml")
        results = self._parse_listings(soup, target_oem=oem)
        detailed: List[Dict] = []
        for res in results:
            if res.get("link"):
                enriched = self._scrape_detail(res["link"], oem)
                if enriched:
                    detailed.append(enriched)
        return detailed or results

    def search_substring(self, oem: str) -> List[Dict]:
        if len(oem) < 5:
            return []
        partial = oem[:5]
        url = f"https://rrr.lt/paieska/?q={quote(partial)}"
        response = self._get(url)
        if not response:
            return []
        soup = BeautifulSoup(response.text, "lxml")
        found: List[Dict] = []
        for item in self._parse_listings(soup, target_oem=oem):
            found.append(item)
        return found

    def search_translated(self, detail: str) -> List[Dict]:
        translations = {
            "oil filter housing": "Tepalo filtro laikiklis",
            "oil cooler": "Alyvos aušintuvas",
            "turbo": "Turbina",
            "injector": "Purkštukas",
            "radiator": "Radiatorius",
            "fan": "Ventiliatorius",
            "water pump": "Vandens siurblys",
        }
        normalized_detail = normalize_text(detail)
        for key, translated in translations.items():
            if key in normalized_detail:
                response = self._get(f"https://rrr.lt/paieska/?q={quote(translated)}")
                if not response:
                    return []
                soup = BeautifulSoup(response.text, "lxml")
                return self._parse_listings(soup)
        return []

    def search_keywords(self, query: str) -> List[Dict]:
        normalized = normalize_text(query)
        short_keywords = " ".join(normalized.split()[:3])
        url = f"https://rrr.lt/paieska/?q={quote(short_keywords)}"
        response = self._get(url)
        if not response:
            return []
        soup = BeautifulSoup(response.text, "lxml")
        return self._parse_listings(soup)

    def search(self, oem: str, detail: str, query: str) -> List[Dict]:
        strategies = [
            lambda: self.search_direct(oem),
            lambda: self.search_substring(oem),
            lambda: self.search_translated(detail or query),
            lambda: self.search_keywords(query),
        ]
        for strategy in strategies:
            results = strategy()
            if results:
                return results
        return []

    def search_text(self, query: str) -> List[Dict]:
        return self.search_keywords(query)


# ----------------------------- eBay scraper -----------------------------

def fetch_ebay(search_term: str) -> List[Dict]:
    url = f"https://www.ebay.de/sch/i.html?_nkw={quote(search_term)}"
    try:
        response = requests.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return []
    soup = BeautifulSoup(response.text, "lxml")
    items = soup.select(".s-item")
    results: List[Dict] = []
    for item in items:
        price_elem = item.select_one(".s-item__price, span[itemprop='price']")
        price = clean_price_text(price_elem.get_text(" ", strip=True)) if price_elem else None
        if price is None:
            continue
        image_elem = item.select_one(".s-item__image-img")
        link_elem = item.select_one(".s-item__link")
        link = link_elem.get("href") if link_elem else None
        image = image_elem.get("src") if image_elem else None
        results.append({"title": None, "price": price, "image": image, "link": link})
    return results


# ----------------------------- Logging -----------------------------

def log_request(part_number: str, prices: List[float], final_price: float) -> None:
    timestamp = datetime.utcnow().isoformat()
    path = os.path.join("data", "part_logs.csv")
    file_exists = os.path.exists(path)

    min_price = min(prices) if prices else None
    max_price = max(prices) if prices else None
    avg_price = sum(prices) / len(prices) if prices else None
    count = len(prices)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["timestamp", "part_number", "min_price", "max_price", "avg_price", "final_price", "count"])
        writer.writerow([timestamp, part_number, min_price, max_price, avg_price, final_price, count])


# ----------------------------- FastAPI routes -----------------------------


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/cars.json")
async def serve_cars():
    return FileResponse("cars.json")


@app.get("/api/part", response_class=JSONResponse)
async def get_part(q: str = Query(..., min_length=1)):
    search_term = q.strip()
    car, model, detail = parse_query_details(search_term)
    print("Resolved query context:", car, model, detail)
    oem_candidates = resolve_oem(car, model, detail, search_term)

    scraper = RrrScraper()
    combined_results: List[Dict] = []
    internal_links: List[Dict[str, Optional[str]]] = []
    resolved_oem = None
    catalog_hit = False
    cache_used = False

    def add_links(rrr_res: List[Dict], ebay_res: List[Dict]):
        if rrr_res:
            first_link = next((r.get("link") for r in rrr_res if r.get("link")), None)
            if first_link:
                internal_links.append({"source": "rrr", "url": first_link})
        if ebay_res:
            first_link = next((r.get("link") for r in ebay_res if r.get("link")), None)
            if first_link:
                internal_links.append({"source": "ebay", "url": first_link})

    # try OEM candidates
    for candidate in oem_candidates:
        candidate = candidate.strip()
        if not candidate:
            continue

        cached = get_cached(candidate)
        if cached and cached.get("prices"):
            cache_used = True
            resolved_oem = candidate
            combined_results.extend(
                [{"price": p, "image": cached.get("image"), "link": None, "title": None} for p in cached.get("prices", [])]
            )
            break

        rrr_results = scraper.search(candidate, detail, search_term)
        ebay_results = fetch_ebay(candidate)
        add_links(rrr_results, ebay_results)
        candidate_results = rrr_results + ebay_results
        if candidate_results:
            resolved_oem = candidate
            combined_results.extend(candidate_results)
            catalog_hit = True if get_known_oems(car, model, detail) else False
            break

    # fallback to natural text
    if not combined_results:
        rrr_results = scraper.search_text(search_term)
        ebay_results = fetch_ebay(search_term)
        add_links(rrr_results, ebay_results)
        combined_results.extend(rrr_results + ebay_results)

    prices = [item["price"] for item in combined_results if isinstance(item.get("price"), (int, float))]

    if not prices:
        return JSONResponse(
            {
                "error": "No offers found",
                "oem_candidates": oem_candidates,
                "resolved_oem": resolved_oem,
                "raw_prices": prices,
                "internal_links": internal_links,
                "catalog_hit": catalog_hit,
                "cache_used": cache_used,
            }
        )

    avg_price = sum(prices) / len(prices)
    final_price = round(avg_price * 1.35, 2)

    photo = None
    for item in combined_results:
        if item.get("image"):
            photo = item["image"]
            break

    if resolved_oem:
        save_scrape_result(resolved_oem, prices, photo)
        if car and model and detail:
            save_new_oem(car, model, detail, resolved_oem)

    log_request(resolved_oem or search_term, prices, final_price)

    return {
        "final_price": final_price,
        "photo": photo,
        "oem_candidates": oem_candidates,
        "resolved_oem": resolved_oem,
        "raw_prices": prices,
        "internal_links": internal_links,
        "catalog_hit": catalog_hit,
        "cache_used": cache_used,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
