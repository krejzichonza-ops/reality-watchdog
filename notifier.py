"""
Odeslání e-mailu s novými inzeráty přes Gmail SMTP.

Potřebuje dvě proměnné prostředí:
  GMAIL_ADDRESS   - tvůj gmail (stejný jako config.EMAIL_FROM)
  GMAIL_APP_PASSWORD - "heslo pro aplikace" vygenerované v nastavení
                        Google účtu (Zabezpečení -> Ověřování ve dvou
                        krocích -> Hesla pro aplikace). Běžné heslo k účtu
                        fungovat nebude.

E-mail se posílá jako HTML (s prostým textem jako záložní verzí pro
klienty, co HTML nezobrazí) - potřebujeme tučně zvýraznit cenu/m².
"""
import os
import html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import EMAIL_TO, EMAIL_FROM


def _format_czk(value):
    if value is None:
        return "cena neuvedena"
    return f"{value:,.0f} Kč".replace(",", " ")


def _ordered_listings(listings: list) -> list:
    # Nejzajímavější (rekonstrukce a/nebo podhodnocené) nahoru
    return sorted(
        listings,
        key=lambda l: (l.get("renovation_flag", False) or l.get("undervalued", False)),
        reverse=True,
    )


def _build_text_body(listings: list) -> str:
    ordered = _ordered_listings(listings)
    flagged_count = sum(1 for l in ordered if l.get("renovation_flag") or l.get("undervalued"))
    lines = [
        f"Nalezeno {len(ordered)} nových inzerátů odpovídajících kritériím "
        f"({flagged_count} z nich se zvýrazněním 🔨/💰):\n"
    ]
    for l in ordered:
        area = f", {l['area_m2']} m²" if l.get("area_m2") else ""
        ppm = f" ({l['price_per_m2']:,.0f} Kč/m²)".replace(",", " ") if l.get("price_per_m2") else ""
        tags = ""
        if l.get("renovation_flag"):
            tags += "🔨 "
        if l.get("undervalued"):
            tags += "💰 "

        lines.append(
            f"• {tags}[{l['source']}] {l['title']}\n"
            f"  {_format_czk(l['price_czk'])}{area}{ppm}\n"
            f"  {l['url']}\n"
        )

    lines.append(
        "\n🔨 = inzerát sám zmiňuje rekonstrukci/původní stav\n"
        "💰 = cena/m² je výrazně pod průměrem ostatních nalezených bytů ve stejné lokalitě"
    )
    return "\n".join(lines)


def _build_html_body(listings: list) -> str:
    ordered = _ordered_listings(listings)
    flagged_count = sum(1 for l in ordered if l.get("renovation_flag") or l.get("undervalued"))

    rows = []
    for l in ordered:
        area = f", {l['area_m2']} m²" if l.get("area_m2") else ""
        ppm_html = ""
        if l.get("price_per_m2"):
            ppm_value = f"{l['price_per_m2']:,.0f} Kč/m²".replace(",", " ")
            ppm_html = f" (<b>{ppm_value}</b>)"

        tags = ""
        if l.get("renovation_flag"):
            tags += "🔨 "
        if l.get("undervalued"):
            tags += "💰 "

        title = html.escape(l["title"])
        source = html.escape(l["source"])
        url = html.escape(l["url"])
        price = html.escape(_format_czk(l["price_czk"]))
        area_esc = html.escape(area)

        rows.append(f"""
        <li style="margin-bottom:14px;">
          {tags}[{source}] {title}<br>
          {price}{area_esc}{ppm_html}<br>
          <a href="{url}">{url}</a>
        </li>
        """)

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;font-size:14px;">
      <p>Nalezeno {len(ordered)} nových inzerátů odpovídajících kritériím
      ({flagged_count} z nich se zvýrazněním 🔨/💰):</p>
      <ul style="padding-left:20px;">
        {''.join(rows)}
      </ul>
      <p style="color:#666;font-size:12px;">
        🔨 = inzerát sám zmiňuje rekonstrukci/původní stav<br>
        💰 = cena/m² je výrazně pod průměrem ostatních nalezených bytů ve stejné lokalitě
      </p>
    </body>
    </html>
    """


def send_notification(listings: list) -> None:
    if not listings:
        return

    gmail_address = os.environ.get("GMAIL_ADDRESS", EMAIL_FROM)
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not app_password:
        raise RuntimeError(
            "Chybí GMAIL_APP_PASSWORD (nastav jako GitHub Actions secret nebo "
            "proměnnou prostředí). Bez toho nejde e-mail odeslat."
        )

    subject = f"🏠 Hlídací pes: {len(listings)} nových bytů"

    msg = MIMEMultipart("alternative")
    msg["From"] = gmail_address
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    # Text verze musí jít první, HTML druhá - e-mailoví klienti zobrazí
    # poslední (nejbohatší) verzi, kterou umí vykreslit.
    msg.attach(MIMEText(_build_text_body(listings), "plain", "utf-8"))
    msg.attach(MIMEText(_build_html_body(listings), "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, app_password)
        server.sendmail(gmail_address, [EMAIL_TO], msg.as_string())
