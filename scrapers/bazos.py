"""
Scraper pro reality.bazos.cz.

Bazos nemá zdokumentované API, ale výpis inzerátů je čisté server-rendered
HTML (žádné JS), takže jde spolehlivě parsovat regexem/BeautifulSoup přímo
z výpisu kategorie "Byty - prodej" s filtrem na lokalitu a cenu v URL
(stejné parametry jako filtr nahoře na webu: hlokalita, humkreis, cenado).

Pozor: parametry hlokalita/humkreis/cenado jsou odvozené z vyhledávacího
formuláře na webu, ne z oficiální dokumentace - při prvním běhu zkontroluj
v logu, že se pro každou lokalitu vrací rozumný počet inzerátů, a případně
uprav LOCATION_QUERY.
"""
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

BASE_URL = "https://reality.bazos.cz/prodam/byt/"

# Textový název lokality tak, jak ho čekává pole "Lokalita" ve vyhledávacím
# formuláři bazos.cz (běžně obec/okres/PSČ).
LOCATION_QUERY = {
    "brno": "Brno",
    "hradec-kralove": "Hradec Kralove",
    "pardubice": "Pardubice",
}

LISTING_RE = re.compile(
    r'href="(/inzerat/(\d+)/[^"]+\.php)"[^>]*>.*?</a>', re.DOTALL
)
PRICE_RE = re.compile(r"([\d\s]{4,})\s*Kč")
LAYOUT_RE = re.compile(r"\b([1-6]\s?\+\s?(?:kk|1))\b", re.IGNORECASE)
AREA_RE = re.compile(r"(\d+)\s*m2|(\d+)\s*m²")


def _parse_listings(html: str):
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    seen_ids = set()

    for a in soup.find_all("a", href=re.compile(r"^/inzerat/\d+/")):
        m = re.search(r"/inzerat/(\d+)/", a["href"])
        if not m:
            continue
        listing_id = m.group(1)
        if listing_id in seen_ids:
            continue

        title = a.get_text(strip=True)
        if not title:
            continue  # obrázkové odkazy bez textu přeskočíme, počkáme na ten s nadpisem

        seen_ids.add(listing_id)

        # cena a lokalita bývají v nejbližším rodičovském bloku inzerátu
        container = a.find_parent("div") or a.parent
        block_text = container.get_text(" ", strip=True) if container else title

        price_m = PRICE_RE.search(block_text)
        price = int(re.sub(r"\s", "", price_m.group(1))) if price_m else None

        layout_m = LAYOUT_RE.search(title) or LAYOUT_RE.search(block_text)
        area_m = AREA_RE.search(title) or AREA_RE.search(block_text)
        area = None
        if area_m:
            area = int(area_m.group(1) or area_m.group(2))

        url = f"https://reality.bazos.cz{a['href']}"

        listings.append({
            "id": listing_id,
            "title": title,
            "price_czk": price,
            "layout": layout_m.group(1).replace(" ", "").lower() if layout_m else None,
            "area_m2": area,
            "url": url,
            "raw_text": block_text,
        })

    return listings


def fetch_new_listings(location: dict) -> list:
    seo = location["sreality_seo"]
    loc_query = LOCATION_QUERY.get(seo)
    if not loc_query:
        return []

    params = {
        "hlokalita": loc_query,
        "humkreis": "0",  # bez okolí navíc, jen daná obec
        "cenado": str(MAX_PRICE_CZK),
    }
    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    raw = _parse_listings(resp.text)[:MAX_LISTINGS_PER_SOURCE]

    listings = []
    for c in raw:
        if not c["layout"] or c["layout"] not in [d.lower().replace(" ", "") for d in DISPOSITIONS]:
            continue
        if c["price_czk"] is None or c["price_czk"] > MAX_PRICE_CZK:
            continue
        if MAX_AREA_M2 and c["area_m2"] and c["area_m2"] > MAX_AREA_M2:
            continue
        if REQUIRE_RENOVATION_KEYWORD and not matches_renovation(c["raw_text"]):
            continue

        listings.append({
            "source": "bazos.cz",
            "id": f"bazos-{c['id']}",
            "title": c["title"],
            "price_czk": c["price_czk"],
            "area_m2": c["area_m2"],
            "location": loc_query,
            "url": c["url"],
        })

    return listings


def fetch_all() -> list:
    all_listings = []
    for loc in LOCATIONS:
        try:
            found = fetch_new_listings(loc)
            print(f"[bazos] {loc['sreality_seo']}: {len(found)} shod po filtraci")
            all_listings.extend(found)
        except Exception as e:
            print(f"[bazos] Chyba při stahování pro {loc['sreality_seo']}: {e}")
    return all_listings
