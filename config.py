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

# --- Byty vhodné k rekonstrukci (flipování) ---
# Netřídíme podle klíčových slov natvrdo (spousta bytů k rekonstrukci to
# v inzerátu vůbec nezmíní) - místo toho posíláme VŠECHNY byty splňující
# cenu/dispozici/plochu, a tyhle dva signály jen ZVÝRAZNÍME v e-mailu:
#
#  🔨 RENOVATION_KEYWORDS - inzerát to sám říká textem (viz níže)
#  💰 UNDERVALUED - cena za m² je výrazně pod průměrem ostatních nalezených
#     bytů ve stejné lokalitě v tomtéž běhu - silnější signál, funguje i
#     u bytů, které o svém stavu mlčí.
#
# Fráze, které i přes výskyt slova "rekonstrukce" znamenají, že byt je
# UŽ ZREKONSTRUOVANÝ, se z RENOVATION_KEYWORDS shody vždy vyloučí
# (viz RENOVATION_EXCLUDE_KEYWORDS níže).
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

# O kolik % musí být cena/m² pod průměrem lokality (v rámci téhož běhu),
# aby se byt označil jako 💰 podhodnocený. 0.15 = o 15 % levnější než
# průměr ostatních nalezených bytů ve stejném městě.
UNDERVALUE_THRESHOLD_PCT = 0.15

# Tvrdý strop na cenu/m² podle lokality (Kč/m²) - posílají se jen byty
# POD touto hranicí. Hlavní páka na omezení počtu e-mailů.
MAX_PRICE_PER_M2 = {
    "brno": 90_000,
    "hradec-kralove": 80_000,
    "pardubice": 80_000,
}

# Kam posílat notifikace
EMAIL_TO = "krejzic.honza@gmail.com"
EMAIL_FROM = "krejzic.honza@gmail.com"  # Gmail účet, ze kterého se bude odesílat

# Kolik nejnovějších inzerátů max kontrolovat za běh na portál
# (dostatečná rezerva, i kdyby přibylo hodně inzerátů mezi dvěma běhy)
MAX_LISTINGS_PER_SOURCE = 120

# Soubor, kam se ukládají už viděné inzeráty (aby se needlo posílat opakovaně)
SEEN_STORE_PATH = "data/seen.json"
