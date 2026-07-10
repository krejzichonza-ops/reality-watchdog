"""
Scraper pro sreality.cz.

Sreality je postavená na Next.js a výsledky hledání server-side renderuje
přímo do HTML v elementu <script id="__NEXT_DATA__">. Nepotřebujeme tedy
žádné neoficiální API ani headless browser - stačí stáhnout HTML stránky
hledání a vytáhnout z něj vestavěný JSON. Tohle je ověřené na živém webu
(červenec 2026).
"""
import json
import re
import requests
from bs4 import BeautifulSoup

from config import LOCATIONS, DISPOSITIONS, MAX_PRICE_CZK, MAX_AREA_M2, MAX_LISTINGS_PER_SOURCE, \
    REQUIRE_RENOVATION_KEYWORD
from keywords import matches_renovation

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "cs-CZ,cs;q=0.9",
}

NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL
)

AREA_RE = re.compile(r"(\d+)\s*m")


def _extract_next_data(html: str):
    m = NEXT_DATA_RE.search(html)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _parse_area(name: str):
    m = AREA_RE.search(name or "")
    return int(m.group(1)) if m else None


def _build_detail_url(item: dict) -> str:
    try:
        subcat = item["categorySubCb"]["name"]  # e.g. "2+kk"
        loc = item["locality"]
        parts = [loc.get("citySeoName"), loc.get("cityPartSeoName"), loc.get("streetSeoName")]
        parts = [p for p in parts if p]
        slug = "-".join(parts) if parts else str(item["id"])
        return f"https://www.sreality.cz/detail/prodej/byt/{subcat}/{slug}/{item['id']}"
    except Exception:
        # Fallback - alespoň odkaz na detail přes ID (nemusí být 100% přesný tvar,
        # ale sreality běžně přesměruje na správnou stránku, pokud se ID najde).
        return f"https://www.sreality.cz/hledani/prodej/byty?estate-id={item.get('id')}"


def _detail_matches_renovation(url: str) -> bool:
    """Sreality ve výpisu hledání nedává k dispozici popis inzerátu (jen
    název, cenu, dispozici), takže pro filtr na rekonstrukci musíme stáhnout
    detail stránky a zkontrolovat celý text (popis, štítky apod.).
    Voláno jen pro inzeráty, které už prošly cenou/dispozicí/plochou,
    takže se nejedná o stovky požadavků navíc."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        text = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)
        return matches_renovation(text)
    except Exception as e:
        print(f"[sreality] Nepodařilo se ověřit popis detailu {url}: {e}")
        return False


def fetch_new_listings(location: dict) -> list:
    """Stáhne aktuální nabídky bytů k prodeji pro danou lokalitu ze sreality.cz."""
    seo = location["sreality_seo"]
    url = f"https://www.sreality.cz/hledani/prodej/byty/{seo}"

    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    data = _extract_next_data(resp.text)
    if not data:
        raise RuntimeError(f"[sreality] Nepodařilo se najít __NEXT_DATA__ na {url} "
                            f"- struktura stránky se možná změnila.")

    queries = data["props"]["pageProps"]["dehydratedState"]["queries"]
    es_query = next((q for q in queries if q["queryKey"][0] == "estatesSearch"), None)
    if not es_query:
        raise RuntimeError(f"[sreality] Nenašel jsem 'estatesSearch' data na {url}.")

    results = es_query["state"]["data"]["results"][:MAX_LISTINGS_PER_SOURCE]

    listings = []
    for item in results:
        subcat_name = item.get("categorySubCb", {}).get("name", "")
        if subcat_name not in DISPOSITIONS:
            continue

        price = item.get("priceCzk") or item.get("priceSummaryCzk")
        if price is None or price <= 0 or price > MAX_PRICE_CZK:
            continue

        area = _parse_area(item.get("name", ""))
        if MAX_AREA_M2 and area and area > MAX_AREA_M2:
            continue

        detail_url = _build_detail_url(item)

        if REQUIRE_RENOVATION_KEYWORD and not _detail_matches_renovation(detail_url):
            continue

        listings.append({
            "source": "sreality.cz",
            "id": f"sreality-{item['id']}",
            "title": item.get("name", "Byt"),
            "price_czk": price,
            "area_m2": area,
            "location": f"{item.get('locality', {}).get('cityPart', '')}, "
                        f"{item.get('locality', {}).get('city', '')}".strip(", "),
            "url": detail_url,
        })

    return listings


def fetch_all() -> list:
    all_listings = []
    for loc in LOCATIONS:
        try:
            all_listings.extend(fetch_new_listings(loc))
        except Exception as e:
            print(f"[sreality] Chyba při stahování pro {loc['sreality_seo']}: {e}")
    return all_listings
