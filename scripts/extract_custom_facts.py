"""Extract Garmin's custom annual acquisition and repurchase facts from inline XBRL."""

from pathlib import Path
from datetime import datetime, timezone
import urllib.request, json
import os
from source_manifest import write_manifest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
URLS = {
    2024: "https://www.sec.gov/Archives/edgar/data/1121788/000095017025022760/grmn-20241228.htm",
    2022: "https://www.sec.gov/Archives/edgar/data/1121788/000095017023003566/grmn-20221231.htm",
}


def extract():
    records = []
    for year, url in URLS.items():
        path = ROOT / f"data/raw/GRMN_{year}_10K.html"
        if not path.exists():
            req = urllib.request.Request(
                url,
                headers={"User-Agent": os.environ["SEC_USER_AGENT"]},
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                path.write_bytes(r.read())
        soup = BeautifulSoup(path.read_bytes(), "html.parser")
        contexts = {}
        for c in soup.find_all(lambda t: t.name.split(":")[-1] == "context"):
            if c.find(lambda t: t.name.split(":")[-1] == "segment"):
                continue
            end = c.find(lambda t: t.name.split(":")[-1] == "enddate")
            start = c.find(lambda t: t.name.split(":")[-1] == "startdate")
            if (
                end
                and start
                and 350
                <= (
                    datetime.fromisoformat(end.text)
                    - datetime.fromisoformat(start.text)
                ).days
                <= 380
            ):
                contexts[c["id"]] = end.text
        for tag in soup.find_all():
            name = tag.get("name", "")
            ctx = tag.get("contextref")
            if ctx not in contexts:
                continue
            if (
                "CashFromPaymentsForAcquisitions" in name
                or "CashPaidForAcquisitionsNetOfCashAcquired" in name
            ):
                field = "acquisitions"
            elif (
                name == "grmn:PaymentForPurchaseOfTreasuryStockUnderShareRepurchasePlan"
            ):
                field = "repurchase_plan"
            else:
                continue
            value = (
                float(tag.get_text().replace(",", ""))
                * 10 ** int(tag.get("scale", 0))
                / 1e6
            )
            records.append(
                {
                    "field": field,
                    "period_end": contexts[ctx],
                    "value": value,
                    "tag": name,
                    "source": url,
                    "source_fiscal_year": year,
                }
            )
    for end in ["2020-12-26", "2021-12-25"]:
        records.append(
            {
                "field": "repurchase_plan",
                "period_end": end,
                "value": 0.0,
                "tag": "Disclosed dash in consolidated cash-flow table",
                "source": URLS[2022],
                "source_fiscal_year": 2022,
            }
        )
    # Prefer latest annual comparative and one of the equivalent custom tags.
    unique = {}
    for r in sorted(records, key=lambda r: r["source_fiscal_year"]):
        unique[(r["field"], r["period_end"])] = r
    (ROOT / "data/raw/custom_cash_flows.json").write_text(
        json.dumps(list(unique.values()), indent=2)
    )
    print(f"Extracted {len(unique)} custom annual facts")


if __name__ == "__main__":
    extract()
    write_manifest()
