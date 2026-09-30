"""WhatsApp delivery via CallMeBot (free, personal use) or Twilio."""
from __future__ import annotations

import logging
import os

import requests

from .detector import Anomaly

log = logging.getLogger(__name__)

SITE_LABELS = {"mediaworld": "MediaWorld", "unieuro": "Unieuro", "euronics": "Euronics", "amazon": "Amazon.it"}
MAX_MESSAGE_CHARS = 1500


def format_anomaly(a: Anomaly) -> str:
    p = a.product
    return (f"🚨 *{SITE_LABELS.get(p.site, p.site)}* -{a.discount:.0%}\n"
            f"{p.name}\n"
            f"💶 {p.price:,.2f} € (rif. {a.reference_price:,.2f} € – {a.basis})\n"
            f"{p.url}")


def build_messages(anomalies: list[Anomaly]) -> list[str]:
    """Group anomalies into messages that fit WhatsApp/API size limits."""
    messages, current = [], "⚠️ Anomalie di prezzo rilevate"
    for block in map(format_anomaly, anomalies):
        if len(current) + len(block) + 2 > MAX_MESSAGE_CHARS:
            messages.append(current)
            current = block
        else:
            current += "\n\n" + block
    messages.append(current)
    return messages


def send_callmebot(text: str) -> None:
    resp = requests.get("https://api.callmebot.com/whatsapp.php", params={
        "phone": os.environ["WHATSAPP_PHONE"],
        "apikey": os.environ["CALLMEBOT_APIKEY"],
        "text": text,
    }, timeout=30)
    resp.raise_for_status()


def send_twilio(text: str) -> None:
    sid = os.environ["TWILIO_ACCOUNT_SID"]
    resp = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        auth=(sid, os.environ["TWILIO_AUTH_TOKEN"]),
        data={
            "From": f"whatsapp:{os.environ['TWILIO_WHATSAPP_FROM']}",
            "To": f"whatsapp:{os.environ['WHATSAPP_PHONE']}",
            "Body": text,
        },
        timeout=30,
    )
    resp.raise_for_status()


def send_whatsapp(anomalies: list[Anomaly], dry_run: bool = False) -> None:
    if not anomalies:
        return
    if os.environ.get("TWILIO_ACCOUNT_SID"):
        sender = send_twilio
    elif os.environ.get("CALLMEBOT_APIKEY"):
        sender = send_callmebot
    else:
        dry_run = True
        log.warning("No WhatsApp credentials configured: printing messages instead")
    for message in build_messages(anomalies):
        if dry_run:
            print(message, end="\n\n")
        else:
            sender(message)
