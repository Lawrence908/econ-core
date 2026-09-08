# econ-core

Shared standards for the economic tracker collection (diesel, debt, jobs,
yield, credit, freight, housing, lending, consumer, output, and the ones after
them). Exists so that when `econ` overlays every series on common axes, ten
sites do not need refactoring first.

Three things live here and nowhere else:

- **CONTRACT.md** + `schema/series.schema.json` — the shape every long
  series is published in: id, provenance, units, frequency, confidence,
  `[date, value]` observations, splice notes, and a vintages field designed
  in now (ALFRED as-published views) even where it ships empty.
- **econcore.py** — the fetchers (FRED keyless CSV primary with keyed
  fallback, ALFRED vintages, StatCan WDS with title verification, Bank of
  Canada Valet), contract validation, the shared revision-log helpers.
- **data/recessions.json** — one recession-band dataset for every chart:
  US derived from FRED USREC, Canada hardcoded from the C.D. Howe Business
  Cycle Council chronology. Rebuild with `python3 tools/build-recessions.py`.

## Vendoring, not importing

```bash
./vendor.sh ../jobs
```

copies a stamped `econcore.py` into the app's `api/` and a stamped
`recessions.json` into its `data/`. Apps deliberately carry copies: every app
in this collection has to keep working in three years with no installs run in
as long, so there is no shared runtime path to rot. The stamp (git short rev
plus date) says exactly what each app got; re-vendor deliberately, per app,
when econ-core changes.

## Change rules

- `obs` shape and required fields are append-only; breaking the contract
  means bumping `VERSION` in econcore.py and re-vendoring every app in the
  same change.
- New Canadian recessions: add to `CDHOWE_BANDS` in tools/build-recessions.py
  with a citation, rerun, re-vendor.
- New fetchers belong here when a second app needs them, not before.

## Consumers

Ten apps vendor this repo, all private under `Lawrence908`:

| App | Repo |
|---|---|
| consumer | [Lawrence908/consumer](https://github.com/Lawrence908/consumer) |
| credit | [Lawrence908/credit](https://github.com/Lawrence908/credit) |
| debt | [Lawrence908/debt](https://github.com/Lawrence908/debt) |
| diesel | [Lawrence908/diesel](https://github.com/Lawrence908/diesel) |
| freight | [Lawrence908/freight](https://github.com/Lawrence908/freight) |
| housing | [Lawrence908/housing](https://github.com/Lawrence908/housing) |
| jobs | [Lawrence908/jobs](https://github.com/Lawrence908/jobs) |
| lending | [Lawrence908/lending](https://github.com/Lawrence908/lending) |
| output | [Lawrence908/output](https://github.com/Lawrence908/output) |
| yield | [Lawrence908/yield](https://github.com/Lawrence908/yield) |

Do not trust that table for a re-vendor sweep. It has been written by hand three
times and was wrong all three: two apps, then six, then eight. Each time the
correction was written, the enumeration below immediately found more. Run it
instead, which is also how you find the stragglers:

```bash
for d in ../*/; do
  [ -f "$d/api/econcore.py" ] && printf '%-10s %s\n' "$(basename "$d")" \
    "$(sed -n '1s/.*econ-core \([a-f0-9]*\),.*/\1/p' "$d/api/econcore.py")"
done
```

Re-vendor deliberately, per app; the stamp says what each one got, and nothing
warns you when an app falls behind.

This is not hypothetical. The C.D. Howe URL correction in 113b1c7 was vendored
into debt and jobs while the other eight kept the redirecting URL, because
whoever did it believed the collection was two apps.

### Every stamp is currently stale

On 2026-09-07 this repo's history was rewritten to change commit authorship,
which gave every commit a new SHA. The stamps in all ten apps were written
against the old ones and no longer resolve here:

| Stamp in the apps | Now |
|---|---|
| 273cdef | c8328a2 |
| f0eaa96 | 1b01686 |
| 6015b74 | 113b1c7 |
| 0447df7 | 2f044ab |

The vendored `econcore.py` is byte-identical either way, so nothing is broken at
runtime; what is broken is the stamp's one job, which is to say what an app got
in a way you can look up. Re-vendoring every app restamps them and is the fix.
Worth knowing before the next rewrite: rewriting econ-core's history invalidates
every consumer's stamp at once, and nothing warns you.

Vendoring also does not reach a URL an app has written into its own prose.
`jobs/src/index.html` and `yield/src/index.html` both cite the Council's
declaration with a hardcoded href, which has to be corrected by hand and needs
a rebuild rather than a data refresh, since the HTML is baked into the image
while `data/recessions.json` is bind-mounted.

`debt` is also where the FRED User-Agent behaviour documented in `econcore.py`
was measured: its own updater sent a custom UA on the keyless CSV path, so the
fallback had never once worked, silently, because a key was always set. That is
the argument for the fetch policy living here rather than being reimplemented
per app.

## Data and attribution

The MIT licence covers this repository's code. It does not cover the data, which is not
mine: every series belongs to the body that publishes it and carries that body's own terms.
Each series names its `source` and `source_url` so the original is always one click away.

`data/recessions.json` is assembled here, not authored: the US bands are derived from
the NBER chronology via FRED `USREC`, and the Canadian bands are transcribed from the
C.D. Howe Institute Business Cycle Council chronology. Both belong to their publishers.

Series reached through FRED are redistributed by the Federal Reserve Bank of St. Louis
under [its terms of use](https://fred.stlouisfed.org/legal/), which ask that you cite the
original source and note that it was accessed via FRED.
