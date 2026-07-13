"""
Hlavní vstupní bod hlídacího psa.

Spustí scrapery pro sreality.cz, bezrealitky.cz a bazos.cz, porovná
výsledky s dosud viděnými inzeráty (data/seen.json), a pokud najde něco
nového, pošle e-mail. Určeno ke spouštění periodicky přes GitHub Actions,
ale funguje stejně dobře i lokálně (`python main.py`).
"""
import sys
from collections import defaultdict

from scrapers import sreality, bezrealitky, bazos
from storage import load_seen, save_seen, filter_new, prune_old
from notifier import send_notification
from config import UNDERVALUE_THRESHOLD_PCT, MAX_PRICE_PER_M2


def _filter_by_price_per_m2(listings: list) -> list:
    """Tvrdý strop na cenu/m² podle lokality (config.MAX_PRICE_PER_M2).
    Byty bez known plochy/ceny za m² se pro jistotu taky vyřadí, ať
    neproklouzne něco neověřeného."""
    kept = []
    for l in listings:
        cap = MAX_PRICE_PER_M2.get(l.get("location_key"))
        ppm = l.get("price_per_m2")
        if cap and ppm and ppm <= cap:
            kept.append(l)
    return kept


def _flag_undervalued(listings: list) -> None:
    """Označí byty s cenou/m² výrazně pod průměrem stejné lokality
    (v rámci tohoto běhu) jako 'undervalued': True. Mutuje listings in-place."""
    by_location = defaultdict(list)
    for l in listings:
        if l.get("price_per_m2"):
            by_location[l.get("location_key")].append(l["price_per_m2"])

    averages = {
        loc: sum(prices) / len(prices)
        for loc, prices in by_location.items()
        if len(prices) >= 3  # s méně než 3 vzorky by průměr nic neříkal
    }

    for l in listings:
        avg = averages.get(l.get("location_key"))
        ppm = l.get("price_per_m2")
        l["undervalued"] = bool(
            avg and ppm and ppm <= avg * (1 - UNDERVALUE_THRESHOLD_PCT)
        )


def main():
    print("=== Hlídací pes na reality - start ===")

    all_listings = []
    for name, module in [("sreality", sreality), ("bezrealitky", bezrealitky), ("bazos", bazos)]:
        try:
            found = module.fetch_all()
            print(f"[{name}] celkem po filtraci kritérií: {len(found)}")
            all_listings.extend(found)
        except Exception as e:
            print(f"[{name}] CHYBA (portál se možná změnil): {e}")

    _flag_undervalued(all_listings)

    before_cap = len(all_listings)
    all_listings = _filter_by_price_per_m2(all_listings)
    print(f"Po stropu na cenu/m² (config.MAX_PRICE_PER_M2): {len(all_listings)} z {before_cap}")

    seen = load_seen()
    seen = prune_old(seen)
    new_listings = filter_new(all_listings, seen)

    print(f"Nových inzerátů k odeslání: {len(new_listings)}")

    if new_listings:
        try:
            send_notification(new_listings)
            print("E-mail odeslán.")
        except Exception as e:
            print(f"CHYBA při odesílání e-mailu: {e}")
            # I když se e-mail nepodaří odeslat, ID si stejně uložíme,
            # ať se aspoň příště neposílají duplicity donekonečna kvůli
            # dočasnému výpadku SMTP. Pokud bys chtěl radši retry příště,
            # zakomentuj řádek se save_seen níže.

    save_seen(seen)
    print("=== Hotovo ===")


if __name__ == "__main__":
    main()
    sys.exit(0)
