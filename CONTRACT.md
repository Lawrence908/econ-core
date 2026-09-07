# The series contract

Shared shape for every long series in the economic tracker collection
(diesel, debt, jobs, and whatever follows). `econ` will eventually overlay
all of them on common axes; this contract is what makes that possible without
refactoring five sites.

## Shape

```json
{
  "id": "us_unemployment_rate",
  "label": "US unemployment rate",
  "source": "BLS via FRED UNRATE",
  "source_url": "https://fred.stlouisfed.org/series/UNRATE",
  "units": "percent",
  "freq": "monthly",
  "confidence": "reported",
  "as_of": "2026-08-01",
  "obs": [["1948-01-01", 3.4], ["1948-02-01", 3.8]],
  "note": "optional, human-facing",
  "splices": [{"at": "1948-01-01", "note": "why the series changes basis here"}],
  "vintages": {"2008-10-01": [["2008-09-01", 6.1]]}
}
```

## Field rules

- **id** — snake_case, stable forever. Charts, prose tokens and the econ
  overlay all key on it.
- **source / source_url** — where the numbers actually come from, specific
  enough to re-fetch by hand. A series without provenance does not render.
- **units** — one unit per series. Convert at fetch time, never at render
  time. `percent`, `thousands_of_persons`, `persons`, `USD_per_gallon`, ...
- **freq** — `daily | weekly | monthly | quarterly | annual`.
- **confidence** — `reported` (filed or official), `estimate` (third-party or
  historical reconstruction), `projection` (a model's output). Drives colour
  and hatching on every page; mislabelling a projection as reported is a
  correctness bug, not a cosmetic one. One value per series: when a series
  changes confidence partway (historical estimates spliced onto an official
  series), publish two series and a splice note, never one series with a
  silent seam.
- **as_of** — the date of the last observation, always equal to `obs[-1][0]`.
- **obs** — `[iso_date, number]` pairs, ascending, gaps dropped rather than
  filled. Annual averages date as `YYYY-01-01`; a point-in-time annual reading
  dates as the day it describes (Canada's pre-1946 June estimates are
  `YYYY-06-01`) with the convention stated in `note`.
- **splices** — every seam in a stitched series, stated where it happens.
  Diesel's `splice_date` generalised.
- **vintages** — optional map of `as_published_on -> obs`, filled from ALFRED
  (keyed FRED API; the keyless CSV has no vintage access). Design intent:
  recession charts drawn from revised history overstate how obvious every
  turn was, so the page can show what was actually visible at the time. Ship
  the field empty and populate it later; the schema is the commitment.
- **disputed** — where sources genuinely disagree, a sibling field carrying
  the contradiction and its source. The disagreement is content; nothing is
  silently averaged or overwritten.

## Fetch policy

Keyless public endpoint primary, keyed API as documented fallback:

| Source | Keyless primary | Keyed fallback |
|---|---|---|
| FRED | `fredgraph.csv?id=X` | `api.stlouisfed.org` (also the only vintage route) |
| StatCan | WDS REST (no key exists) | — |
| Bank of Canada | Valet (no key exists) | — |
| EIA (diesel) | — | v2 API, HTML spot page as scrape fallback |

StatCan vectors are never guessed: `wds_vector(..., expect_title=...)`
verifies the live English title before returning numbers.

## Revision log

Machine-owned series files are rewritten wholesale, but every change of an
already-published observation gets a jsonl line (what, before, after, when
noticed). `econcore.log_revision` / `read_revisions`. Curated files follow
the debt rules instead: updaters touch only `value`/`as_of` of existing
entries, refuse >20% jumps, and never move `as_of` backwards.

## Recession shading

One dataset for the whole collection: `data/recessions.json`, built by
`tools/build-recessions.py`.

- **US** — derived mechanically from FRED `USREC` (NBER, monthly, 1854+).
  USREC marks the months from the peak's successor through the trough, so a
  band runs `first_1 - 1 month` (the peak) through `last_1` (the trough).
- **Canada** — C.D. Howe Institute Business Cycle Council chronology
  (Commentary 366, Table 1, 1929 onward, with the Council's category 1-5
  severity where assigned; COVID dated by the Council's 2021 declaration).
  No API exists; the dates are hardcoded with citations and change roughly
  once per business cycle.

Bands are `{"peak": "YYYY-MM", "trough": "YYYY-MM"}`, month precision,
shaded peak month through trough month inclusive.

## Normalization (reserved for econ)

The overlay site will need cross-unit comparison (a $/bbl crack against a
percentage-point spread). Convention reserved now: z-scores against a
trailing 10-year window, and percentile rank as the alternate view. Apps do
not pre-normalize; econ computes from `obs` at render time so the raw series
stays the artifact of record.
