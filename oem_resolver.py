import json
import os
import re
import string
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz, process

from catalog_manager import get_known_oems

STOPWORDS = {
    "bmw",
    "audi",
    "volvo",
    "peugeot",
    "citroen",
    "citroën",
    "series",
    "class",
    "model",
    "f30",
    "b8",
    "golf",
    "a4",
    "a6",
    "passat",
    "engine",
    "cooling",
    "suspension",
    "turbo",
    "part",
    "oem",
    "number",
}

KEYWORD_OEM_MAP: Dict[str, List[str]] = {
    # Turbochargers
    "turbo": ["11657595351", "11657649288", "06H145702S", "06H145702L", "0375J6", "0375J7", "36002657", "53039700569", "53039700586", "4937701700", "04E145721Q", "04L253010N", "03L253016SV", "059145722T", "04E145721R"],
    "turbina": ["11657595351", "11657649288", "06H145702S", "06H145702L", "0375J6", "0375J7", "059145722T"],
    "turbolader": ["11657649288", "06H145702S", "06H145702L", "03L198716", "03L145702T", "04E145721Q"],
    # Injectors
    "injector": ["13537585261", "06J906036", "06H906036G", "1980L0", "1980L1", "28232242", "33800-2A000", "0445116030", "0445110328", "1465A041", "03L130277B", "057130277AR", "36002691", "30777394"],
    "einspritzdüse": ["13537585261", "06J906036", "06H906036G", "1980L0", "057130277AR"],
    "inyector": ["13537585261", "06J906036", "06H906036G", "1980L1", "04E906036Q"],
    # Cooling fans
    "fan": ["31429982", "17427640501", "31387062", "31387064", "17427640502", "8K0959455T", "3Q0959455AD", "5Q0959455H"],
    "cooling fan": ["31429982", "17427640501", "17427640502", "3Q0959455AD"],
    "ventiliatorius": ["31429982", "17427640501"],
    # Oil filter housing / cooler
    "oil filter housing": ["11428576524", "11428506797", "1103.TQ", "06J115403Q", "11427525335", "11427612143", "03L115389C", "31319824", "04E115397R"],
    "olio filtro": ["11428576524", "11428506797", "1103.TQ"],
    "carter olio": ["11428506797", "1103.TQ"],
    "oil cooler": ["17217600553", "31293695", "17217529499"],
    # Suspension & steering
    "control arm": ["8K0407151B", "31126771893", "31126769715", "4F0407509E", "1K0407151BC", "31212740", "3C0407151T"],
    "wishbone": ["8K0407151B", "4F0407509E"],
    "air spring": ["37126790078", "37126790079", "4Z7616051A", "4Z7616052A", "2113200725"],
    "shock absorber": ["31316796314", "33526796317", "8K0513035J", "1K0512011BG", "520697", "31277540"],
    # Cooling components
    "radiator": ["17117573781", "17117573782", "1300262", "8K0121251L", "1K0121251J", "31319076", "3G0121251A", "5Q0121251ET"],
    "water pump": ["11517546994", "11517586925", "03L121011", "06H121011", "16100-39436", "31319642", "11517546988", "04L121011N", "059121004D"],
    "expansion tank": ["17137619189", "17137647280", "1K0121407A", "8E0121403", "1306E3"],
    "thermostat": ["11537510959", "11538648988", "03L121113", "06H121113B", "1336Q5"],
    # Brakes
    "brake disc": ["34116793247", "34106797602", "8K0615301T", "1K0615301AA", "4249W0"],
    "brake pad": ["34116794918", "34116787168", "8K0698151E", "1K0698151T", "4254.40"],
    # Intake / exhaust
    "intercooler": ["17517600533", "14411EB70A", "8K0145806B", "03L145749N", "17117791677", "4G0145805P"],
    "oxygen sensor": ["11787575933", "11787548713", "06J906262AN", "03L906262BD", "0258006028"],
    "glow plug": ["12232247692", "12237801268", "03L905061N", "04L905061G", "5960R7"],
    # Fuel and ignition
    "fuel pump": ["16146752499", "16147276073", "8E0919051CJ", "1K0919051DB", "1525KX"],
    "spark plug": ["12120039664", "12122158253", "06H905611", "03L905618", "5960A3"],
    # Cooling fans alt translations
    "ventilador": ["31429982", "17427640501"],
    "ventilateur": ["31429982", "31429982"],
}

OEM_REGEX = re.compile(
    r"\b(?:(?:\d{10,12})|(?:0[36][A-Z]\d{6,7}[A-Z]?)|(?:\d[A-Z]\d{6,8})|(?:[0-9]{2}[A-Z0-9]{6,8}))\b",
    re.IGNORECASE,
)

PREFIX_HINT_PATTERNS = [
    re.compile(r"\b(?:11\d{8,10}|13\d{8,10}|17\d{8,10})\b", re.IGNORECASE),
    re.compile(r"\b(?:03L|06H|8K0)[A-Z0-9]{5,8}\b", re.IGNORECASE),
    re.compile(r"\b(?:96|98|19)\d{6,8}\b", re.IGNORECASE),
    re.compile(r"\b31\d{2,8}\b", re.IGNORECASE),
]


def load_lookup(file_name: str) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    path = os.path.join(os.path.dirname(__file__), file_name)
    try:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except (OSError, json.JSONDecodeError):
        return {}


LOOKUP_DATA = load_lookup("oem_lookup.json")
CATALOG_DATA = load_lookup("oem_catalog.json")


def normalize(text: str) -> str:
    lowered = text.lower()
    table = str.maketrans({ch: " " for ch in string.punctuation})
    return re.sub(r"\s+", " ", lowered.translate(table)).strip()


def dedupe_preserve(seq: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in seq:
        if not item:
            continue
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def best_key(options: List[str], value: str) -> Optional[str]:
    if not options or not value:
        return None
    match = process.extractOne(value, options, scorer=fuzz.partial_ratio)
    if match and match[1] >= 80:
        return match[0]
    for opt in options:
        if normalize(opt) == normalize(value):
            return opt
    return None


def lookup_from_table(car: str, model: str, detail: str, table: Dict[str, Dict[str, Dict[str, List[str]]]]) -> List[str]:
    candidates: List[str] = []
    if not table:
        return candidates
    car_key = best_key(list(table.keys()), car)
    if not car_key:
        return candidates
    model_data = table.get(car_key, {})
    model_key = best_key(list(model_data.keys()), model)
    if not model_key:
        return candidates
    detail_data = model_data.get(model_key, {})
    detail_key = best_key(list(detail_data.keys()), detail)
    if detail_key:
        candidates.extend(detail_data.get(detail_key, []))
    return candidates


def keyword_oems(query: str) -> List[str]:
    normalized_query = normalize(query)
    collected: List[str] = []
    for keyword, oems in KEYWORD_OEM_MAP.items():
        if keyword in normalized_query:
            collected.extend(oems)
        else:
            ratio = fuzz.partial_ratio(keyword, normalized_query)
            if ratio > 85:
                collected.extend(oems)
    return collected


def extract_oems_from_text(text: str) -> List[str]:
    results = OEM_REGEX.findall(text)
    for pattern in PREFIX_HINT_PATTERNS:
        results.extend(pattern.findall(text))
    cleaned: List[str] = []
    for match in results:
        if isinstance(match, tuple):
            match = "".join(match)
        cleaned.append(match)
    return cleaned


def scrape_rrr_for_keywords(keywords: List[str]) -> List[str]:
    found: List[str] = []
    for kw in keywords:
        try:
            response = requests.get(f"https://rrr.lt/paieska/?q={quote(kw)}", timeout=10)
            response.raise_for_status()
        except requests.RequestException:
            continue
        soup = BeautifulSoup(response.text, "lxml")
        text_content = soup.get_text(" ", strip=True)
        found.extend(extract_oems_from_text(text_content))
        links = soup.find_all("a", href=True)
        for link in links:
            found.extend(extract_oems_from_text(link.get_text(" ", strip=True)))
            found.extend(extract_oems_from_text(link.get("href", "")))
    return found


def score_candidates(candidates: List[Tuple[str, int]]) -> List[str]:
    sorted_items = sorted(candidates, key=lambda item: item[1], reverse=True)
    ordered: List[str] = []
    seen = set()
    for cand, _ in sorted_items:
        if cand not in seen:
            seen.add(cand)
            ordered.append(cand)
    return ordered


def resolve_oem(car: str, model: str, detail: str, query: str) -> List[str]:
    print("OEM resolver input:", car, model, detail, query)
    scored: List[Tuple[str, int]] = []

    # catalog / lookup matches
    for table, weight in ((LOOKUP_DATA, 90), (CATALOG_DATA, 88)):
        for oem in lookup_from_table(car, model, detail, table):
            scored.append((oem.upper(), weight))

    for oem in get_known_oems(car, model, detail, base_catalog=CATALOG_DATA):
        scored.append((oem.upper(), 87))

    for oem in keyword_oems(query):
        scored.append((oem.upper(), 85))

    normalized_query = normalize(query)
    for detected in extract_oems_from_text(query + " " + normalized_query):
        scored.append((detected.upper(), 95))

    for pattern in PREFIX_HINT_PATTERNS:
        for m in pattern.findall(normalized_query):
            scored.append((m.upper(), 80))

    if not scored:
        keywords = [kw for kw in normalized_query.split() if kw not in STOPWORDS and len(kw) > 2][:3]
        scored.extend([(cand.upper(), 70) for cand in scrape_rrr_for_keywords(keywords)])

    final_candidates = score_candidates(scored)
    print("Detected OEM candidates:", final_candidates)
    return final_candidates
