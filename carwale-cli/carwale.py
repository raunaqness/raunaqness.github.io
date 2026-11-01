#!/usr/bin/env python3
"""carwale - fetch car details from carwale.com on the command line.

CarWale has no public API, but each page embeds its data as JSON in
`window.__INITIAL_STATE__`. This tool downloads pages and reads that JSON.
Standard library only. Be polite: responses are cached for an hour.

Examples:
  carwale.py brands
  carwale.py search swift
  carwale.py brand "maruti suzuki"
  carwale.py model maruti-suzuki swift
  carwale.py variants maruti-suzuki swift
  carwale.py variant maruti-suzuki swift lxi-petrol-manual --specs
  carwale.py reviews maruti-suzuki swift --pages 2
  carwale.py expert-reviews maruti-suzuki swift
Add --json to any command for machine-readable output.
"""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://www.carwale.com"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
CACHE_DIR = Path.home() / ".cache" / "carwale-cli"
CACHE_TTL = 3600


class CarWaleError(Exception):
    pass


# --------------------------------------------------------------- fetching
def fetch_html(path):
    url = path if path.startswith("http") else BASE + path
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / hashlib.sha1(url.encode()).hexdigest()
    if cache.exists() and time.time() - cache.stat().st_mtime < CACHE_TTL:
        return cache.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-IN,en;q=0.9"})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                html = r.read().decode("utf-8", "replace")
            cache.write_text(html, encoding="utf-8")
            return html
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise CarWaleError(f"Not found: {url}")
            last = e
        except urllib.error.URLError as e:
            last = e
        time.sleep(1.5 * (attempt + 1))
    raise CarWaleError(f"Could not fetch {url}: {last}")


def get_state(path):
    html = fetch_html(path)
    i = html.find("window.__INITIAL_STATE__")
    if i < 0:
        raise CarWaleError(f"No embedded data found at {path} (page layout may have changed).")
    j = html.index("=", i) + 1
    obj, _ = json.JSONDecoder().raw_decode(html[j:].lstrip())
    return obj


# ---------------------------------------------------------------- helpers
def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def specs_dict(items):
    out = {}
    for it in items or []:
        v = it.get("value")
        if v in (None, ""):
            continue
        unit = it.get("unitType") or ""
        out[it["itemName"]] = f"{v} {unit}".strip()
    return out


def price_text(po):
    return (po or {}).get("formattedPrice") or "n/a"


def brands():
    st = get_state("/new-cars/")["newCars"]["makeList"]
    return [{"name": m["makeName"], "slug": m["maskingName"]}
            for m in st if not m.get("isScooterOnlyMake")]


def resolve_brand(name):
    s = slug(name)
    allb = brands()
    for b in allb:
        if b["slug"] == s or slug(b["name"]) == s:
            return b["slug"]
    hits = [b for b in allb if s in b["slug"] or b["slug"] in s]
    if len(hits) == 1:
        return hits[0]["slug"]
    raise CarWaleError(f"Unknown brand '{name}'. Run `carwale.py brands` to list them.")


def brand_models(brand_slug):
    mp = get_state(f"/{brand_slug}-cars/")["makePage"]
    rows = []
    for m in mp["models"]:
        rows.append({
            "brand": m["makeName"], "brand_slug": m["makeMaskingName"],
            "model": m["modelName"], "slug": m["modelMaskingName"],
            "price": price_text(m.get("priceOverview")),
            "mileage": m.get("mileageRangeText"), "power": m.get("maxPowerRangeText"),
            "rating": m.get("modelAggregateRating"), "reviews": m.get("modelReviewCount"),
            "safety_rating": m.get("safetyRating"),
        })
    return rows


def model_page(brand, model):
    b = resolve_brand(brand)
    mp = get_state(f"/{b}-cars/{slug(model)}/")
    if "modelPage" not in mp:
        raise CarWaleError(f"No model page for {brand}/{model}.")
    return b, mp["modelPage"]


# --------------------------------------------------------------- commands
def cmd_brands(a):
    return brands()


def cmd_search(a):
    q = slug(a.query)
    toks = q.split("-")
    allb = brands()
    cand = [b for b in allb if any(t and t in b["slug"] for t in toks)]
    brand_toks = {t for b in cand for t in toks if t in b["slug"]}
    rest = [t for t in toks if t not in brand_toks]
    pool = cand if cand else allb  # no brand named in the query: scan all brands
    with ThreadPoolExecutor(6) as ex:
        lists = list(ex.map(lambda b: brand_models(b["slug"]), pool))
    out = []
    for models in lists:
        for m in models:
            hay = slug(f"{m['brand']} {m['model']}")
            if all(t in hay for t in (rest if cand else toks)):
                out.append(m)
    return out


def cmd_brand(a):
    return brand_models(resolve_brand(a.brand))


def cmd_model(a):
    b, mp = model_page(a.brand, a.model)
    d = mp["modelDetails"]
    po = d["priceOverview"]
    res = {
        "name": f"{d['makeName']} {d['rootName']}",
        "url": f"{BASE}/{b}-cars/{d['rootMaskingName']}/",
        "price_range": (po.get("formattedPriceRangeText") or "").replace("  ", " ").strip(),
        "starting_price": price_text(po),
        "on_road_starting": price_text(d.get("basePriceOverview")),
        "launched": (d.get("launchedOn") or "")[:10],
        "rating": d.get("modelAggregateRating"),
        "review_count": d.get("modelReviewCount"),
        "key_specs": {k["title"]: ", ".join(v["text"] for v in k["keySpecsValue"]) for k in mp.get("keySpecs", [])},
        "mileage": [
            {k: x[k] for k in ("fuelType", "transmission", "displacement", "mileageUnit", "arai", "userReportedArai") if x.get(k)}
            for x in mp.get("mileage", [])],
        "brochure": d.get("brochurePath"),
        "variants_count": len(mp.get("versions", [])),
        "summary": mp.get("versionTableSummary"),
    }
    return res


def variant_row(v):
    return {
        "variant": v["versionName"], "slug": v["versionMaskingName"], "id": v["versionId"],
        "price": price_text(v.get("priceOverview")),
        "specs": specs_dict(v.get("specsSummary")),
        "features": specs_dict(v.get("featureSpecs")),
    }


def cmd_variants(a):
    _, mp = model_page(a.brand, a.model)
    return [variant_row(v) for v in mp["versions"]]


def cmd_variant(a):
    _, mp = model_page(a.brand, a.model)
    want = slug(a.variant)
    hits = [v for v in mp["versions"] if want in (v["versionMaskingName"], slug(v["versionName"]))]
    hits = hits or [v for v in mp["versions"] if want in v["versionMaskingName"]]
    if not hits:
        names = ", ".join(v["versionMaskingName"] for v in mp["versions"])
        raise CarWaleError(f"Variant not found. Available: {names}")
    return variant_row(hits[0])


def cmd_reviews(a):
    b = resolve_brand(a.brand)
    m = slug(a.model)
    reviews, agg = [], None
    for p in range(1, a.pages + 1):
        st = get_state(f"/{b}-cars/{m}/user-reviews/?page={p}")["userReviewListing"]
        if agg is None:
            ar = st["aggregateRating"]
            agg = {
                "overall_rating": ar["overallRating"], "total_ratings": ar["totalRatings"],
                "review_count": ar["reviewCount"]["total"],
                "star_distribution": ar["specificRating"],
                "parameters": {x["MinHeading"] or x["Heading"]: round(x["Answer"], 2) for x in ar["reviewParameters"] if x.get("MinHeading") and not x["MinHeading"].endswith("?")},
            }
        for r in st["userReviewList"]["Reviews"]:
            reviews.append({
                "title": r["Title"], "rating": r["RatingInfo"]["UserRating"],
                "author": r["CustomerInfo"]["UserName"], "variant": r["VehicleInfo"]["VersionName"],
                "upvotes": r["Upvotes"], "text": r["Description"].strip(),
            })
    return {"summary": agg, "reviews": reviews}


def cmd_expert(a):
    _, mp = model_page(a.brand, a.model)
    return [{"title": e["title"], "author": e["authorName"], "date": e["displayDate"],
             "description": e["description"], "url": BASE + e["url"]} for e in mp["expertReviews"]]


# ----------------------------------------------------------------- output
def table(rows, cols):
    if not rows:
        print("(no results)")
        return
    w = [max(len(str(c[0])), *(len(str(r.get(c[1], "") if r.get(c[1]) is not None else "")) for r in rows)) for c in cols]
    print("  ".join(c[0].ljust(x) for c, x in zip(cols, w)))
    print("  ".join("-" * x for x in w))
    for r in rows:
        print("  ".join(str("" if r.get(c[1]) is None else r.get(c[1])).ljust(x) for c, x in zip(cols, w)))


def kv(d, indent=0):
    pad = " " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            print(f"{pad}{k}:")
            kv(v, indent + 2)
        elif isinstance(v, list):
            print(f"{pad}{k}:")
            for x in v:
                print(f"{pad}  - " + (", ".join(f"{a}={b}" for a, b in x.items()) if isinstance(x, dict) else str(x)))
        elif v not in (None, ""):
            print(f"{pad}{k}: {v}")


MODEL_COLS = [("Brand", "brand"), ("Model", "model"), ("Price", "price"), ("Mileage", "mileage"),
              ("Power", "power"), ("Rating", "rating"), ("Reviews", "reviews"), ("Slug", "slug")]


def render(cmd, data, a):
    if cmd == "brands":
        table(data, [("Brand", "name"), ("Slug", "slug")])
    elif cmd in ("search", "brand"):
        table(data, MODEL_COLS)
    elif cmd == "model":
        kv(data)
    elif cmd == "variants":
        rows = [{"variant": v["variant"], "price": v["price"], "slug": v["slug"],
                 "mileage": v["specs"].get("Mileage (ARAI)"), "power": v["specs"].get("Max Engine Power"),
                 "gearbox": v["specs"].get("Transmission Type"), "fuel": v["specs"].get("Fuel Type")}
                for v in data]
        table(rows, [("Variant", "variant"), ("Price", "price"), ("Fuel", "fuel"), ("Gearbox", "gearbox"),
                     ("Mileage", "mileage"), ("Power", "power"), ("Slug", "slug")])
    elif cmd == "variant":
        print(f"{data['variant']}  -  {data['price']}\n\nKey specs:")
        kv(data["specs"], 2)
        if a.specs:
            print("\nFeatures & specs:")
            kv(data["features"], 2)
    elif cmd == "reviews":
        s = data["summary"]
        print(f"Rating {s['overall_rating']}/5 from {s['total_ratings']} ratings, {s['review_count']} reviews")
        print("Stars:", ", ".join(f"{k}*={v}" for k, v in sorted(s["star_distribution"].items(), reverse=True)))
        print("Parameters:", ", ".join(f"{k} {v}" for k, v in s["parameters"].items()), "\n")
        for r in data["reviews"]:
            print(f"[{r['rating']}/5] {r['title']} - {r['author']} ({r['variant']}, {r['upvotes']} upvotes)")
            print("   " + r["text"].replace("\n", "\n   ") + "\n")
    elif cmd == "expert-reviews":
        for e in data:
            print(f"{e['title']} ({e['author']}, {e['date']})\n  {e['description']}\n  {e['url']}\n")


def main():
    p = argparse.ArgumentParser(prog="carwale", description="Fetch car details from carwale.com")
    p.add_argument("--json", action="store_true", help="print JSON")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("brands", help="list all brands").set_defaults(fn=cmd_brands)
    s = sub.add_parser("search", help="find models by name"); s.add_argument("query"); s.set_defaults(fn=cmd_search)
    s = sub.add_parser("brand", help="list a brand's models"); s.add_argument("brand"); s.set_defaults(fn=cmd_brand)
    for name, fn, h in [("model", cmd_model, "model overview, price, mileage"),
                        ("variants", cmd_variants, "all variants with prices"),
                        ("expert-reviews", cmd_expert, "expert review articles")]:
        s = sub.add_parser(name, help=h); s.add_argument("brand"); s.add_argument("model"); s.set_defaults(fn=fn)
    s = sub.add_parser("variant", help="one variant's specs"); s.add_argument("brand"); s.add_argument("model")
    s.add_argument("variant"); s.add_argument("--specs", action="store_true", help="include full feature list"); s.set_defaults(fn=cmd_variant)
    s = sub.add_parser("reviews", help="user ratings and reviews"); s.add_argument("brand"); s.add_argument("model")
    s.add_argument("--pages", type=int, default=1, help="pages of 10 reviews"); s.set_defaults(fn=cmd_reviews)
    a = p.parse_args()
    try:
        data = a.fn(a)
    except CarWaleError as e:
        sys.exit(f"error: {e}")
    if a.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        render(a.cmd, data, a)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:  # e.g. piped into `head`
        sys.stderr.close()
