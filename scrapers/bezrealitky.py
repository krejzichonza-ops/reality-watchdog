"""
Scraper pro bezrealitky.com (majitel bezrealitky.cz, data identická).

Přístup: každá karta inzerátu v HTML výpisu obsahuje několik odkazů
(fotky + nadpis), které všechny míří na stejné /properties-flats-houses/{id}-...
URL. Nový inzerát tedy pozná podle změny ID v pořadí odkazů - rozsekáme
syrové HTML na bloky mezi jednotlivými ID a v každém bloku regexem najdeme
cenu, dispozici a plochu. Tohle je odolnější vůči změnám CSS tříd než
hledání přes selektory.

Ověřeno na živém webu (červenec 2026), nicméně pokud bezrealitky přestrukturují
stránku, může být potřeba tuhle logiku doladit.
"""
import re
import requests
from bs4 import BeautifulSoup

from config import LOCATIONS, DISPOSITIONS, MAX_PRICE_CZK, MAX_AREA_M2, MAX_LISTINGS_PER_SOURCE
from keywords import matches_renovation

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "cs-CZ,cs;q=0.9",
}

# okres slug pro každou lokalitu - ověřeno pro Brno, u zbylých dvou zkontroluj
# při prvním běhu (log vypíše počet nalezených inzerátů na lokalitu).
LOCATION_SLUGS = {
    "brno": "okres-brno-mesto",
    "hradec-kralove": "okres-hradec-kralove",
    "pardubice": "okres-pardubice",
}

DETAIL_HREF_RE = re.compile(r'href="(?:https://www\.bezrealitky\.com)?(/properties-flats-houses/(\d+)-[^"]+)"')
PRICE_RE = re.compile(r"CZK\s*([\d,\s]+?)(?:\(|<)")
LAYOUT_RE = re.compile(r"\b([1-6]\+(?:kk|1))\b", re.IGNORECASE)


def _strip_tags(html_fragment: str) -> str:
    return BeautifulSoup(html_fragment, "html.parser").get_text(" ", strip=True)


def _parse_cards(html: str):
    matches = list(DETAIL_HREF_RE.finditer(html))
    if not matches:
        return []

    first_pos = {}
    order = []
    for m in matches:
        listing_id = m.group(2)
        if listing_id not in first_pos:
            # posuň začátek bloku na začátek obklopující <a ...> značky,
            # jinak BeautifulSoup dostane rozbitý fragment (uprostřed atributu)
            tag_start = html.rfind("<a", 0, m.start())
            first_pos[listing_id] = tag_start if tag_start != -1 else m.start()
            order.append((listing_id, m.group(1)))

    positions = [first_pos[lid] for lid, _ in order]
    listings = []
    for i, (listing_id, href) in enumerate(order):
        start = positions[i]
        end = positions[i + 1] if i + 1 < len(positions) else min(start + 4000, len(html))
        block = html[start:end]
        text = _strip_tags(block)

        price_m = PRICE_RE.search(block) or PRICE_RE.search(text)
        price = None
        if price_m:
            digits = re.sub(r"[^\d]", "", price_m.group(1))
            if digits:
                price = int(digits)

        layout_m = LAYOUT_RE.search(text)
        area_m = re.search(r"(\d+)\s*m²", text)

        url = href if href.startswith("http") else f"https://www.bezrealitky.com{href}"

        title_m = re.search(r"(Flat for sale|Prodej bytu)[^<]{0,80}", text)
        title = title_m.group(0) if title_m else text[:80]

        listings.append({
            "id": listing_id,
            "title": title,
            "price_czk": price,
            "layout": layout_m.group(1).lower() if layout_m else None,
            "area_m2": int(area_m.group(1)) if area_m else None,
            "url": url,
            "raw_text": text,
        })

    return listings


def fetch_new_listings(location: dict) -> list:
    seo = location["sreality_seo"]
    slug = LOCATION_SLUGS.get(seo)
    if not slug:
        return []

    url = f"https://www.bezrealitky.com/listings/offer-sale/flat/{slug}"
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    raw_cards = _parse_cards(resp.text)[:MAX_LISTINGS_PER_SOURCE]
    print(f"[bezrealitky] {seo}: staženo {len(resp.text)} znaků HTML, "
          f"nalezeno {len(raw_cards)} karet inzerátů před filtrací")

    listings = []
    for c in raw_cards:
        # Pokud dispozici neumíme rozpoznat (např. "Studio", "2 bedroom"),
        # radši inzerát přeskočíme, než abychom posílali falešné shody.
        if not c["layout"] or c["layout"] not in [d.lower() for d in DISPOSITIONS]:
            continue
        if c["price_czk"] is None or c["price_czk"] > MAX_PRICE_CZK:
            continue
        if MAX_AREA_M2 and c["area_m2"] and c["area_m2"] > MAX_AREA_M2:
            continue

        listings.append({
            "source": "bezrealitky.cz",
            "id": f"bezrealitky-{c['id']}",
            "title": c["title"],
            "price_czk": c["price_czk"],
            "area_m2": c["area_m2"],
            "price_per_m2": round(c["price_czk"] / c["area_m2"]) if c["area_m2"] else None,
            "location": location["sreality_seo"],
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
            print(f"[bezrealitky] {loc['sreality_seo']}: {len(found)} shod po filtraci")
            all_listings.extend(found)
        except Exception as e:
            print(f"[bezrealitky] Chyba při stahování pro {loc['sreality_seo']}: {e}")
    return all_listings
