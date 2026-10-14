# shopify-products-json

A small, polite collector for the public `/products.json` feed that most Shopify stores expose, plus the results of our test of 68 US-facing brand stores.

Full write-up: **[Scraping Shopify Stores via the /products.json Endpoint](https://jsonengine.com/blog/scrape-shopify-products-json/)**

## What we found (October 8, 2026)

| Finding | Detail |
|---|---|
| 50 of 68 domains returned a catalog | others returned 403/404 or did not answer; we did not verify their platform |
| Max 250 products per page | `limit=500` still returned 250 |
| Hard cap at 25,000 products | page 101 with `limit=250` → HTTP 400 `Page * Limit exceeds the 25000 limit.` |
| Short pages mid-catalog | 4 of 50 stores; one returned 58 of 250 on page 1 of an 855-product catalog |
| Prices in shop currency | USD for 47 stores, plus CAD, GBP and EUR; not adjusted to the visitor's market |

Raw results: [`data/shopify_products_json_test_2026-10-08.csv`](data/shopify_products_json_test_2026-10-08.csv)

## Usage

```bash
pip install -r requirements.txt
python collect.py www.allbirds.com --out allbirds.csv
```

The script:

- pages with `?limit=250&page=N` and stops on an **empty** page, not a short one
- detects the 25,000-product cap and reports it
- backs off on HTTP 429
- deduplicates by product ID and compares the total with `/meta.json`
- writes one CSV row per variant (price, compare-at price, availability, SKU)

Keep the default one-second delay. Most catalogs need one to four requests.

## Notes

- `/products.json` is not the Admin API. Cursor pagination (`page_info`) does not apply here.
- Prices are strings in the shop's base currency. For market-specific prices use `/products/{handle}.js` or locale-prefixed URLs.
- Only collect what stores publish publicly, keep request rates low and respect a store's request to stop.

## License

- Code: [MIT](LICENSE)
- Data in `data/`: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please credit "JsonEngine (jsonengine.com)" with a link.

Built by [JsonEngine](https://jsonengine.com): managed web scraping, price monitoring and ready-to-use e-commerce datasets.
