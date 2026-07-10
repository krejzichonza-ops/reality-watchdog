"""
Jednoduché úložiště ID už viděných inzerátů - obyčejný JSON soubor v repu.
Při každém běhu se commitne zpět (viz GitHub Actions workflow), takže
funguje jako perzistentní paměť mezi jednotlivými spuštěními.
"""
import json
import os
from datetime import datetime, timezone

from config import SEEN_STORE_PATH

# Po kolika dnech smažeme staré záznamy, ať soubor neroste do nekonečna
MAX_AGE_DAYS = 60


def load_seen() -> dict:
    if not os.path.exists(SEEN_STORE_PATH):
        return {}
    try:
        with open(SEEN_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_seen(seen: dict) -> None:
    os.makedirs(os.path.dirname(SEEN_STORE_PATH), exist_ok=True)
    with open(SEEN_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)


def filter_new(listings: list, seen: dict) -> list:
    """Vrátí jen ty inzeráty, které ještě nejsou v `seen`, a zároveň
    do `seen` zapíše jejich ID s aktuálním časem (mutuje seen in-place)."""
    now = datetime.now(timezone.utc).isoformat()
    new_listings = []
    for listing in listings:
        if listing["id"] not in seen:
            seen[listing["id"]] = now
            new_listings.append(listing)
    return new_listings


def prune_old(seen: dict) -> dict:
    cutoff = datetime.now(timezone.utc).timestamp() - MAX_AGE_DAYS * 86400
    pruned = {}
    for listing_id, ts in seen.items():
        try:
            ts_val = datetime.fromisoformat(ts).timestamp()
        except ValueError:
            continue
        if ts_val >= cutoff:
            pruned[listing_id] = ts
    return pruned
