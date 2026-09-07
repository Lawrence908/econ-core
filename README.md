# econ-core

Shared standards for the economic tracker collection (diesel, debt, jobs,
yield, credit, freight, housing, lending, and the ones after them). Exists so
that when `econ` overlays every series on common axes, eight sites do not need
refactoring first.

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

## Consumers

Eight apps vendor this repo:

| App | Repo |
|---|---|
| credit | [Lawrence908/credit](https://github.com/Lawrence908/credit) |
| debt | [Lawrence908/debt](https://github.com/Lawrence908/debt) |
| diesel | [Lawrence908/diesel](https://github.com/Lawrence908/diesel) |
| freight | [Lawrence908/freight](https://github.com/Lawrence908/freight) |
| housing | [Lawrence908/housing](https://github.com/Lawrence908/housing) |
| jobs | local only, not on GitHub |
| lending | [Lawrence908/lending](https://github.com/Lawrence908/lending) |
| yield | [Lawrence908/yield](https://github.com/Lawrence908/yield) |

Do not trust that table for a re-vendor sweep. It was written by hand twice and
was wrong both times, first at two apps and then at six. Enumerate from disk
instead, which is also how you find the stragglers:

```bash
for d in /mnt/storage/apps/*/; do
  [ -f "$d/api/econcore.py" ] && printf '%-10s %s\n' "$(basename "$d")" \
    "$(sed -n '1s/.*econ-core \([a-f0-9]*\),.*/\1/p' "$d/api/econcore.py")"
done
```

Re-vendor deliberately, per app; the stamp says what each one got, and nothing
warns you when an app falls behind.

This is not hypothetical. The C.D. Howe URL correction in 6015b74 was vendored
into debt and jobs while the other six kept the redirecting URL, because
whoever did it believed the collection was two apps.

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
