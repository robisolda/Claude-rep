"""Entry point: python -m price_monitor [--config config.yaml] [--dry-run]."""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

from .detector import History, find_anomalies
from .fetch import fetch_browser, fetch_requests
from .notify import send_whatsapp
from .parsers import parse_page

log = logging.getLogger("price_monitor")


def collect(config: dict) -> list:
    session = requests.Session()
    products = []
    for source in config["sources"]:
        site, url = source["site"], source["url"]
        found = []
        html = fetch_requests(session, url)
        if html:
            found = parse_page(site, html, url)
        if not found:
            html = fetch_browser(url)
            if html:
                found = parse_page(site, html, url)
        log.info("%-10s %3d prodotti  %s", site, len(found), url)
        products.extend(found)
    return products


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Monitor anomalie di prezzo con notifiche WhatsApp")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--history", default="data/history.json")
    parser.add_argument("--dry-run", action="store_true", help="stampa i messaggi invece di inviarli")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = yaml.safe_load(Path(args.config).read_text())
    history = History(Path(args.history))

    products = collect(config)
    if not products:
        log.error("Nessun prodotto letto da nessuna fonte")
        return 1

    now = datetime.now(timezone.utc)
    anomalies = find_anomalies(products, history, config, now)
    log.info("%d prodotti analizzati, %d anomalie", len(products), len(anomalies))
    try:
        send_whatsapp(anomalies, dry_run=args.dry_run)
        # Only mark as notified once delivery succeeded, so failures are retried next run.
        for anomaly in anomalies:
            history.mark_notified(anomaly.product, now)
    finally:
        history.save()
    return 0


if __name__ == "__main__":
    sys.exit(main())
