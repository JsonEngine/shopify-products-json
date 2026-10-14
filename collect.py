#!/usr/bin/env python3
"""Collect a Shopify store's public catalog from /products.json.

Handles the things that break naive scrapers:
  * stops on an EMPTY page, never on a short one (some stores return short pages mid-catalog)
  * detects the hard cap: HTTP 400 "Page * Limit exceeds the 25000 limit."
  * backs off on HTTP 429
  * deduplicates by product id and checks the total against /meta.json

Usage:
  python collect.py www.allbirds.com
  python collect.py www.allbirds.com --out allbirds.csv --delay 1.5
"""
import argparse
import csv
import sys
import time

import requests

USER_AGENT = "Mozilla/5.0 (compatible; shopify-products-json/1.0; +https://github.com/JsonEngine/shopify-products-json)"
S = requests.Session()
S.headers["User-Agent"] = USER_AGENT


def get(url, tries=4):
    for i in range(tries):
        r = S.get(url, timeout=30)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 5 * (i + 1)))
            print(f"  429, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue
        return r
    r.raise_for_status()
    return r


def collect(domain, delay=1.0):
    base = f"https://{domain}"
    meta = get(f"{base}/meta.json").json()
    products, page, capped = {}, 0, False
    while True:
        page += 1
        r = get(f"{base}/products.json?limit=250&page={page}")
        if r.status_code == 400 and "25000" in r.text:
            capped = True  # page * limit > 25,000: the public feed stops here
            break
        r.raise_for_status()
        batch = r.json().get("products", [])
        if not batch:  # stop on EMPTY, not short
            break
        for p in batch:
            products[p["id"]] = p
        print(f"  page {page}: {len(batch)} products", file=sys.stderr)
        time.sleep(delay)
    return meta, list(products.values()), capped


def rows(domain, meta, products):
    for p in products:
        for v in p.get("variants", []):
            yield {
                "domain": domain,
                "currency": meta.get("currency"),
                "product_id": p["id"],
                "handle": p.get("handle"),
                "title": p.get("title"),
                "vendor": p.get("vendor"),
                "product_type": p.get("product_type"),
                "variant_id": v["id"],
                "sku": v.get("sku"),
                "variant": v.get("title"),
                "price": v.get("price"),
                "compare_at_price": v.get("compare_at_price"),
                "available": v.get("available"),
                "updated_at": v.get("updated_at"),
            }


def main():
    ap = argparse.ArgumentParser(description="Collect a Shopify catalog from /products.json")
    ap.add_argument("domain", help="store domain, e.g. www.allbirds.com")
    ap.add_argument("--out", default="catalog.csv", help="output CSV (default: catalog.csv)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between pages (default: 1.0)")
    a = ap.parse_args()

    meta, products, capped = collect(a.domain, a.delay)
    expected = meta.get("published_products_count")
    print(f"{a.domain}: {len(products)} products collected, meta.json says {expected}, "
          f"currency {meta.get('currency')}, capped={capped}")
    data = list(rows(a.domain, meta, products))
    if not data:
        print("No products found.")
        return
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=data[0].keys())
        w.writeheader()
        w.writerows(data)
    print(f"Wrote {len(data)} variant rows to {a.out}")


if __name__ == "__main__":
    main()
