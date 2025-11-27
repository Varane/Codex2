from datetime import datetime
import csv
import os
from typing import Dict, List, Optional
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Part Price Aggregator")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/cars.json")
async def serve_cars():
    return FileResponse("cars.json")


def parse_price(text: str) -> Optional[float]:
    cleaned = "".join(ch for ch in text if ch.isdigit() or ch in ",.")
    if not cleaned:
        return None
    cleaned = cleaned.replace(".", "").replace(",", ".", 1)
    try:
        return float(cleaned)
    except ValueError:
        return None


def fetch_rrr(search_term: str, is_oem: bool) -> List[Dict[str, Optional[str]]]:
    search_results = _scrape_rrr(search_term)
    if not search_results and is_oem:
        fallback_term = f"BMW {search_term}"
        search_results = _scrape_rrr(fallback_term)
    return search_results


def _scrape_rrr(search_term: str) -> List[Dict[str, Optional[str]]]:
    url = f"https://rrr.lt/paieska/?q={quote(search_term)}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "lxml")
    items = soup.select(".item-block")
    results: List[Dict[str, Optional[str]]] = []

    for item in items:
        title_elem = item.select_one(".item-title, .title, a")
        price_elem = item.select_one(".item-price, .price")
        image_elem = item.select_one('img[itemprop="image"], img')
        link_elem = item.select_one(".item-block a")

        price = parse_price(price_elem.get_text(strip=True)) if price_elem else None
        image = image_elem.get("src") if image_elem else None
        link_href = link_elem.get("href") if link_elem else None
        link = urljoin("https://rrr.lt", link_href) if link_href else None
        title = title_elem.get_text(strip=True) if title_elem else None

        if price is not None:
            results.append(
                {
                    "title": title,
                    "price": price,
                    "image": image,
                    "link": link,
                }
            )
    return results


def fetch_ebay(search_term: str) -> List[Dict[str, Optional[str]]]:
    url = f"https://www.ebay.de/sch/i.html?_nkw={quote(search_term)}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "lxml")
    items = soup.select(".s-item")
    results: List[Dict[str, Optional[str]]] = []

    for item in items:
        price_elem = item.select_one(".s-item__price")
        image_elem = item.select_one(".s-item__image-img")
        link_elem = item.select_one(".s-item__link")

        price = parse_price(price_elem.get_text(strip=True)) if price_elem else None
        image = image_elem.get("src") if image_elem else None
        link = link_elem.get("href") if link_elem else None

        if price is not None:
            results.append(
                {
                    "title": None,
                    "price": price,
                    "image": image,
                    "link": link,
                }
            )
    return results


def log_request(part_number: str, prices: List[float], final_price: float) -> None:
    timestamp = datetime.utcnow().isoformat()
    path = os.path.join("data", "part_logs.csv")
    file_exists = os.path.exists(path)

    min_price = min(prices) if prices else None
    max_price = max(prices) if prices else None
    avg_price = sum(prices) / len(prices) if prices else None
    count = len(prices)

    with open(path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["timestamp", "part_number", "min_price", "max_price", "avg_price", "final_price", "count"])
        writer.writerow([timestamp, part_number, min_price, max_price, avg_price, final_price, count])


@app.get("/api/part", response_class=JSONResponse)
async def get_part(q: str = Query(..., min_length=1)):
    search_term = q.strip()
    is_oem = search_term.replace(" ", "").isdigit()

    rrr_results = fetch_rrr(search_term, is_oem)
    ebay_results = fetch_ebay(search_term)

    combined_results = rrr_results + ebay_results
    prices = [item["price"] for item in combined_results if isinstance(item.get("price"), (int, float))]

    if not prices:
        return JSONResponse({"error": "No offers found"}, status_code=404)

    avg_price = sum(prices) / len(prices)
    final_price = round(avg_price * 1.35, 2)

    photo = None
    for item in combined_results:
        if item.get("image"):
            photo = item["image"]
            break

    internal_links: List[Dict[str, Optional[str]]] = []
    if rrr_results and rrr_results[0].get("link"):
        internal_links.append({"source": "rrr", "url": rrr_results[0]["link"]})
    if ebay_results and ebay_results[0].get("link"):
        internal_links.append({"source": "ebay", "url": ebay_results[0]["link"]})

    log_request(search_term, prices, final_price)

    return {
        "final_price": final_price,
        "photo": photo,
        "internal_links": internal_links,
        "raw_prices": prices,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
