"""
Odeslání e-mailu s novými inzeráty přes Gmail SMTP.

Potřebuje dvě proměnné prostředí:
  GMAIL_ADDRESS   - tvůj gmail (stejný jako config.EMAIL_FROM)
  GMAIL_APP_PASSWORD - "heslo pro aplikace" vygenerované v nastavení
                        Google účtu (Zabezpečení -> Ověřování ve dvou
                        krocích -> Hesla pro aplikace). Běžné heslo k účtu
                        fungovat nebude.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import EMAIL_TO, EMAIL_FROM


def _format_czk(value):
    if value is None:
        return "cena neuvedena"
    return f"{value:,.0f} Kč".replace(",", " ")


def _build_body(listings: list) -> str:
    lines = [f"Nalezeno {len(listings)} nových inzerátů odpovídajících kritériím:\n"]
    for l in listings:
        area = f", {l['area_m2']} m²" if l.get("area_m2") else ""
        lines.append(
            f"• [{l['source']}] {l['title']}\n"
            f"  {_format_czk(l['price_czk'])}{area}\n"
            f"  {l['url']}\n"
        )
    return "\n".join(lines)


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
    body = _build_body(listings)

    msg = MIMEMultipart()
    msg["From"] = gmail_address
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, app_password)
        server.sendmail(gmail_address, [EMAIL_TO], msg.as_string())
