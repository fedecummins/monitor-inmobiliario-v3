#!/usr/bin/env python3
"""
Monitor Inmobiliario — GBA Norte
Fuente: Zonaprop via ScraperAPI
Zonas: Vicente López, Florida, La Lucila, San Isidro
Precio: USD 250.000 – 350.000
"""

import json
import hashlib
import time
import random
import logging
import re
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PRICE_MIN = 250000
PRICE_MAX = 350000
DATA_FILE = Path(__file__).parent / "data" / "properties.json"

SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY", "72404a3277533db7d13a93c6b44bb00f")

def scraper_get(url: str) -> Optional[BeautifulSoup]:
    """Fetch URL via ScraperAPI to bypass bot detection."""
    proxy_url = f"http://scraperapi:{SCRAPER_API_KEY}@proxy-server.scraperapi.com:8001"
    proxies = {"http": proxy_url, "https": proxy_url}
    for attempt in range(3):
        try:
            r = requests.get(url, proxies=proxies, timeout=60, verify=False)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            log.warning(f"Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(5 * (attempt + 1))
    return None

def make_id(url): return hashlib.md5(url.encode()).hexdigest()[:12]
def now_iso(): return datetime.now(timezone.utc).isoformat()

def parse_price(text: str) -> Optional[int]:
    if not text: return None
    text = text.upper().replace(".", "").replace(",", "")
    for pattern in [r"USD\s*(\d+)", r"U\$S\s*(\d+)", r"US\$\s*(\d+)"]:
        m = re.search(pattern, text)
        if m:
            val = int(m.group(1))
            if val < 1000: val *= 1000
            return val
    return None

def parse_surface(text: str) -> Optional[int]:
    if not text: return None
    m = re.search(r"(\d+)\s*m", text.lower())
    return int(m.group(1)) if m else None

# ── ZONAPROP ──────────────────────────────────────────────────────────────────

ZP_TYPES = {
    "Casa":     "casas",
    "PH":       "ph",
    "Terreno":  "terrenos",
    "Galpón":   "galpones",
    "Depósito": "depositos",
}

ZP_ZONES = {
    "Vicente López": "vicente-lopez-partido",
    "Florida":       "florida-partido-vicente-lopez",
    "La Lucila":     "la-lucila-partido-vicente-lopez",
    "San Isidro":    "san-isidro-partido",
}

def scrape_zonaprop() -> list:
    results = []

    for ptype_name, ptype_slug in ZP_TYPES.items():
        for zone_name, zone_slug in ZP_ZONES.items():
            url = (
                f"https://www.zonaprop.com.ar/{ptype_slug}-venta-{zone_slug}"
                f"-{PRICE_MIN}-{PRICE_MAX}-dolar.html"
            )
            log.info(f"[Zonaprop] {ptype_name} en {zone_name}")
            soup = scraper_get(url)
            if not soup:
                log.warning(f"[Zonaprop] Sin respuesta para {ptype_name} en {zone_name}")
                continue

            # Zonaprop embeds listing data as JSON in a <script> tag
            found_json = False
            for script in soup.find_all("script"):
                text = script.string or ""
                if "listPostings" in text or "postingsSummary" in text:
                    try:
                        # Extract JSON from script
                        m = re.search(r'initialState\s*=\s*({.+?});?\s*</script', text, re.DOTALL)
                        if not m:
                            m = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', text, re.DOTALL)
                        if m:
                            data = json.loads(m.group(1))
                            # Navigate the JSON structure
                            postings = (
                                data.get("listStore", {}).get("listPostings", []) or
                                data.get("listPostings", []) or
                                []
                            )
                            for p in postings:
                                try:
                                    price_data = p.get("priceOperationTypes", [{}])[0] if p.get("priceOperationTypes") else {}
                                    price_usd = None
                                    for pop in p.get("priceOperationTypes", []):
                                        for pr in pop.get("prices", []):
                                            if pr.get("currency") == "USD":
                                                price_usd = int(pr.get("amount", 0))
                                    if not price_usd or not (PRICE_MIN <= price_usd <= PRICE_MAX):
                                        continue

                                    posting_id = str(p.get("postingId", ""))
                                    pub_url = f"https://www.zonaprop.com.ar{p.get('url', '')}"
                                    title = p.get("title") or f"{ptype_name} en {zone_name}"
                                    address = p.get("address") or zone_name
                                    surface_total = p.get("totalSurface")
                                    surface_covered = p.get("roofedSurface")
                                    surface_m2 = surface_total or surface_covered
                                    rooms = p.get("room")
                                    rooms_str = f"{rooms} amb." if rooms else None

                                    results.append({
                                        "id": make_id(pub_url),
                                        "source": "Zonaprop",
                                        "type": ptype_name,
                                        "zone": zone_name,
                                        "title": title,
                                        "address": address,
                                        "price_usd": price_usd,
                                        "surface_m2": int(surface_m2) if surface_m2 else None,
                                        "rooms": rooms_str,
                                        "url": pub_url,
                                        "first_seen": now_iso(),
                                        "last_seen": now_iso(),
                                    })
                                    found_json = True
                                except Exception as e:
                                    log.debug(f"Error parsing posting: {e}")
                    except Exception as e:
                        log.debug(f"Error parsing JSON from script: {e}")

            # Fallback: parse HTML cards if JSON not found
            if not found_json:
                cards = soup.select("[data-id]") or soup.select(".postingCard") or soup.select("[class*='posting-card']")
                for card in cards[:40]:
                    try:
                        price_el = card.select_one("[class*='Price'], [class*='price']")
                        if not price_el: continue
                        price = parse_price(price_el.get_text())
                        if not price or not (PRICE_MIN <= price <= PRICE_MAX): continue

                        link_el = card.select_one("a[href]")
                        href = link_el["href"] if link_el else ""
                        pub_url = f"https://www.zonaprop.com.ar{href}" if href.startswith("/") else href

                        title_el = card.select_one("[class*='Title'], [class*='title'], h2, h3")
                        addr_el = card.select_one("[class*='Address'], [class*='address'], [class*='location']")
                        surface_el = card.select_one("[class*='Surface'], [class*='surface']")
                        rooms_el = card.select_one("[class*='Room'], [class*='room'], [class*='ambiente']")

                        results.append({
                            "id": make_id(pub_url),
                            "source": "Zonaprop",
                            "type": ptype_name,
                            "zone": zone_name,
                            "title": title_el.get_text(strip=True) if title_el else f"{ptype_name} en {zone_name}",
                            "address": addr_el.get_text(strip=True) if addr_el else zone_name,
                            "price_usd": price,
                            "surface_m2": parse_surface(surface_el.get_text()) if surface_el else None,
                            "rooms": rooms_el.get_text(strip=True) if rooms_el else None,
                            "url": pub_url,
                            "first_seen": now_iso(),
                            "last_seen": now_iso(),
                        })
                    except Exception as e:
                        log.debug(f"Error parsing card: {e}")

            count = len([r for r in results if r["zone"] == zone_name and r["type"] == ptype_name])
            log.info(f"[Zonaprop] {ptype_name} en {zone_name}: {count} encontradas")
            time.sleep(random.uniform(2, 4))

    log.info(f"[Zonaprop] TOTAL: {len(results)} propiedades")
    return results

# ── DEDUP & DIFF ──────────────────────────────────────────────────────────────

def dedup(props):
    seen = {}
    for p in props:
        if p["id"] not in seen:
            seen[p["id"]] = p
    return list(seen.values())

def diff(old_props, new_props):
    old_map = {p["id"]: p for p in old_props}
    new_map = {p["id"]: p for p in new_props}
    new_today     = [p for pid, p in new_map.items() if pid not in old_map]
    removed_today = [p for pid, p in old_map.items() if pid not in new_map]
    price_changes = []
    for pid, new_p in new_map.items():
        if pid in old_map:
            op = old_map[pid].get("price_usd")
            np = new_p.get("price_usd")
            if op and np and op != np:
                price_changes.append({**new_p, "old_price_usd": op,
                    "price_change_pct": round((np - op) / op * 100, 1)})
    return new_today, removed_today, price_changes

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Monitor Inmobiliario GBA Norte ===")

    old_props = []
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE) as f:
                old_data = json.load(f)
                old_props = old_data.get("all_properties", [])
                log.info(f"Cargadas {len(old_props)} propiedades previas")
        except Exception as e:
            log.warning(f"No se pudo cargar data previa: {e}")

    fresh = []
    try:
        fresh = scrape_zonaprop()
    except Exception as e:
        log.error(f"Zonaprop failed: {e}")

    fresh = dedup(fresh)
    log.info(f"Total dedup: {len(fresh)}")

    old_map = {p["id"]: p for p in old_props}
    for p in fresh:
        if p["id"] in old_map:
            p["first_seen"] = old_map[p["id"]]["first_seen"]

    new_today, removed_today, price_changes = diff(old_props, fresh)
    prices   = [p["price_usd"] for p in fresh if p.get("price_usd")]
    surfaces = [p["surface_m2"] for p in fresh if p.get("surface_m2")]
    ppm2_list = [p["price_usd"]/p["surface_m2"] for p in fresh
                 if p.get("price_usd") and p.get("surface_m2") and p["surface_m2"] > 0]

    output = {
        "last_updated": now_iso(),
        "meta": {
            "zones": ["Vicente López", "Florida", "La Lucila", "San Isidro"],
            "price_min_usd": PRICE_MIN, "price_max_usd": PRICE_MAX,
            "types": ["Casa", "PH", "Terreno", "Galpón", "Depósito"]
        },
        "stats": {
            "total": len(fresh), "new_today": len(new_today),
            "removed_today": len(removed_today), "price_changes": len(price_changes),
            "avg_price_usd": int(sum(prices)/len(prices)) if prices else 0,
            "avg_price_per_m2": int(sum(ppm2_list)/len(ppm2_list)) if ppm2_list else 0,
            "avg_surface_m2": int(sum(surfaces)/len(surfaces)) if surfaces else 0,
        },
        "new_today": new_today, "removed_today": removed_today,
        "price_changes": price_changes, "all_properties": fresh,
    }

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    log.info(f"✅ Guardado. Total: {len(fresh)} | Nuevas: {len(new_today)} | Bajas: {len(removed_today)} | Cambios: {len(price_changes)}")

if __name__ == "__main__":
    main()
