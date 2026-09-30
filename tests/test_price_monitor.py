import json
from datetime import datetime, timedelta, timezone

import pytest

from price_monitor.detector import History, find_anomalies
from price_monitor.models import Product, parse_price
from price_monitor.notify import MAX_MESSAGE_CHARS, build_messages
from price_monitor.parsers import parse_page

CONFIG = {"threshold": 0.5, "min_history_samples": 3, "history_days": 30,
          "renotify_after_hours": 24, "min_price": 30, "exclude_keywords": ["cover"]}
NOW = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)


@pytest.mark.parametrize("raw, expected", [
    ("1.299,99 €", 1299.99),
    ("€ 499,00", 499.0),
    ("1.299 €", 1299.0),
    ("1299.99", 1299.99),
    ("1,299.99", 1299.99),
    ("349,-", 349.0),
    (799, 799.0),
    ("gratis", None),
    (None, None),
])
def test_parse_price(raw, expected):
    assert parse_price(raw) == expected


AMAZON_HTML = """
<div data-component-type="s-search-result" data-asin="B0TEST1234">
  <h2><a class="a-link-normal" href="/Apple-iPhone-15/dp/B0TEST1234/ref=sr_1_1?x=1"><span>Apple iPhone 15 128GB</span></a></h2>
  <span class="a-price"><span class="a-offscreen">399,00 €</span></span>
  <span class="a-price a-text-price"><span class="a-offscreen">979,00 €</span></span>
</div>
<div data-asin="B0NOPRICE"><h2>Senza prezzo</h2></div>
"""


def test_parse_amazon():
    [p] = parse_page("amazon", AMAZON_HTML, "https://www.amazon.it/s?k=x")
    assert (p.product_id, p.price, p.list_price) == ("B0TEST1234", 399.0, 979.0)
    assert p.url == "https://www.amazon.it/Apple-iPhone-15/dp/B0TEST1234"


def test_parse_jsonld_itemlist():
    data = {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "item": {"@type": "Product", "name": "Samsung Galaxy S24", "sku": "123",
                                        "url": "/p/galaxy-s24",
                                        "offers": {"@type": "Offer", "price": "429.90", "priceSpecification": {
                                            "@type": "UnitPriceSpecification",
                                            "priceType": "https://schema.org/ListPrice", "price": 899}}}}]}
    html = f'<script type="application/ld+json">{json.dumps(data)}</script>'
    [p] = parse_page("unieuro", html, "https://www.unieuro.it/online/Smartphone")
    assert (p.key, p.price, p.list_price) == ("unieuro:123", 429.9, 899.0)
    assert p.url == "https://www.unieuro.it/p/galaxy-s24"


def test_parse_next_data():
    state = {"props": {"pageProps": {"products": [
        {"productId": "M1", "name": "Xiaomi 14", "price": {"value": 300}, "strikePrice": 799, "url": "/it/product/_xiaomi-14-M1.html"},
        {"id": "nav", "title": "Menu"},
    ]}}}
    html = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(state)}</script>'
    [p] = parse_page("mediaworld", html, "https://www.mediaworld.it/it/category/x.html")
    assert (p.product_id, p.price, p.list_price) == ("M1", 300.0, 799.0)


def test_parse_html_cards():
    html = """
    <div class="product-tile">
      <a href="/prodotto/google-pixel-9"><h3 class="title">Google Pixel 9</h3></a>
      <span class="price-old"><del>899,00 €</del></span>
      <span class="price">449,00 €</span>
    </div>"""
    [p] = parse_page("euronics", html, "https://www.euronics.it/telefonia/")
    assert (p.name, p.price, p.list_price) == ("Google Pixel 9", 449.0, 899.0)


def _product(price, list_price=None, name="iPhone 15"):
    return Product("amazon", "A1", name, price, "https://www.amazon.it/dp/A1", list_price)


def test_anomaly_against_list_price(tmp_path):
    history = History(tmp_path / "h.json")
    [a] = find_anomalies([_product(400, list_price=1000)], history, CONFIG, NOW)
    assert a.discount == pytest.approx(0.6)


def test_no_anomaly_below_threshold(tmp_path):
    history = History(tmp_path / "h.json")
    assert find_anomalies([_product(600, list_price=1000)], history, CONFIG, NOW) == []


def test_anomaly_against_history_average(tmp_path):
    history = History(tmp_path / "h.json")
    for days in (3, 2, 1):
        find_anomalies([_product(800)], history, CONFIG, NOW - timedelta(days=days))
    # First run without enough history or list price: nothing to compare with.
    assert find_anomalies([_product(390)], History(tmp_path / "x.json"), CONFIG, NOW) == []
    [a] = find_anomalies([_product(390)], history, CONFIG, NOW)
    assert a.reference_price == 800 and "3 rilevazioni" in a.basis


def test_excluded_products(tmp_path):
    history = History(tmp_path / "h.json")
    products = [_product(10, list_price=100), _product(100, list_price=500, name="Cover iPhone 15")]
    assert find_anomalies(products, history, CONFIG, NOW) == []


def test_no_duplicate_notifications(tmp_path):
    path = tmp_path / "h.json"
    history = History(path)
    [a] = find_anomalies([_product(400, list_price=1000)], history, CONFIG, NOW)
    history.mark_notified(a.product, NOW)
    history.save()
    reloaded = History(path)
    assert find_anomalies([_product(400, list_price=1000)], reloaded, CONFIG, NOW + timedelta(hours=1)) == []
    # A further price drop is notified again.
    assert len(find_anomalies([_product(300, list_price=1000)], reloaded, CONFIG, NOW + timedelta(hours=2))) == 1


def test_messages_are_split(tmp_path):
    history = History(tmp_path / "h.json")
    products = [Product("unieuro", str(i), f"Smartphone {i} " + "x" * 100, 100, f"https://u.it/{i}", 500)
                for i in range(30)]
    anomalies = find_anomalies(products, history, CONFIG, NOW)
    messages = build_messages(anomalies)
    assert len(messages) > 1
    assert all(len(m) <= MAX_MESSAGE_CHARS for m in messages)
    assert sum(m.count("🚨") for m in messages) == 30
