"""Email delivery through Gmail SMTP (requires a Google App Password)."""
from __future__ import annotations

import html
import logging
import os
import smtplib
from email.message import EmailMessage

from .detector import Anomaly

log = logging.getLogger(__name__)

SITE_LABELS = {"mediaworld": "MediaWorld", "unieuro": "Unieuro", "euronics": "Euronics", "amazon": "Amazon.it"}
SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 465


def _site(a: Anomaly) -> str:
    return SITE_LABELS.get(a.product.site, a.product.site)


def build_subject(anomalies: list[Anomaly]) -> str:
    best = max(anomalies, key=lambda a: a.discount)
    subject = f"Anomalia prezzo -{best.discount:.0%}: {best.product.name[:60]} ({_site(best)})"
    if len(anomalies) > 1:
        subject += f" e altre {len(anomalies) - 1}"
    return subject


def build_text(anomalies: list[Anomaly]) -> str:
    blocks = [
        f"{_site(a)} -{a.discount:.0%}\n{a.product.name}\n"
        f"Prezzo: {a.product.price:,.2f} € (riferimento {a.reference_price:,.2f} € – {a.basis})\n"
        f"{a.product.url}"
        for a in anomalies
    ]
    return "Anomalie di prezzo rilevate:\n\n" + "\n\n".join(blocks)


def build_html(anomalies: list[Anomaly]) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(_site(a))}</td>"
        f"<td><a href=\"{html.escape(a.product.url)}\">{html.escape(a.product.name)}</a></td>"
        f"<td style=\"text-align:right\"><b>{a.product.price:,.2f} €</b></td>"
        f"<td style=\"text-align:right\"><s>{a.reference_price:,.2f} €</s><br><small>{html.escape(a.basis)}</small></td>"
        f"<td style=\"text-align:right;color:#c00\"><b>-{a.discount:.0%}</b></td></tr>"
        for a in sorted(anomalies, key=lambda a: -a.discount)
    )
    return (
        "<p>Anomalie di prezzo rilevate:</p>"
        "<table cellpadding=\"6\" style=\"border-collapse:collapse;font-family:sans-serif\" border=\"1\">"
        "<tr><th>Negozio</th><th>Prodotto</th><th>Prezzo</th><th>Riferimento</th><th>Sconto</th></tr>"
        f"{rows}</table>"
    )


def build_email(anomalies: list[Anomaly], sender: str, recipient: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = build_subject(anomalies)
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(build_text(anomalies))
    msg.add_alternative(build_html(anomalies), subtype="html")
    return msg


def send_email(anomalies: list[Anomaly], dry_run: bool = False) -> None:
    if not anomalies:
        return
    user = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not (user and password):
        dry_run = True
        log.warning("GMAIL_USER / GMAIL_APP_PASSWORD not set: printing the email instead")
    msg = build_email(anomalies, user or "price-monitor", os.environ.get("EMAIL_TO") or user or "")
    if dry_run:
        print(f"Subject: {msg['Subject']}\n\n{build_text(anomalies)}")
        return
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.login(user, password.replace(" ", ""))
        smtp.send_message(msg)
