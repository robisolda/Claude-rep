"""Extract products and prices from retailer listing pages.

Every site goes through the same pipeline: a site-specific HTML parser (when
one exists), then schema.org JSON-LD, then a heuristic scan of the JSON state
embedded by JavaScript frameworks (Next.js, Nuxt, ...). The first strategy that
yields products wins.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .models import Product, parse_price

NAME_KEYS = ("name", "productName", "title", "displayName")
PRICE_KEYS = ("finalPrice", "salePrice", "currentPrice", "sellingPrice", "offerPrice", "price")
LIST_PRICE_KEYS = (
    "listPrice", "strikePrice", "strikeThroughPrice", "strikethroughPrice",
    "crossedPrice", "originalPrice", "fullPrice", "oldPrice", "basePrice",
    "regularPrice", "rrp", "msrp", "recommendedRetailPrice",
)
ID_KEYS = ("sku", "productId", "gtin13", "gtin", "ean", "mpn", "code", "id")
URL_KEYS = ("url", "link", "productUrl", "href", "canonicalUrl")


def parse_page(site: str, html: str, base_url: str) -> list[Product]:
    soup = BeautifulSoup(html, "html.parser")
    # Structured data is more reliable than scraping CSS classes, so the
    # generic HTML card parser only runs when nothing else found products.
    strategies = [parse_jsonld, parse_embedded_state, parse_html_cards]
    specific = SITE_PARSERS.get(site)
    if specific:
        strategies.insert(0, specific)
    for strategy in strategies:
        products = _dedupe(strategy(site, soup, base_url))
        if products:
            return products
    return []


def _dedupe(products: list[Product]) -> list[Product]:
    seen: dict[str, Product] = {}
    for product in products:
        if product.key not in seen:
            seen[product.key] = product
    return list(seen.values())


def _product_id_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1] or url


# --- Amazon -----------------------------------------------------------------

def parse_amazon(site: str, soup: BeautifulSoup, base_url: str) -> list[Product]:
    products = []
    for card in soup.select("[data-asin]"):
        asin = card.get("data-asin", "").strip()
        if not asin:
            continue
        title = card.select_one("h2") or card.select_one("[data-cy=title-recipe]")
        current = card.select_one(".a-price:not(.a-text-price) .a-offscreen")
        if not title or not current:
            continue
        price = parse_price(current.get_text())
        if price is None:
            continue
        strike = card.select_one(".a-price.a-text-price .a-offscreen")
        link = card.select_one("a[href*='/dp/']")
        url = urljoin(base_url, link["href"]) if link else f"https://www.amazon.it/dp/{asin}"
        products.append(Product(
            site=site,
            product_id=asin,
            name=" ".join(title.get_text().split()),
            price=price,
            url=url.split("?")[0].split("/ref=")[0],
            list_price=parse_price(strike.get_text()) if strike else None,
        ))
    return products


# --- Generic HTML cards (MediaWorld, Unieuro, Euronics) ---------------------

_STRIKE_SELECTORS = "del, s, [class*='strike'], [class*='Strike'], [class*='old'], [class*='Old'], [class*='crossed'], [class*='list-price'], [class*='listPrice']"


def parse_html_cards(site: str, soup: BeautifulSoup, base_url: str) -> list[Product]:
    """Fallback for tile-based listings that expose prices only in markup."""
    products = []
    selector = "[data-test*='product'], [class*='product-tile'], [class*='productTile'], [class*='product-card'], [class*='ProductCard'], article"
    for card in soup.select(selector):
        link = card.select_one("a[href]")
        price_el = card.select_one("[class*='price']:not(del):not(s), [data-test*='price']")
        if not link or not price_el:
            continue
        struck = card.select_one(_STRIKE_SELECTORS)
        if struck is not None and (price_el is struck or struck in price_el.parents):
            candidates = [el for el in card.select("[class*='price'], [data-test*='price']")
                          if el is not struck and struck not in el.parents and el not in struck.parents]
            if not candidates:
                continue
            price_el = candidates[0]
        price = parse_price(price_el.get_text())
        title_el = card.select_one("h2, h3, [class*='title'], [class*='name']") or link
        name = " ".join(title_el.get_text().split())
        if price is None or not name:
            continue
        url = urljoin(base_url, link["href"])
        products.append(Product(
            site=site,
            product_id=_product_id_from_url(url),
            name=name,
            price=price,
            url=url,
            list_price=parse_price(struck.get_text()) if struck else None,
        ))
    return products


# --- schema.org JSON-LD -----------------------------------------------------

def _iter_jsonld(soup: BeautifulSoup):
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        yield from _walk(data)


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def _types(node: dict) -> set[str]:
    value = node.get("@type", [])
    return set(value if isinstance(value, list) else [value])


def parse_jsonld(site: str, soup: BeautifulSoup, base_url: str) -> list[Product]:
    products = []
    for node in _iter_jsonld(soup):
        if "Product" not in _types(node) or not node.get("name"):
            continue
        offers = node.get("offers")
        if isinstance(offers, list):
            offers = offers[0] if offers else None
        if not isinstance(offers, dict):
            continue
        price = parse_price(offers.get("price") or offers.get("lowPrice"))
        if price is None:
            continue
        list_price = None
        specs = offers.get("priceSpecification") or []
        for spec in specs if isinstance(specs, list) else [specs]:
            if isinstance(spec, dict) and re.search(r"(ListPrice|StrikethroughPrice|MSRP)", str(spec.get("priceType", ""))):
                list_price = parse_price(spec.get("price"))
        url = urljoin(base_url, node.get("url") or offers.get("url") or base_url)
        product_id = next((str(node[k]) for k in ("sku", "gtin13", "gtin", "mpn", "productID") if node.get(k)), None)
        products.append(Product(
            site=site,
            product_id=product_id or _product_id_from_url(url),
            name=str(node["name"]).strip(),
            price=price,
            url=url,
            list_price=list_price,
        ))
    return products


# --- Embedded JS state (Next.js / Nuxt / window.__STATE__) ------------------

_STATE_RE = re.compile(r"window\.__[A-Z_]+__\s*=\s*(\{.*?\})\s*;?\s*(?:</script>|$)", re.S)


def _embedded_json(soup: BeautifulSoup):
    for script in soup.find_all("script"):
        text = script.string or ""
        if script.get("type") == "application/json" or script.get("id") == "__NEXT_DATA__":
            try:
                yield json.loads(text)
            except json.JSONDecodeError:
                pass
            continue
        for match in _STATE_RE.finditer(text):
            try:
                yield json.loads(match.group(1))
            except json.JSONDecodeError:
                pass


def _first(node: dict, keys) -> object:
    for key in keys:
        value = node.get(key)
        if isinstance(value, dict):
            value = value.get("value") or value.get("amount") or value.get("price")
        if value not in (None, "", 0):
            return value
    return None


def parse_embedded_state(site: str, soup: BeautifulSoup, base_url: str) -> list[Product]:
    products = []
    for data in _embedded_json(soup):
        for node in _walk(data):
            name = _first(node, NAME_KEYS)
            price = parse_price(_first(node, PRICE_KEYS))
            if not isinstance(name, str) or price is None:
                continue
            url_value = _first(node, URL_KEYS)
            url = urljoin(base_url, url_value) if isinstance(url_value, str) else base_url
            product_id = _first(node, ID_KEYS)
            if product_id is None and url == base_url:
                continue
            list_price = parse_price(_first(node, LIST_PRICE_KEYS))
            products.append(Product(
                site=site,
                product_id=str(product_id) if product_id is not None else _product_id_from_url(url),
                name=name.strip(),
                price=price,
                url=url,
                list_price=list_price if list_price and list_price > price else None,
            ))
    return products


SITE_PARSERS = {
    "amazon": parse_amazon,
}
