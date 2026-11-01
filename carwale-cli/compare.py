#!/usr/bin/env python3
"""Build automatic-variants-comparison.md from downloads/*/details.json.

One table per car: automatic variants by price. The first row lists everything;
each later row lists only what changes versus a reference variant (the previous
variant with the same engine + gearbox, or the base variant for a new powertrain).
"""
import json, re, sys
from pathlib import Path

ORDER = ["hyundai-creta", "kia-sonet", "honda-elevate", "skoda-kylaq", "honda-amaze", "kia-syros", "hyundai-venue"]
HIDE = {"", "No", "Not Tested", "Not Available", "0", "None"}
FLAG_ONLY = {"Keyless Start/ Button Start"}  # source says "1" for yes
POWER = ["Fuel Type", "Transmission Type", "Engine Type", "Displacement", "Max Engine Power", "Max Engine Torque"]
SKIP_FEATURES = {"Alloy Wheels", "Max Engine Torque", "Seating Capacity", "Drivetrain", "Turbocharger / Supercharger"}  # shown via powertrain


def lakh(n):
    return f"Rs. {n / 100000:.2f} Lakh" if n else "n/a"


def price(v):
    return v["on_road"] or v["ex_showroom"] or 1e12


def feat(v):
    out = {}
    for k, x in v["features"].items():
        if k in SKIP_FEATURES or x in HIDE:
            continue
        out[k] = "Yes" if (x == "Yes" or k in FLAG_ONLY) else x
    return out


def label(k, x):
    return k if x == "Yes" else f"{k}: {x}"


def power_line(v):
    s = v["specs"]
    parts = [s.get("Fuel Type"), s.get("Transmission Type"), s.get("Displacement"),
             s.get("Max Engine Power"), s.get("Max Engine Torque") or v["features"].get("Max Engine Torque")]
    if v["features"].get("Turbocharger / Supercharger") == "Turbocharged":
        parts.append("Turbo")
    return ", ".join(p for p in parts if p)


def pt(v):
    return (v["specs"].get("Fuel Type"), v["specs"].get("Transmission Type"), v["specs"].get("Max Engine Power"))


def esc(t):
    return t.replace("|", "\\|")


def diff(prev, cur):
    pf, cf = feat(prev), feat(cur)
    lines = []
    if power_line(prev) != power_line(cur):
        lines.append(f"Powertrain: {power_line(cur)}")
    for k, x in cf.items():
        if pf.get(k) != x:
            lines.append(("Adds " if k not in pf else "Changes ") + (label(k, x) if k not in pf else f"{k}: {pf[k]} → {x}"))
    for k, x in pf.items():
        if k not in cf:
            lines.append(f"Drops {label(k, x)}")
    return lines


def cell(lines):
    return "<br>".join("• " + esc(l) for l in lines) if lines else "No difference in the features CarWale lists (likely a paint, trim or cosmetic option)"


def main():
    base = Path("downloads")
    out = ["# Automatic variants comparison", "",
           "Source: carwale.com. Prices are CarWale's **Bangalore on-road prices** (ex-showroom + RTO/road tax, insurance, TCS and other charges). CarWale quotes them at city level only: it has no HSR Layout area option for Bangalore. Brochures are saved in `downloads/`. "
           "Only automatic gearboxes (CVT, DCT, torque converter) are included. Kia Sonet's clutchless-manual (iMT) variants are excluded.", "",
           "**How to read each table:** the first row is the cheapest automatic and lists everything it has. "
           "Every later row lists *only what changes* compared with the variant named in **vs**: "
           "that is the previous variant with the same engine and gearbox, or the base variant when the engine/gearbox changes. "
           "So reading down a column shows what you get for each upgrade.", ""]
    for slug_ in ORDER:
        d = json.loads((base / slug_ / "details.json").read_text())
        cp = {r["id"]: r for r in json.loads((base / slug_ / "prices-bangalore.json").read_text())["variants"]}
        for v in d["variants"]:
            r = cp.get(int(v["id"]), {})
            v["on_road"], v["ex_showroom"] = r.get("on_road"), r.get("ex_showroom")
        vs = sorted([v for v in d["variants"] if v["specs"].get("Transmission Type", "").startswith("Automatic")],
                    key=lambda v: (price(v), v["variant"]))
        o = d["overview"]
        out += [f"## {o['name']}", ""]
        if not vs:
            out += ["No automatic variants listed.", ""]
            continue
        out += [f"{len(vs)} automatic variants, {lakh(vs[0]['on_road'])} to {lakh(vs[-1]['on_road'])} on-road in Bangalore. "
                f"Brochure: [`downloads/{slug_}/brochure.pdf`](downloads/{slug_}/brochure.pdf). ", "",
                "| Variant | On-road price, Bangalore | Ex-showroom (Bangalore) | vs | What you get |", "|---|---|---|---|---|"]
        last = {}  # powertrain -> latest variant
        for i, v in enumerate(vs):
            if i == 0:
                ref, lines, refname = None, [power_line(v)] + [label(k, x) for k, x in feat(v).items()], "(base)"
            else:
                ref = last.get(pt(v)) or vs[0]
                lines, refname = diff(ref, v), ref["variant"]
            last[pt(v)] = v
            out.append(f"| {esc(v['variant'])} | {lakh(v['on_road'])} | {lakh(v['ex_showroom'])} | {esc(refname)} | {cell(lines)} |")
        out.append("")
    Path("automatic-variants-comparison.md").write_text("\n".join(out), encoding="utf-8")
    print("written", len(out), "lines")


if __name__ == "__main__":
    main()
