#!/usr/bin/env python3
"""
Monitor Inmobiliario — GBA Norte
Scraper para: Zonaprop, Argenprop, MercadoLibre, Properati, Inmuebles24
Zonas: Vicente López, Florida, La Lucila, San Isidro
Precio: USD 250.000 – 350.000
Tipos: Casas, PH, Terrenos, Galpones/Depósitos
"""

import json
import hashlib
import time
import random
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ─── CONFIG ──────────────────────────────────────────────────────────────────

ZONES = ["vicente-lopez", "florida", "la-lucila", "san-isidro"]
ZONES_DISPLAY = ["Vicente López", "Florida", "La Lucila", "San Isidro"]
PRICE_MIN = 250000
PRICE_MAX = 350000
PROPERTY_TYPES_ZP = ["casa", "ph", "terreno", "galpon", "deposito"]

DATA_FILE = Path(__file__).parent.parent / "data" / "properties.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]

def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))

def get_page(url: str, retries=3) -> Optional[BeautifulSoup]:
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            log.warning(f"Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(5 * (attempt + 1))
    return None

def parse_price(text: str) -> Optional[int]:
    """Extract USD price from string."""
    import re
    text = text.replace(".", "").replace(",", "").upper()
    m = re.search(r"USD\s*(\d+)", text)
    if m:
        return int(m.group(1))
    m = re.search(r"U\$S\s*(\d+)", text)
    if m:
        return int(m.group(1))
    m = re.search(r"\$\s*(\d{5,})", text)
    if m:
        val = int(m.group(1))
        if 250000 <= val <= 350000:
            return val
    return None

def parse_surface(text: str) -> Optional[int]:
    import re
    m = re.search(r"(\d+)\s*m", text.lower())
    return int(m.group(1)) if m else None

# ─── ZONAPROP ────────────────────────────────────────────────────────────────

def scrape_zonaprop() -> list:
    results = []
    type_slugs = {
        "Casa": "casas",
        "PH": "ph",
        "Terreno": "terrenos",
        "Galpón": "galpones",
        "Depósito": "depositos",
    }
    zone_slugs = {
        "Vicente López": "vicente-lopez-partido",
        "Florida": "florida-partido-vicente-lopez",
        "La Lucila": "la-lucila-partido-vicente-lopez",
        "San Isidro": "san-isidro-partido",
    }

    for ptype_name, ptype_slug in type_slugs.items():
        for zone_name, zone_slug in zone_slugs.items():
            url = (
                f"https://www.zonaprop.com.ar/{ptype_slug}-venta-{zone_slug}"
                f"-{PRICE_MIN}-{PRICE_MAX}-dolar.html"
            )
            log.info(f"[Zonaprop] {ptype_name} en {zone_name}")
            soup = get_page(url)
            if not soup:
                continue

            for card in soup.select("[data-id]")[:30]:
                try:
                    title_el = card.select_one("[class*='title']")
                    price_el = card.select_one("[class*='price']")
                    addr_el = card.select_one("[class*='address'], [class*='location']")
                    surface_el = card.select_one("[class*='surface'], [class*='area']")
                    link_el = card.select_one("a[href]")
                    rooms_el = card.select_one("[class*='room'], [class*='ambiente']")

                    if not price_el:
                        continue

                    price = parse_price(price_el.get_text())
                    if not price or not (PRICE_MIN <= price <= PRICE_MAX):
                        continue

                    href = link_el["href"] if link_el else ""
                    full_url = f"https://www.zonaprop.com.ar{href}" if href.startswith("/") else href

                    results.append({
                        "id": make_id(full_url),
                        "source": "Zonaprop",
                        "type": ptype_name,
                        "zone": zone_name,
                        "title": title_el.get_text(strip=True) if title_el else f"{ptype_name} en {zone_name}",
                        "address": addr_el.get_text(strip=True) if addr_el else zone_name,
                        "price_usd": price,
                        "surface_m2": parse_surface(surface_el.get_text()) if surface_el else None,
                        "rooms": rooms_el.get_text(strip=True) if rooms_el else None,
                        "url": full_url,
                        "first_seen": datetime.now(timezone.utc).isoformat(),
                        "last_seen": datetime.now(timezone.utc).isoformat(),
                    })
                except Exception as e:
                    log.debug(f"Error parsing Zonaprop card: {e}")

            sleep_random(2, 4)

    log.info(f"[Zonaprop] {len(results)} propiedades encontradas")
    return results

# ─── ARGENPROP ───────────────────────────────────────────────────────────────

def scrape_argenprop() -> list:
    results = []
    type_slugs = {
        "Casa": "casa",
        "PH": "ph",
        "Terreno": "terreno",
        "Galpón": "galpon",
        "Depósito": "deposito",
    }
    zone_ids = {
        "Vicente López": "partido-vicente-lopez",
        "San Isidro": "partido-san-isidro",
    }

    for ptype_name, ptype_slug in type_slugs.items():
        for zone_name, zone_slug in zone_ids.items():
            url = (
                f"https://www.argenprop.com/{ptype_slug}/venta/{zone_slug}"
                f"?precio-desde={PRICE_MIN}&precio-hasta={PRICE_MAX}&moneda=dolares"
            )
            log.info(f"[Argenprop] {ptype_name} en {zone_name}")
            soup = get_page(url)
            if not soup:
                continue

            for card in soup.select(".card--property, .listing__item")[:30]:
                try:
                    title_el = card.select_one(".card__title, .listing__title")
                    price_el = card.select_one(".card__price, .listing__price")
                    addr_el = card.select_one(".card__address, .listing__address")
                    surface_el = card.select_one(".card__main-features, .listing__features")
                    link_el = card.select_one("a[href]")

                    if not price_el:
                        continue

                    price = parse_price(price_el.get_text())
                    if not price or not (PRICE_MIN <= price <= PRICE_MAX):
                        continue

                    href = link_el["href"] if link_el else ""
                    full_url = f"https://www.argenprop.com{href}" if href.startswith("/") else href

                    results.append({
                        "id": make_id(full_url),
                        "source": "Argenprop",
                        "type": ptype_name,
                        "zone": zone_name,
                        "title": title_el.get_text(strip=True) if title_el else f"{ptype_name} en {zone_name}",
                        "address": addr_el.get_text(strip=True) if addr_el else zone_name,
                        "price_usd": price,
                        "surface_m2": parse_surface(surface_el.get_text()) if surface_el else None,
                        "rooms": None,
                        "url": full_url,
                        "first_seen": datetime.now(timezone.utc).isoformat(),
                        "last_seen": datetime.now(timezone.utc).isoformat(),
                    })
                except Exception as e:
                    log.debug(f"Error parsing Argenprop card: {e}")

            sleep_random(2, 4)

    log.info(f"[Argenprop] {len(results)} propiedades encontradas")
    return results

# ─── MERCADOLIBRE ────────────────────────────────────────────────────────────

def scrape_mercadolibre() -> list:
    results = []
    categories = {
        "Casa": "MLA1459",
        "PH": "MLA1460",
        "Terreno": "MLA1461",
        "Galpón": "MLA9998",
    }
    zones_ml = {
        "Vicente López": "vicente+lopez",
        "San Isidro": "san+isidro",
        "Florida": "florida+vicente+lopez",
        "La Lucila": "la+lucila",
    }

    for ptype_name, cat_id in categories.items():
        for zone_name, zone_q in zones_ml.items():
            url = (
                f"https://inmuebles.mercadolibre.com.ar/{cat_id}/venta/"
                f"_PriceRange_{PRICE_MIN}usd-{PRICE_MAX}usd"
                f"_q_{zone_q}"
            )
            log.info(f"[MercadoLibre] {ptype_name} en {zone_name}")
            soup = get_page(url)
            if not soup:
                continue

            for card in soup.select(".ui-search-result__wrapper, .results-item")[:20]:
                try:
                    title_el = card.select_one(".ui-search-item__title, h2")
                    price_el = card.select_one(".price-tag-fraction, .ui-search-price__second-line")
                    addr_el = card.select_one(".ui-search-item__location, .ui-search-item__group--location")
                    link_el = card.select_one("a.ui-search-link, a[href*='inmuebles']")
                    attr_els = card.select(".ui-search-item__details li")

                    if not price_el:
                        continue

                    price_text = price_el.get_text(strip=True)
                    # ML shows price without USD symbol sometimes, add context
                    price = parse_price(f"USD {price_text}")
                    if not price:
                        price = parse_price(price_text)
                    if not price or not (PRICE_MIN <= price <= PRICE_MAX):
                        continue

                    href = link_el["href"] if link_el else ""
                    surface = None
                    rooms = None
                    for attr in attr_els:
                        txt = attr.get_text(strip=True).lower()
                        if "m²" in txt or "m2" in txt:
                            surface = parse_surface(txt)
                        if "amb" in txt or "dorm" in txt:
                            rooms = txt

                    results.append({
                        "id": make_id(href),
                        "source": "MercadoLibre",
                        "type": ptype_name,
                        "zone": zone_name,
                        "title": title_el.get_text(strip=True) if title_el else f"{ptype_name} en {zone_name}",
                        "address": addr_el.get_text(strip=True) if addr_el else zone_name,
                        "price_usd": price,
                        "surface_m2": surface,
                        "rooms": rooms,
                        "url": href,
                        "first_seen": datetime.now(timezone.utc).isoformat(),
                        "last_seen": datetime.now(timezone.utc).isoformat(),
                    })
                except Exception as e:
                    log.debug(f"Error parsing MercadoLibre card: {e}")

            sleep_random(3, 6)

    log.info(f"[MercadoLibre] {len(results)} propiedades encontradas")
    return results

# ─── PROPERATI ───────────────────────────────────────────────────────────────

def scrape_properati() -> list:
    results = []
    type_slugs = {
        "Casa": "casas",
        "PH": "ph",
        "Terreno": "terrenos",
    }
    zones_p = ["vicente-lopez", "san-isidro", "la-lucila", "florida"]
    zone_display = {
        "vicente-lopez": "Vicente López",
        "san-isidro": "San Isidro",
        "la-lucila": "La Lucila",
        "florida": "Florida",
    }

    for ptype_name, ptype_slug in type_slugs.items():
        for zone_slug in zones_p:
            url = (
                f"https://www.properati.com.ar/{zone_slug}/{ptype_slug}/venta/"
                f"?precio-min={PRICE_MIN}&precio-max={PRICE_MAX}&currency=USD"
            )
            log.info(f"[Properati] {ptype_name} en {zone_display[zone_slug]}")
            soup = get_page(url)
            if not soup:
                continue

            for card in soup.select(".listing-card, [class*='ListingCard']")[:20]:
                try:
                    title_el = card.select_one("[class*='title'], h2, h3")
                    price_el = card.select_one("[class*='price'], [class*='Price']")
                    addr_el = card.select_one("[class*='address'], [class*='location']")
                    link_el = card.select_one("a[href]")
                    surface_el = card.select_one("[class*='surface'], [class*='area']")

                    if not price_el:
                        continue

                    price = parse_price(price_el.get_text())
                    if not price or not (PRICE_MIN <= price <= PRICE_MAX):
                        continue

                    href = link_el["href"] if link_el else ""
                    full_url = f"https://www.properati.com.ar{href}" if href.startswith("/") else href

                    results.append({
                        "id": make_id(full_url),
                        "source": "Properati",
                        "type": ptype_name,
                        "zone": zone_display[zone_slug],
                        "title": title_el.get_text(strip=True) if title_el else f"{ptype_name} en {zone_display[zone_slug]}",
                        "address": addr_el.get_text(strip=True) if addr_el else zone_display[zone_slug],
                        "price_usd": price,
                        "surface_m2": parse_surface(surface_el.get_text()) if surface_el else None,
                        "rooms": None,
                        "url": full_url,
                        "first_seen": datetime.now(timezone.utc).isoformat(),
                        "last_seen": datetime.now(timezone.utc).isoformat(),
                    })
                except Exception as e:
                    log.debug(f"Error parsing Properati card: {e}")

            sleep_random(2, 5)

    log.info(f"[Properati] {len(results)} propiedades encontradas")
    return results

# ─── INMUEBLES24 ─────────────────────────────────────────────────────────────

def scrape_inmuebles24() -> list:
    results = []
    zones_i24 = {
        "Vicente López": "vicente-lopez",
        "San Isidro": "san-isidro",
        "La Lucila": "la-lucila",
        "Florida": "florida",
    }
    type_slugs = {
        "Casa": "casas",
        "PH": "ph",
        "Terreno": "terrenos",
    }

    for ptype_name, ptype_slug in type_slugs.items():
        for zone_name, zone_slug in zones_i24.items():
            url = (
                f"https://www.inmuebles24.com/{ptype_slug}-venta-en-{zone_slug}.html"
                f"?precio-desde={PRICE_MIN}&precio-hasta={PRICE_MAX}&moneda=Dolares"
            )
            log.info(f"[Inmuebles24] {ptype_name} en {zone_name}")
            soup = get_page(url)
            if not soup:
                continue

            for card in soup.select("[data-id], .posting-card")[:20]:
                try:
                    title_el = card.select_one("[class*='title'], h2, h3")
                    price_el = card.select_one("[class*='price']")
                    addr_el = card.select_one("[class*='location'], [class*='address']")
                    link_el = card.select_one("a[href]")
                    surface_el = card.select_one("[class*='surface']")

                    if not price_el:
                        continue

                    price = parse_price(price_el.get_text())
                    if not price or not (PRICE_MIN <= price <= PRICE_MAX):
                        continue

                    href = link_el["href"] if link_el else ""
                    full_url = f"https://www.inmuebles24.com{href}" if href.startswith("/") else href

                    results.append({
                        "id": make_id(full_url),
                        "source": "Inmuebles24",
                        "type": ptype_name,
                        "zone": zone_name,
                        "title": title_el.get_text(strip=True) if title_el else f"{ptype_name} en {zone_name}",
                        "address": addr_el.get_text(strip=True) if addr_el else zone_name,
                        "price_usd": price,
                        "surface_m2": parse_surface(surface_el.get_text()) if surface_el else None,
                        "rooms": None,
                        "url": full_url,
                        "first_seen": datetime.now(timezone.utc).isoformat(),
                        "last_seen": datetime.now(timezone.utc).isoformat(),
                    })
                except Exception as e:
                    log.debug(f"Error parsing Inmuebles24 card: {e}")

            sleep_random(2, 4)

    log.info(f"[Inmuebles24] {len(results)} propiedades encontradas")
    return results

# ─── DEDUP & DIFF ─────────────────────────────────────────────────────────────

def dedup(props: list) -> list:
    seen = {}
    for p in props:
        if p["id"] not in seen:
            seen[p["id"]] = p
    return list(seen.values())

def diff(old_props: list, new_props: list):
    old_map = {p["id"]: p for p in old_props}
    new_map = {p["id"]: p for p in new_props}

    new_today = [p for pid, p in new_map.items() if pid not in old_map]
    removed_today = [p for pid, p in old_map.items() if pid not in new_map]

    price_changes = []
    for pid, new_p in new_map.items():
        if pid in old_map:
            old_price = old_map[pid].get("price_usd")
            new_price = new_p.get("price_usd")
            if old_price and new_price and old_price != new_price:
                price_changes.append({
                    **new_p,
                    "old_price_usd": old_price,
                    "price_change_pct": round((new_price - old_price) / old_price * 100, 1),
                })

    return new_today, removed_today, price_changes

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Monitor Inmobiliario GBA Norte — iniciando scraping ===")

    # Load previous data
    old_props = []
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE) as f:
                old_data = json.load(f)
                old_props = old_data.get("all_properties", [])
                log.info(f"Loaded {len(old_props)} previous properties")
        except Exception as e:
            log.warning(f"Could not load previous data: {e}")

    # Run scrapers
    fresh = []
    scrapers = [
        ("Zonaprop", scrape_zonaprop),
        ("Argenprop", scrape_argenprop),
        ("MercadoLibre", scrape_mercadolibre),
        ("Properati", scrape_properati),
        ("Inmuebles24", scrape_inmuebles24),
    ]

    for name, fn in scrapers:
        try:
            results = fn()
            fresh.extend(results)
            log.info(f"{name}: {len(results)} encontradas")
        except Exception as e:
            log.error(f"{name} failed: {e}")

    fresh = dedup(fresh)
    log.info(f"Total después de dedup: {len(fresh)}")

    # Preserve first_seen from old data
    old_map = {p["id"]: p for p in old_props}
    for p in fresh:
        if p["id"] in old_map:
            p["first_seen"] = old_map[p["id"]]["first_seen"]

    # Compute diff
    new_today, removed_today, price_changes = diff(old_props, fresh)
    log.info(f"Nuevas: {len(new_today)} | Bajas: {len(removed_today)} | Cambios precio: {len(price_changes)}")

    # Stats
    prices = [p["price_usd"] for p in fresh if p.get("price_usd")]
    surfaces = [p["surface_m2"] for p in fresh if p.get("surface_m2")]
    avg_price = int(sum(prices) / len(prices)) if prices else 0
    price_per_m2_list = [
        p["price_usd"] / p["surface_m2"]
        for p in fresh
        if p.get("price_usd") and p.get("surface_m2") and p["surface_m2"] > 0
    ]
    avg_ppm2 = int(sum(price_per_m2_list) / len(price_per_m2_list)) if price_per_m2_list else 0

    # Build output
    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "meta": {
            "zones": ["Vicente López", "Florida", "La Lucila", "San Isidro"],
            "price_min_usd": PRICE_MIN,
            "price_max_usd": PRICE_MAX,
            "types": ["Casa", "PH", "Terreno", "Galpón", "Depósito"],
        },
        "stats": {
            "total": len(fresh),
            "new_today": len(new_today),
            "removed_today": len(removed_today),
            "price_changes": len(price_changes),
            "avg_price_usd": avg_price,
            "avg_price_per_m2": avg_ppm2,
            "avg_surface_m2": int(sum(surfaces) / len(surfaces)) if surfaces else 0,
        },
        "new_today": new_today,
        "removed_today": removed_today,
        "price_changes": price_changes,
        "all_properties": fresh,
    }

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    log.info(f"✅ Datos guardados en {DATA_FILE}")
    log.info(f"Total: {len(fresh)} | Nuevas: {len(new_today)} | Bajas: {len(removed_today)}")

if __name__ == "__main__":
    main()
