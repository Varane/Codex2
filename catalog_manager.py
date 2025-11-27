import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

CATALOG_PATH = os.path.join("data", "catalog.json")
CACHE_PATH = os.path.join("data", "scrape_cache.json")
DEFAULT_STRUCTURE: Dict[str, Dict[str, Dict[str, List[str]]]] = {}


def _ensure_file(path: str, default_content) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(default_content, fp, indent=2)


def _load_json(path: str, default_content):
    _ensure_file(path, default_content)
    try:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except (OSError, json.JSONDecodeError):
        return default_content.copy() if isinstance(default_content, dict) else default_content


def _write_json(path: str, data) -> None:
    _ensure_file(path, data)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)


def get_known_oems(car: str, model: str, detail: str, base_catalog: Optional[Dict] = None) -> List[str]:
    catalog_data = _load_json(CATALOG_PATH, DEFAULT_STRUCTURE)
    merged_catalog: Dict = {}
    if base_catalog:
        merged_catalog.update(base_catalog)
    # merge persisted catalog
    for car_key, models in catalog_data.items():
        merged_catalog.setdefault(car_key, {}).update(models)

    if not car or not model or not detail:
        return []

    car_entry = merged_catalog.get(car, {})
    model_entry = car_entry.get(model, {})
    detail_list = model_entry.get(detail, [])
    return list(detail_list) if isinstance(detail_list, list) else []


def save_new_oem(car: str, model: str, detail: str, oem: str) -> None:
    if not (car and model and detail and oem):
        return
    catalog_data = _load_json(CATALOG_PATH, DEFAULT_STRUCTURE)
    catalog_data.setdefault(car, {}).setdefault(model, {}).setdefault(detail, [])
    if oem not in catalog_data[car][model][detail]:
        catalog_data[car][model][detail].append(oem)
        _write_json(CATALOG_PATH, catalog_data)


def save_scrape_result(oem: str, prices: List[float], image: Optional[str]) -> None:
    if not oem:
        return
    cache = _load_json(CACHE_PATH, {})
    cache[oem] = {
        "prices": prices,
        "image": image,
        "timestamp": datetime.utcnow().isoformat(),
    }
    _write_json(CACHE_PATH, cache)


def get_cached(oem: str) -> Optional[Dict]:
    cache = _load_json(CACHE_PATH, {})
    data = cache.get(oem)
    if not data:
        return None
    try:
        ts = datetime.fromisoformat(data.get("timestamp", ""))
    except ValueError:
        return None
    if datetime.utcnow() - ts > timedelta(days=7):
        return None
    return data
