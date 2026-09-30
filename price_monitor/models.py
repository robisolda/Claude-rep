from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Product:
    site: str
    product_id: str
    name: str
    price: float
    url: str
    list_price: float | None = None

    @property
    def key(self) -> str:
        return f"{self.site}:{self.product_id}"


_NUMBER_RE = re.compile(r"\d[\d.,\s  ]*")


def parse_price(value) -> float | None:
    """Convert an Italian or plain price ("1.299,99 €", "1299.99", 1299) to float."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    match = _NUMBER_RE.search(str(value))
    if not match:
        return None
    text = re.sub(r"[\s  ]", "", match.group(0)).rstrip(".,")
    if "," in text and "." in text:
        # The right-most separator is the decimal one.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        whole, _, frac = text.rpartition(",")
        text = f"{whole.replace(',', '')}.{frac}" if len(frac) <= 2 else text.replace(",", "")
    elif text.count(".") == 1 and len(text.split(".")[1]) == 3:
        # "1.299" is a thousands separator in Italian notation.
        text = text.replace(".", "")
    elif text.count(".") > 1:
        text = text.replace(".", "")
    try:
        price = float(text)
    except ValueError:
        return None
    return price if price > 0 else None
