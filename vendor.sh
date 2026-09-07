#!/usr/bin/env bash
# Vendor econ-core into an app: a stamped copy of econcore.py into <app>/api/
# and recessions.json into <app>/data/. Apps carry copies, not imports, so
# they keep working when nothing has run an install in three years. Re-run
# after changing econ-core; the stamp records what they got and when.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
dest="${1:?usage: vendor.sh /path/to/app}"

rev="$(git -C "$here" rev-parse --short HEAD 2>/dev/null || echo unversioned)"
stamp="econ-core ${rev}, vendored $(date -u +%F)"

mkdir -p "$dest/api" "$dest/data"

{
  echo "# VENDORED: ${stamp}. Do not edit here; edit econ-core and re-vendor."
  cat "$here/econcore.py"
} > "$dest/api/econcore.py"

python3 - "$here/data/recessions.json" "$dest/data/recessions.json" "$stamp" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
doc["vendored"] = sys.argv[3]
with open(sys.argv[2], "w") as fh:
    json.dump(doc, fh, indent=1)
    fh.write("\n")
PY

echo "vendored to ${dest} (${stamp})"
