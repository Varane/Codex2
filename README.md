# Part Price Aggregator

This project provides a FastAPI backend and a simple frontend to search automotive parts across multiple sources, calculate an adjusted final price, and log every query. It includes an OEM intelligence layer with caching and an internal catalog to make results resilient even when marketplaces change their markup.

## Features
- Scrapes listings from rrr.lt and eBay.de using multi-strategy searches (direct OEM, substring, translations, keyword fallback, and detail-page rescans) to maximize hit rate.
- OEM intelligence layer resolves likely part numbers from natural-language queries, vehicle context, lookup tables, catalogs, fuzzy rules, and heuristic scraping.
- Applies a 1.35 multiplier to the average price across sources to present a final offer.
- Caches successful scrapes for 7 days and stores known OEMs in `data/catalog.json` for future lookups.
- Logs every request to `data/part_logs.csv` with summary statistics.
- Clean, dependency-free frontend with manual car/model/detail selection that generates search queries using an expanded dataset.
- Car dataset spans multiple makes (BMW, Audi, Mercedes, Volkswagen, Toyota, Ford, Honda, Nissan, Volvo, Peugeot) with several models and system categories for broader dropdown coverage.

## Project Structure
- `main.py` — FastAPI app, scrapers, cache-aware catalog logic, and logging.
- `cars.json` — Hierarchical car/model/detail data loaded by the frontend.
- `templates/index.html` — Minimal UI with search input and dropdown selectors.
- `static/script.js` — Frontend logic for fetching results and handling dropdowns.
- `data/part_logs.csv` — CSV log file automatically appended per request.
- `data/catalog.json` — Persistent catalog for newly learned OEM numbers.
- `data/scrape_cache.json` — Cache of recent scrape results (expires after 7 days).
- `requirements.txt` — Python dependencies (FastAPI stack, scraping utilities, Jinja2 for templating, RapidFuzz for fuzzy matches).
- `oem_lookup.json` / `oem_catalog.json` — Seeded OEM data to boost resolver accuracy.

## Getting Started
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the development server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Open the app:
   ```
   http://localhost:8000
   ```

Use the top search bar for direct OEM or text search, or pick a car/model/detail combination to generate the query automatically.
