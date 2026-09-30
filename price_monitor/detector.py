"""Price history and anomaly detection.

The reference ("average list") price of a product is the mean of:
  * the list/strikethrough price shown by the retailer, when present, and
  * the mean of the prices observed in the last `history_days` days, when at
    least `min_history_samples` observations exist.
A product is anomalous when its current price is at least `threshold` below
that reference.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import Product


@dataclass
class Anomaly:
    product: Product
    reference_price: float
    discount: float
    basis: str


class History:
    def __init__(self, path: Path):
        self.path = path
        self.data = {"products": {}, "notified": {}}
        if path.exists():
            self.data.update(json.loads(path.read_text()))

    def samples(self, key: str, since: datetime) -> list[float]:
        entries = self.data["products"].get(key, {}).get("prices", [])
        return [p for ts, p in entries if datetime.fromisoformat(ts) >= since]

    def record(self, product: Product, now: datetime, keep_days: int) -> None:
        entry = self.data["products"].setdefault(product.key, {"prices": []})
        entry.update(name=product.name, url=product.url)
        if product.list_price:
            entry["list_price"] = product.list_price
        cutoff = now - timedelta(days=keep_days)
        entry["prices"] = [e for e in entry["prices"] if datetime.fromisoformat(e[0]) >= cutoff]
        entry["prices"].append([now.isoformat(timespec="seconds"), product.price])

    def recently_notified(self, product: Product, now: datetime, hours: int) -> bool:
        last = self.data["notified"].get(product.key)
        if not last:
            return False
        return (last["price"] == product.price
                and now - datetime.fromisoformat(last["at"]) < timedelta(hours=hours))

    def mark_notified(self, product: Product, now: datetime) -> None:
        self.data["notified"][product.key] = {"at": now.isoformat(timespec="seconds"), "price": product.price}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=1, ensure_ascii=False, sort_keys=True))


def reference_price(product: Product, history: History, config: dict, now: datetime) -> tuple[float, str] | None:
    since = now - timedelta(days=config.get("history_days", 30))
    samples = history.samples(product.key, since)
    parts, basis = [], []
    if product.list_price and product.list_price > product.price:
        parts.append(product.list_price)
        basis.append("prezzo di listino")
    if len(samples) >= config.get("min_history_samples", 3):
        parts.append(sum(samples) / len(samples))
        basis.append(f"media {len(samples)} rilevazioni")
    if not parts:
        return None
    return sum(parts) / len(parts), " + ".join(basis)


def is_excluded(product: Product, config: dict) -> bool:
    if product.price < config.get("min_price", 0):
        return True
    name = product.name.lower()
    return any(word.lower() in name for word in config.get("exclude_keywords", []))


def find_anomalies(products: list[Product], history: History, config: dict,
                   now: datetime | None = None) -> list[Anomaly]:
    """Detect anomalies against the stored history, then record current prices."""
    now = now or datetime.now(timezone.utc)
    threshold = config.get("threshold", 0.5)
    anomalies = []
    for product in products:
        if is_excluded(product, config):
            continue
        ref = reference_price(product, history, config, now)
        if ref:
            ref_price, basis = ref
            discount = 1 - product.price / ref_price
            if discount >= threshold and not history.recently_notified(
                    product, now, config.get("renotify_after_hours", 24)):
                anomalies.append(Anomaly(product, ref_price, discount, basis))
        history.record(product, now, keep_days=config.get("history_days", 30) * 2)
    return anomalies
