"""
Scraper pro reality.bazos.cz.

Bazos nemá zdokumentované API a výpis inzerátů je čisté server-rendered
HTML (žádné JS). POZOR: bazos v průběhu roku 2026 změnil URL strukturu -
staré query-param URL (/prodam/byt/?hlokalita=...&cenado=...) teď vrací
404. Aktuální funkční formát jsou SEO cesty typu
/inzeraty/prodej-bytu-<mesto>/ (ověřeno živě). Filtr na cenu/plochu/
dispozici proto děláme čistě klientsky (viz níže), URL už žádné
parametry nenese.
"""
import re
import requests
from bs4 import BeautifulSoup

from config import LOCATIONS, DISPOSITIONS, MAX_PRICE_CZK, MAX_AREA_M2, MAX_LISTINGS_PER_SOURCE
from keywords import matches_renovation

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.5",
    "Referer": "https://www.google.com/",
}

# SEO cesta pro danou lokalitu (bez domény) - ověřeno vyhledáním, že tyto
# stránky reálně existují a jsou indexované.
LOCATION_SLUGS = {
    "brno": "prodej-bytu-brno",
    "hradec-kralove": "prodej-bytu-hradec-kralove",
    "pardubice": "prodej-bytu-pardubice",
}

PRICE_RE = re.compile(r"([\d\s]{4,})\s*Kč")
LAYOUT_RE = re.compile(r"\b([1-6]\s?\+\s?(?:kk|1))\b", re.IGNORECASE)
AREA_RE = re.compile(r"(\d+)\s*m2|(\d+)\s*m²")


def _parse_listings(html: str):
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    seen_ids = set()

    for a in soup.find_all("a", href=re.compile(r"/inzerat/\d+/")):
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

        href = a["href"]
        url = href if href.startswith("http") else f"https://reality.bazos.cz{href}"

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
    slug = LOCATION_SLUGS.get(seo)
    if not slug:
        return []

    url = f"https://reality.bazos.cz/inzeraty/{slug}/"
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    raw = _parse_listings(resp.text)[:MAX_LISTINGS_PER_SOURCE]
    print(f"[bazos] {seo}: staženo {len(resp.text)} znaků HTML, "
          f"nalezeno {len(raw)} inzerátů před filtrací")

    listings = []
    for c in raw:
        if not c["layout"] or c["layout"] not in [d.lower().replace(" ", "") for d in DISPOSITIONS]:
            continue
        if c["price_czk"] is None or c["price_czk"] > MAX_PRICE_CZK:
            continue
        if MAX_AREA_M2 and c["area_m2"] and c["area_m2"] > MAX_AREA_M2:
            continue

        listings.append({
            "source": "bazos.cz",
            "id": f"bazos-{c['id']}",
            "title": c["title"],
            "price_czk": c["price_czk"],
            "area_m2": c["area_m2"],
            "price_per_m2": round(c["price_czk"] / c["area_m2"]) if c["area_m2"] else None,
            "location": seo,
            "location_key": seo,
            "renovation_flag": matches_renovation(c["raw_text"]),
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
