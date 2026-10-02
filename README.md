# GiftScope (gifts.specversus.com)

Holiday gift guide for kids and teens (Amazon USA affiliate, tag `giftscope-20`).
Static site, Python stdlib only. Netlify runs `python3 tools/build.py` and publishes `dist/`.

## Data
- `data/finalists.csv` — selected products (asin, name, price, rating, theme, ages, image id).
- `data/verified_YYYY-MM-DD.txt` — latest price check (asin,price,rating,reviews). The newest file wins.
- `tools/make_products.py` — editorial (display name, interest, top pick, blurb) → `data/products.json`.
- `data/site.json` — age groups, interests, budgets and their page copy.

## Update prices
1. Re-check prices on Amazon and save a new `data/verified_<date>.txt`; set `CHECKED` in `tools/make_products.py`.
2. `python3 tools/make_products.py && python3 tools/build.py`
3. Commit and push → Netlify deploys.

## Add a product
Add a row to `data/finalists.csv`, its editorial entry in `ED` (tools/make_products.py), then rebuild.
The build fails if any Amazon link lacks `tag=giftscope-20` or `rel="sponsored nofollow noopener"`.

## Pages
`/` · `/gift-finder/` · `/age/<baby|toddler|preschool|5-to-7|8-to-12|teens>/` · `/interest/<theme>/` ·
`/budget/<under-10|under-25|under-50|under-100|over-100>/` · `/guides/<slug>/` (data/guides.json) · `/all-gifts/` · about, disclosure, privacy, 404, sitemap.xml.
Listing pages support URL filters, e.g. `/age/teens/?budget=under-25` (useful for Pinterest pins).
