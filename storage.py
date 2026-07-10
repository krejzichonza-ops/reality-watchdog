# Realitní hlídací pes (Brno / Hradec Králové / Pardubice)

Hlídá **sreality.cz**, **bezrealitky.cz** a **bazos.cz** a e-mailem pošle
upozornění na nové byty ke koupi 2+kk a větší (do 120 m²) do 8 mil. Kč.
Běží automaticky přes GitHub Actions každých ~15 minut, zdarma.

## Jak to funguje

- `scrapers/sreality.py` – čte data přímo z vestavěného JSON, který
  sreality.cz posílá v HTML stránky hledání (žádné neoficiální API).
- `scrapers/bezrealitky.py` a `scrapers/bazos.py` – parsují HTML výpis
  inzerátů.
- `data/seen.json` – seznam ID inzerátů, které už byly poslané, aby se
  needlo posílat opakovaně. Po každém běhu se commitne zpátky do repa.
- `main.py` – spustí všechny tři scrapery, porovná s `seen.json`, pošle
  e-mail s novinkami.

## Nastavení (cca 10 minut)

### 1. Vytvoř si GitHub repozitář

Nejjednodušeji přes GitHub web: New repository → nahraj tuhle složku
(nebo `git init`, `git add .`, `git commit`, `git push`). Repo může být
klidně **veřejné** – žádná citlivá data v kódu nejsou (heslo jde přes
Secrets, viz níže), veřejné repo navíc má neomezené GitHub Actions minuty
zdarma.

### 2. Vytvoř Gmail "Heslo pro aplikace"

Běžné heslo k Gmailu pro odesílání přes SMTP fungovat nebude. Potřebuješ:

1. Zapnout dvoufázové ověření na účtu (pokud ještě není): myaccount.google.com/security
2. Vytvořit heslo pro aplikace: myaccount.google.com/apppasswords
3. Zvolit název (např. "reality-watchdog") a zkopírovat vygenerované
   16znakové heslo (bez mezer).

### 3. Uprav `config.py`

- `EMAIL_TO` / `EMAIL_FROM` – tvůj e-mail
- `LOCATIONS`, `DISPOSITIONS`, `MAX_PRICE_CZK`, `MAX_AREA_M2` – kritéria
  hledání (výchozí nastavení odpovídá tomu, na čem jsme se domluvili:
  Brno/Hradec Králové/Pardubice, 2+kk a větší do 120 m², do 8 mil. Kč)

### 4. Přidej GitHub Secrets

V repozitáři: **Settings → Secrets and variables → Actions → New repository secret**

| Název | Hodnota |
|---|---|
| `GMAIL_ADDRESS` | tvůj gmail, ze kterého se bude odesílat |
| `GMAIL_APP_PASSWORD` | 16znakové heslo z kroku 2 |

### 5. Zapni workflow

Workflow (`.github/workflows/watchdog.yml`) se spustí automaticky podle
plánu (`*/15 * * * *`), jakmile je v repu. Pro rychlé ověření, že vše
funguje, jdi do repozitáře na záložku **Actions → Realitni hlidaci pes →
Run workflow** a spusť ho ručně. Podívej se do logu běhu - u každého
zdroje se vypíše, kolik inzerátů po filtraci našel; pokud je u některého
portálu 0 pořád dokola, něco je špatně (viz Ladění níže).

## Lokální test (doporučeno před prvním nasazením)

```bash
pip install -r requirements.txt
export GMAIL_ADDRESS="tvuj@gmail.com"
export GMAIL_APP_PASSWORD="xxxxxxxxxxxxxxxx"
python main.py
```

Při prvním spuštění pravděpodobně přijde e-mail se spoustou inzerátů
najednou (protože ještě nic není v `seen.json`) - to je v pořádku, další
běhy už budou posílat jen skutečné novinky.

## Ladění, pokud portál nic nevrací

Weby čas od času mění strukturu stránek, což může scraper rozbít. V logu
běhu (GitHub Actions → Runs → poslední běh) uvidíš u každého zdroje
chybovou hlášku nebo počet nalezených inzerátů. Pošli mi tu hlášku a
opravím to:

- **sreality.py** je nejrobustnější (čte strukturovaná data, ne HTML
  vzhled), měl by vydržet nejdéle.
- **bezrealitky.py** a **bazos.py** parsují viditelný text stránky -
  náchylnější na změny designu.

## Filtr na byty vhodné k rekonstrukci (flipování)

Kromě ceny/dispozice/plochy se teď hlídají i klíčová slova indikující, že
byt potřebuje rekonstrukci (viz `config.py` → `RENOVATION_KEYWORDS`), např.
"k rekonstrukci", "původní stav", "investiční příležitost", "po babičce" apod.

Aby se omylem nechytaly byty, které jsou už **po** rekonstrukci (opak toho,
co chceme), je tam i seznam `RENOVATION_EXCLUDE_KEYWORDS` ("po rekonstrukci",
"zrekonstruovaný" apod.) - pokud se objeví, inzerát se vždy vyřadí, i kdyby
někde jinde v textu bylo i slovo "rekonstrukce".

**Důležité pro sreality.cz:** výpis hledání neobsahuje popis inzerátu, jen
název (např. "Prodej bytu 2+kk 71 m²") - takže pro tenhle filtr scraper u
sreality navíc stahuje detail stránky u inzerátů, které už prošly cenou/
dispozicí/plochou (ne u všech, jen u kandidátů). Zvyšuje to počet požadavků,
ale jen o malé množství - v rámci free tieru GitHub Actions to není problém.

Filtr lze vypnout nastavením `REQUIRE_RENOVATION_KEYWORD = False` v `config.py`,
pokud budeš chtít vidět úplně všechny nabídky bez ohledu na stav.

## Úprava kritérií

Všechno je v `config.py`:
- přidat/ubrat lokalitu do `LOCATIONS`
- změnit `MAX_PRICE_CZK`, `MAX_AREA_M2`
- změnit `DISPOSITIONS` (např. přidat `"1+kk"`)

## Náklady

Řádově 0 Kč/měsíc – veřejný GitHub repozitář má neomezené GitHub Actions
minuty, Gmail SMTP je zdarma. Podrobný rozpad viz diskuze v chatu.
