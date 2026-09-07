#!/usr/bin/env python3
"""Build data/recessions.json: the collection's shared recession bands.

US bands derive mechanically from FRED USREC (NBER recession indicator,
monthly, 1854+): USREC is 1 from the month after the peak through the trough,
so peak = first 1 minus one month, trough = last 1. Spot checks against
NBER's published table: 1929-08..1933-03, 2007-12..2009-06, 2020-02..2020-04.

Canada has no machine-readable chronology, so the C.D. Howe Institute
Business Cycle Council dates are hardcoded below with their citations. They
change roughly once per business cycle; when the Council dates a new
recession, add it here and rerun.
"""

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from econcore import fred_series  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "recessions.json")

CDHOWE_URL = "https://www.cdhowe.org/wp-content/uploads/2024/12/Commentary_366_0-2.pdf"

# Commentary 366 (Cross & Bergevin, 2012), Table 1: Historical Chronology of
# Canadian Recessions since 1926. Monthly peak/trough plus the Council's
# category (1 mildest .. 5 most severe).
CDHOWE_BANDS = [
    {"peak": "1929-04", "trough": "1933-02", "category": 5},
    {"peak": "1937-11", "trough": "1938-06", "category": 5},
    {"peak": "1947-08", "trough": "1948-03", "category": 2},
    {"peak": "1951-04", "trough": "1951-12", "category": 3},
    {"peak": "1953-07", "trough": "1954-07", "category": 4},
    {"peak": "1957-03", "trough": "1958-01", "category": 3},
    {"peak": "1960-03", "trough": "1961-03", "category": 3},
    {"peak": "1974-12", "trough": "1975-03", "category": 2},
    {"peak": "1980-01", "trough": "1980-06", "category": 1},
    {"peak": "1981-06", "trough": "1982-10", "category": 4},
    {"peak": "1990-03", "trough": "1992-04", "category": 4},
    {"peak": "2008-10", "trough": "2009-05", "category": 4},
    # Dated by the Council's 2021 declaration; no category was assigned, only
    # "the shortest and deepest recession since the Great Depression".
    # The /council-reports/ path this was first cited at now 302s to
    # /publication/; storing the settled URL rather than the one that redirects,
    # so the link checkers in the consuming apps do not report it every run.
    {"peak": "2020-02", "trough": "2020-04", "category": None,
     "source_url": "https://cdhowe.org/publication/cd-howe-institute-business-cycle-council-declares-end-Covid-19-recession/"},
]


def month_shift(year_month, delta):
    year, month = int(year_month[:4]), int(year_month[5:7])
    index = year * 12 + (month - 1) + delta
    return "%04d-%02d" % (index // 12, index % 12 + 1)


def us_bands():
    obs = fred_series("USREC")
    first_month = obs[0][0][:7]
    bands, start, last = [], None, None
    for date, value in obs:
        month = date[:7]
        if value >= 0.5:
            if start is None:
                start = month
            last = month
        elif start is not None:
            bands.append(_band(start, last, first_month))
            start = None
    if start is not None:
        bands.append(dict(_band(start, last, first_month), ongoing=True))
    return bands, obs[-1][0]


def _band(start, last, first_month):
    if start == first_month:
        # USREC begins inside a recession; inventing a peak one month before
        # the data starts would assert a date the series cannot support.
        return {"peak": start, "trough": last, "truncated_start": True,
                "note": "USREC starts mid-recession; the true peak predates the series."}
    return {"peak": month_shift(start, -1), "trough": last}


def main():
    bands, usrec_as_of = us_bands()
    doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "builder": "econ-core/tools/build-recessions.py",
        "convention": "Shade peak month through trough month inclusive.",
        "us": {
            "source": "NBER business cycle dates via FRED USREC",
            "source_url": "https://fred.stlouisfed.org/series/USREC",
            "derivation": "USREC is 1 from the month after the peak through the trough; peak = first 1 minus one month, trough = last 1.",
            "as_of": usrec_as_of,
            "bands": bands,
        },
        "ca": {
            "source": "C.D. Howe Institute Business Cycle Council, Commentary 366 (Cross & Bergevin 2012), Table 1; COVID-19 dates from the Council's 2021 declaration",
            "source_url": CDHOWE_URL,
            "note": "No API exists; hardcoded, category is the Council's severity scale (1 mildest to 5 most severe).",
            "bands": CDHOWE_BANDS,
        },
    }
    tmp = OUT + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(doc, fh, indent=1)
        fh.write("\n")
    os.replace(tmp, OUT)
    print("recessions.json: %d US bands (%s..%s), %d Canadian bands"
          % (len(bands), bands[0]["peak"], bands[-1]["trough"],
             len(CDHOWE_BANDS)))


if __name__ == "__main__":
    main()
