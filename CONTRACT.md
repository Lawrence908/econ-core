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

## Status block

Every page carries one sentence at the top saying what its data currently
says. The pill that renders it is cosmetic; the block behind it is the
artifact, and it is what the hub reads to build a row per tracker without
knowing anything about the page that produced it.

Published at `analysis.status.headline`, and mirrored onto `/api/health`:

```json
{
  "state": "signal",
  "label": "Above the WWII peak",
  "detail": "gross debt 122.6% of GDP against 119.1% in 1946",
  "as_of": "2026-01-01",
  "rule": "Gross federal debt exceeds its 1946 peak of 119.1% of GDP."
}
```

- **state** — `signal` or `normal`, and nothing else. Two values because the
  hub sorts on it. A page may use a more specific word for its own CSS hook
  (yield shades on `inverted`); the payload field stays binary.
- **label** — the bold clause: a state, not a number. "Inverted", "Standards
  neutral", "Above the WWII peak". Reads as an assertion about the world.
- **detail** — the figures that justify the label, in the page's own units.
  Not normalized here; econ normalizes at render time.
- **as_of** — the observation the state was computed from, never the fetch
  time. A stale reading is still a true reading about its own date, and the
  hub has to be able to say which.
- **rule** — the printed threshold, in words. A different rule gives a
  different state, so the rule travels with the state exactly as the episode
  tables carry theirs. A `state` without a `rule` is an opinion.

`signal_active` (`state == "signal"`) stays at `analysis.status` top level
because `/api/health` already publishes it and monitoring keys on it.

Per-series entries under `analysis.status.<series_id>` stay page-local and
free-form: they feed that page's own tiles and prose, and the hub ignores
them.

A page with no threshold worth printing does not get a fabricated one. Where
no alarm rule exists in the literature, the rule is stated as what it is:
debt scores a level against a dated historical record, diesel scores the
current margin's percentile against its own full history. Both are printed,
and both are recomputable from `obs` by a reader who doubts them.

Two anchors that are easy to get wrong, and are therefore pinned here.
Gross federal debt and debt held by the public are different series with
different records: gross peaked at 119.1% of GDP in 1946 (FRED
`GFDGDPA188S`) and again at 125.9% in 2020, while debt held by the public
peaked at 106.3% in 1946 (FRED `FYPUGDA188S`) and has not since been
passed. Quoting a gross level against the 106.3% record, or the reverse,
overstates the comparison by roughly thirteen points. Any status rule
citing "the WWII peak" states which series it means.

## Normalization (reserved for econ)

The overlay site will need cross-unit comparison (a $/bbl crack against a
percentage-point spread). Convention reserved now: z-scores against a
trailing 10-year window, and percentile rank as the alternate view. Apps do
not pre-normalize; econ computes from `obs` at render time so the raw series
stays the artifact of record.
