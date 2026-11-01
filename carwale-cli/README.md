# carwale-cli

Command-line tool to fetch car details from [carwale.com](https://www.carwale.com): models, variants, prices, specs, and user/expert reviews.

CarWale has no public API. Each page embeds its data as JSON (`window.__INITIAL_STATE__`), which this tool reads. If CarWale changes its pages, parsing may break. Check CarWale's terms of use before heavy or commercial use. Responses are cached for an hour in `~/.cache/carwale-cli`.

Requires Python 3.9+, no dependencies.

```
python3 carwale.py brands                                   # all brands
python3 carwale.py search swift                             # find models by name (try "hyundai creta")
python3 carwale.py brand hyundai                            # a brand's models, prices, ratings
python3 carwale.py model maruti-suzuki swift                # overview, price range, mileage
python3 carwale.py variants maruti-suzuki swift             # every variant with price and key specs
python3 carwale.py variant maruti-suzuki swift lxi-petrol-manual --specs
python3 carwale.py reviews maruti-suzuki swift --pages 3    # rating breakdown + user reviews (10/page)
python3 carwale.py expert-reviews maruti-suzuki swift
```

Add `--json` before the command for JSON output, e.g. `python3 carwale.py --json model hyundai creta`.
Prices are CarWale's average ex-showroom prices (not city-specific).
