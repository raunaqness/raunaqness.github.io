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


def features(v):
    out = []
    for k, x in v["features"].items():
        if k in SKIP or x in HIDE:
            continue
        out.append(k if (x == "Yes" or k in FLAG_ONLY) else f"{k}: {x}")
    return "; ".join(out)


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
            rows.append((name, v["variant"], s.get("Fuel Type", ""), s.get("Transmission Type", ""), s.get("Displacement", ""),
                         s.get("Max Engine Power", ""), v["features"].get("Max Engine Torque", s.get("Max Engine Torque", "")),
                         on, r.get("ex_showroom"), features(v)))
    L = [f"# Automatic variants under Rs. {LIMIT / 100000:g} lakh on-road in Bangalore", "",
         "Data source file. Every automatic variant (CVT, DCT, torque converter; manual and clutchless-manual iMT excluded) of Hyundai Creta, Kia Sonet, Honda Elevate, Skoda Kylaq, Honda Amaze, Kia Syros and Hyundai Venue "
         f"whose CarWale on-road price in Bangalore is below Rs. {LIMIT:,}. Grouped by car, cheapest first within each car.", "",
         "- **Prices** are in rupees, from carwale.com, quoted at Bangalore city level (CarWale has no HSR Layout option). On-road = ex-showroom + RTO/road tax, insurance, TCS, FASTag and other charges. It excludes accessories, warranty extensions and discounts.",
         "- **Features** are the ~33 fields CarWale lists per variant (only those present). Cosmetic differences between trims may not appear.",
         "- Regenerate with `python3 under_budget.py [limit_in_rupees]` after refreshing `downloads/` (`carwale.py download <brand> <model> --city bangalore`).", "",
         "| Car | Variant | Fuel | Gearbox | Engine (cc) | Power (bhp) | Torque (Nm) | On-road, Bangalore (Rs.) | Ex-showroom, Bangalore (Rs.) | Features |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        pw = str(r[5]).replace(" bhp", "").strip()
        tq = str(r[6]).replace(" Nm", "").strip()
        L.append(f"| {esc(r[0])} | {esc(r[1])} | {r[2]} | {r[3]} | {str(r[4]).replace(' cc','')} | {pw} | {tq} | {r[7]:,} | {r[8]:,} | {esc(r[9])} |")
    L += ["", "## Counts", "", "| Car | Automatic variants under limit | Total automatic variants |", "|---|---|---|"]
    L += [f"| {k} | {a} | {b} |" for k, (a, b) in per_car.items()]
    L.append(f"| **Total** | **{sum(a for a, _ in per_car.values())}** | **{sum(b for _, b in per_car.values())}** |")
    Path("variants-under-15-lakh-bangalore.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(per_car)


if __name__ == "__main__":
    main()
