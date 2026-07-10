"""
Sdílená logika pro filtr "vhodné k rekonstrukci" (flipování).

Pozor na past: fráze "po rekonstrukci" i "před rekonstrukcí" obě obsahují
slovo "rekonstrukce", ale znamenají opak. Proto se nejdřív kontrolují
vylučovací fráze (RENOVATION_EXCLUDE_KEYWORDS) a teprve pak ty hledané.
"""
from config import RENOVATION_KEYWORDS, RENOVATION_EXCLUDE_KEYWORDS


def matches_renovation(text: str) -> bool:
    if not text:
        return False
    t = text.lower()

    if any(exclude.lower() in t for exclude in RENOVATION_EXCLUDE_KEYWORDS):
        return False

    return any(keyword.lower() in t for keyword in RENOVATION_KEYWORDS)
