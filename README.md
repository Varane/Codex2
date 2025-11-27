# Part Price Aggregator

This project provides a FastAPI backend and a simple frontend to search automotive parts across multiple sources, calculate an adjusted final price, and log every query.

## Features
- Scrapes listings from rrr.lt and eBay.de for a given OEM number or part description.
- Applies a 1.35 multiplier to the average price across sources to present a final offer.
- Fallback search on rrr.lt for OEM inputs that return no results (prepends "BMW" to the query).
- Logs every request to `data/part_logs.csv` with summary statistics.
- Clean, dependency-free frontend with manual car/model/detail selection that generates search queries using an expanded dataset.

## Project Structure
- `main.py` — FastAPI app, scrapers, and logging.
- `cars.json` — Hierarchical car/model/detail data loaded by the frontend.
- `templates/index.html` — Minimal UI with search input and dropdown selectors.
- `static/script.js` — Frontend logic for fetching results and handling dropdowns.
- `data/part_logs.csv` — CSV log file automatically appended per request.
- `requirements.txt` — Python dependencies (FastAPI stack plus Jinja2 for templating).

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
