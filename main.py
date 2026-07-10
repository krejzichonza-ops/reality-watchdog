"""
Konfigurace hlídacího psa na byty ke koupi.
Uprav podle potřeby - lokality, cena, dispozice, plocha.
"""

# Lokality - používají se jako:
#  - seo název v URL pro sreality.cz (napr. "brno", "hradec-kralove", "pardubice")
#  - textový filtr pro bazos.cz a bezrealitky.cz (hledá se v adrese/lokalitě inzerátu)
LOCATIONS = [
    {"sreality_seo": "brno", "match_text": ["brno"]},
    {"sreality_seo": "hradec-kralove", "match_text": ["hradec kralove", "hradec králové"]},
    {"sreality_seo": "pardubice", "match_text": ["pardubice"]},
]

# Dispozice, které nás zajímají (2+kk a větší)
DISPOSITIONS = ["2+kk", "2+1", "3+kk", "3+1", "4+kk", "4+1", "5+kk", "5+1", "6+"]

# Cenový strop v Kč
MAX_PRICE_CZK = 8_000_000

# Maximální plocha v m2 (0/None = neomezeno)
MAX_AREA_M2 = 120

# --- Filtr na byty vhodné k rekonstrukci (flipování) ---
# Pokud True, projdou dál jen inzeráty, jejichž text obsahuje některou
# z RENOVATION_KEYWORDS frází A ZÁROVEŇ žádnou z RENOVATION_EXCLUDE_KEYWORDS
# (ty vyřazují byty, které jsou už PO rekonstrukci - opak toho, co chceme).
REQUIRE_RENOVATION_KEYWORD = True

RENOVATION_KEYWORDS = [
    "k rekonstrukci",
    "před rekonstrukcí",
    "nutná rekonstrukce",
    "vyžaduje rekonstrukci",
    "vyžaduje opravu",
    "k opravě",
    "původní stav",
    "původní jádro",
    "k modernizaci",
    "špatný technický stav",
    "špatný stavební stav",
    "horší technický stav",
    "investiční příležitost",
    "developerská příležitost",
    "po babičce",
    "holobyt",
    "nevhodné k bydlení",
]

# Fráze, které i přes výskyt slova "rekonstrukce" znamenají, že byt je
# UŽ ZREKONSTRUOVANÝ - takové chceme naopak vyřadit.
RENOVATION_EXCLUDE_KEYWORDS = [
    "po rekonstrukci",
    "po kompletní rekonstrukci",
    "po celkové rekonstrukci",
    "kompletně zrekonstruovaný",
    "kompletně zrekonstruovaná",
    "zrekonstruovaný byt",
    "zrekonstruovaná",
    "čerstvě zrekonstruovaný",
    "nově zrekonstruovaný",
    "krásně zrekonstruovaný",
]

# Kam posílat notifikace
EMAIL_TO = "TVUJ_EMAIL@example.com"  # uprav
EMAIL_FROM = "TVUJ_EMAIL@example.com"  # Gmail účet, ze kterého se bude odesílat

# Kolik nejnovějších inzerátů max kontrolovat za běh na portál
# (dostatečná rezerva, i kdyby přibylo hodně inzerátů mezi dvěma běhy)
MAX_LISTINGS_PER_SOURCE = 120

# Soubor, kam se ukládají už viděné inzeráty (aby se needlo posílat opakovaně)
SEEN_STORE_PATH = "data/seen.json"
