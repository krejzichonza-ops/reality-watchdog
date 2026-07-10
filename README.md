"""
Hlavní vstupní bod hlídacího psa.

Spustí scrapery pro sreality.cz, bezrealitky.cz a bazos.cz, porovná
výsledky s dosud viděnými inzeráty (data/seen.json), a pokud najde něco
nového, pošle e-mail. Určeno ke spouštění periodicky přes GitHub Actions,
ale funguje stejně dobře i lokálně (`python main.py`).
"""
import sys

from scrapers import sreality, bezrealitky, bazos
from storage import load_seen, save_seen, filter_new, prune_old
from notifier import send_notification


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
