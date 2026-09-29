# Builds the interactive dashboard (docs/index.html) from the cleaned CSV files.
# Run from the project folder:  python dashboard/build_dashboard.py

import json
import glob
import pandas as pd

us = pd.read_csv("data/cleaned/us_smartphone_imports.csv", parse_dates=["date"])
india = pd.read_csv("data/cleaned/india_smartphone_exports.csv", parse_dates=["date"])

# every month from Jan 2022 to the last month in the US data
months = pd.date_range("2022-01-01", us["date"].max(), freq="MS")
month_index = {d: i for i, d in enumerate(months)}

countries = sorted(set(us["country"]) | set(india["country"]))
country_index = {c: i for i, c in enumerate(countries)}


def pack(df):
    # one short list per row to keep the file small:
    # [month, country, value in US$, number of phones, 1 if usable for price per phone]
    rows = []
    for r in df.itertuples():
        qty = 0 if pd.isnull(r.quantity) else int(r.quantity)
        price_ok = 0 if pd.isnull(r.price_per_phone) else 1
        rows.append([month_index[r.date], country_index[r.country], int(round(r.value_usd)), qty, price_ok])
    return rows


# numbers for the "checking the data" section
tiny = us["quantity"] < 1000
raw_files = glob.glob("data/raw/us_imports/*.json") + glob.glob("data/raw/india_exports/*.json")
raw_rows = sum(len(json.load(open(f))["data"]) for f in raw_files)
us_2022 = us[us["year"] == 2022]

data = {
    "months": [d.strftime("%Y-%m") for d in months],
    "countries": countries,
    "us": pack(us),
    "india": pack(india),
    "meta": {
        "rawFiles": len(raw_files),
        "rawRows": raw_rows,
        "cleanRows": len(us) + len(india),
        "price2022": round(us_2022["value_usd"].sum() / us_2022["quantity"].sum()),
        "tinyRowShare": round(tiny.mean() * 100, 1),
        "tinyValueShare": round(us.loc[tiny, "value_usd"].sum() / us["value_usd"].sum() * 100, 3),
    },
}

template = open("dashboard/template.html").read()
page = template.replace("__DATA__", json.dumps(data, separators=(",", ":")))

with open("docs/index.html", "w") as f:
    f.write(page)

print("Months:", len(months), "| Countries:", len(countries))
print("US rows:", len(data["us"]), "| India rows:", len(data["india"]))
print("Saved docs/index.html (%.0f KB)" % (len(page) / 1024))
