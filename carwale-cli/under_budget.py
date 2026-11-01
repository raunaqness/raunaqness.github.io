#!/usr/bin/env python3
"""Build variants-under-15-lakh-bangalore.md: every automatic variant of the
saved cars whose Bangalore on-road price is below the limit, in one table grouped by car."""
import json, sys
from pathlib import Path

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 1_500_000
ORDER = ["hyundai-creta", "kia-sonet", "honda-elevate", "skoda-kylaq", "honda-amaze", "kia-syros", "hyundai-venue"]
HIDE = {"", "No", "Not Tested", "Not Available", "0", "None"}
FLAG_ONLY = {"Alloy Wheels", "Keyless Start/ Button Start"}
SKIP = {"Alloy Wheels", "Max Engine Torque", "Seating Capacity", "Drivetrain", "Turbocharger / Supercharger"}


def esc(t):
    return str(t).replace("|", "\\|")


def feature_list(v):
    out = []
    for k, x in v["features"].items():
        if k in SKIP or x in HIDE:
            continue
        out.append(k if (x == "Yes" or k in FLAG_ONLY) else f"{k}: {x}")
    return out


def lakh(n):
    return f"{n / 100000:.2f}"


def main():
    base = Path("downloads")
    rows, per_car = [], {}
    for c in ORDER:
        d = json.loads((base / c / "details.json").read_text())
        cp = {r["id"]: r for r in json.loads((base / c / "prices-bangalore.json").read_text())["variants"]}
        name = d["overview"]["name"]
        picked = []
        autos = [v for v in d["variants"] if v["specs"].get("Transmission Type", "").startswith("Automatic")]
        for v in autos:
            r = cp.get(int(v["id"]), {})
            if r.get("on_road") and r["on_road"] < LIMIT:
                picked.append((r["on_road"], v, r))
        picked.sort(key=lambda t: (t[0], t[1]["variant"]))
        per_car[name] = (len(picked), len(autos))
        for on, v, r in picked:
            s = v["specs"]
            rows.append({"car": name, "variant": v["variant"], "fuel": s.get("Fuel Type", ""), "gearbox": s.get("Transmission Type", ""),
                         "cc": str(s.get("Displacement", "")).replace(" cc", ""), "power": str(s.get("Max Engine Power", "")).replace(" bhp", "").strip(),
                         "torque": str(v["features"].get("Max Engine Torque", s.get("Max Engine Torque", ""))).replace(" Nm", "").strip(),
                         "on_road": on, "ex": r.get("ex_showroom"), "features": feature_list(v)})
    lim = f"Rs. {LIMIT / 100000:g} lakh"
    L = [f"# Automatic variants under {lim}, Bangalore on-road", "",
         f"{len(rows)} automatic variants (CVT, DCT, torque converter) of Creta, Sonet, Elevate, Kylaq, Amaze, Syros and Venue "
         f"with a CarWale on-road price in Bangalore below {lim}. Grouped by car, cheapest first. Manual and iMT variants are excluded.", "",
         "Prices are in lakh (Rs.) from carwale.com at Bangalore city level (no HSR Layout option exists). On-road = ex-showroom + RTO/road tax, "
         "insurance, TCS, FASTag and other charges; no accessories, warranty extensions or discounts. "
         "Exact rupee amounts are in each variant's heading. Regenerate with `python3 under_budget.py [limit_in_rupees]`.", "",
         "## Counts", "", "| Car | Under limit | Automatics total |", "|---|---|---|"]
    L += [f"| {k} | {a_} | {b_} |" for k, (a_, b_) in per_car.items()]
    L += [f"| **Total** | **{sum(a_ for a_, _ in per_car.values())}** | **{sum(b_ for _, b_ in per_car.values())}** |", ""]
    cars = []
    for r in rows:
        if r["car"] not in cars:
            cars.append(r["car"])
    for car in cars:
        cr = [r for r in rows if r["car"] == car]
        L += [f"## {car}", "", "| Variant | On-road (L) | Ex-showroom (L) | Engine | Power |", "|---|---|---|---|---|"]
        for r in cr:
            L.append(f"| {esc(r['variant'])} | {lakh(r['on_road'])} | {lakh(r['ex'])} | {r['fuel']} {r['cc']} cc, {r['gearbox'].replace('Automatic (', '').rstrip(')')} | {r['power']} bhp / {r['torque']} Nm |")
        L += ["", "### Features by variant", ""]
        for r in cr:
            L += [f"#### {esc(r['variant'])}", "", f"Rs. {r['on_road']:,} on-road / Rs. {r['ex']:,} ex-showroom", ""]
            L += [f"- {f}" for f in r["features"]] + [""]
    Path("variants-under-15-lakh-bangalore.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(per_car)


if __name__ == "__main__":
    main()
