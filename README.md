# econ-core

Shared standards for the economic tracker collection (diesel, debt, jobs, and
the ones after them). Exists so that when `econ` overlays every series on
common axes, five sites do not need refactoring first.

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
./vendor.sh /mnt/storage/apps/jobs
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

Consumers: [jobs](../jobs) (jobs.chrislawrence.ca) and [debt](../debt)
(debt.chrislawrence.ca). Re-vendor each one deliberately when this repo
changes; the stamp at the top of each app's `api/econcore.py` says what it has,
and nothing warns you when an app falls behind.

`debt` is also where the FRED User-Agent behaviour documented in `econcore.py`
was measured: its own updater sent a custom UA on the keyless CSV path, so the
fallback had never once worked, silently, because a key was always set. That is
the argument for the fetch policy living here rather than being reimplemented
per app.
