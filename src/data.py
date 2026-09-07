"""SEC annual fact selection, explicit normalization and validation."""

import json
from functools import lru_cache
from datetime import date, datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
TAGS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
    ],
    "cogs": ["CostOfGoodsAndServicesSold", "CostOfRevenue"],
    "gross_profit": ["GrossProfit"],
    "ebit": ["OperatingIncomeLoss"],
    "sga": ["SellingGeneralAndAdministrativeExpense"],
    "rd": ["ResearchAndDevelopmentExpense"],
    "depreciation": ["Depreciation"],
    "amortization": ["AmortizationOfIntangibleAssets"],
    "taxes": ["IncomeTaxExpenseBenefit"],
    "net_income": ["NetIncomeLoss"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "ar": ["AccountsReceivableNetCurrent"],
    "inventory": ["InventoryNet"],
    "other_current_assets": ["PrepaidExpenseAndOtherAssetsCurrent"],
    "ppe": ["PropertyPlantAndEquipmentNet"],
    "intangibles": ["OtherIntangibleAssetsNet"],
    "goodwill": ["Goodwill"],
    "ap": ["AccountsPayableCurrent"],
    "accrued": ["OtherAccruedLiabilitiesCurrent"],
    "current_liabilities": ["LiabilitiesCurrent"],
    "assets": ["Assets"],
    "equity": ["StockholdersEquity"],
    "investments": ["AvailableForSaleSecuritiesDebtSecurities"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "cfi": ["NetCashProvidedByUsedInInvestingActivities"],
    "cff": ["NetCashProvidedByUsedInFinancingActivities"],
    "dividends": ["PaymentsOfDividends"],
    "employee_share_withholding": ["TreasuryStockValueAcquiredCostMethod"],
    "sbc": ["ShareBasedCompensation"],
    "restricted_cash_total": [
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
    ],
    "cash_change": [
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect"
    ],
    "fx_cash": [
        "EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations"
    ],
}
INSTANT = {
    "cash",
    "ar",
    "inventory",
    "other_current_assets",
    "ppe",
    "intangibles",
    "goodwill",
    "ap",
    "accrued",
    "current_liabilities",
    "assets",
    "equity",
    "investments",
    "restricted_cash_total",
}


def config() -> dict:
    return yaml.safe_load((ROOT / "config/company.yaml").read_text())


@lru_cache(maxsize=8)
def raw_facts(ticker: str) -> dict:
    return json.loads((ROOT / f"data/raw/{ticker}_companyfacts.json").read_text())


def fact(
    ticker: str,
    tags: list[str],
    end: str,
    cutoff: str,
    instant: bool = False,
    unit: str = "USD",
) -> tuple[float, dict]:
    data = raw_facts(ticker)
    for tag in tags:
        candidates = []
        for namespace in data["facts"].values():
            for x in namespace.get(tag, {}).get("units", {}).get(unit, []):
                if (
                    x["end"] != end
                    or x.get("filed", "9999") > cutoff
                    or x.get("form") not in ["10-K", "10-Q"]
                ):
                    continue
                days = (
                    date.fromisoformat(x["end"])
                    - date.fromisoformat(x.get("start", x["end"]))
                ).days
                if (instant and "start" not in x) or (
                    not instant and 350 <= days <= 380
                ):
                    candidates.append(x)
        if candidates:
            x = sorted(candidates, key=lambda x: (x["filed"], x["accn"]))[-1]
            metadata_path = ROOT / f"data/raw/{ticker}_companyfacts.source.json"
            metadata = json.loads(metadata_path.read_text())
            x = {**x, "retrieved_at": metadata["retrieved_at"]}
            return x["val"] / (1e6 if unit in ["USD", "shares"] else 1), {
                "tag": tag,
                **x,
                "source": f"https://www.sec.gov/Archives/edgar/data/{data['cik']}/{x['accn'].replace('-','')}/",
            }
    raise ValueError(
        f"Missing disclosed fact: {ticker} {tags} {end}; use documented manual import"
    )


def validate(df: pd.DataFrame) -> None:
    required = set(TAGS) | {
        "year",
        "period_end",
        "debt",
        "interest",
        "ebitda",
        "da",
        "other_assets",
        "other_liabilities",
        "other_current_liabilities",
        "acquisitions",
        "buybacks",
    }
    if required - set(df):
        raise ValueError(f"Missing columns {required-set(df)}")
    if not np.isfinite(df[list(required - {"period_end"})].to_numpy(dtype=float)).all():
        raise ValueError("Missing or non-finite numeric historical facts")
    if df.year.duplicated().any() or not df.year.is_monotonic_increasing:
        raise ValueError("Duplicate or unsorted fiscal years")
    if len(df) < 5:
        raise ValueError("At least five annual historical periods are required")
    for _, r in df.iterrows():
        checks = [
            r.revenue - r.cogs - r.gross_profit,
            r.assets - r.equity - r.current_liabilities - r.other_liabilities - r.debt,
            r.cfo + r.cfi + r.cff + r.fx_cash - r.cash_change,
        ]
        if max(abs(x) for x in checks) > 0.01:
            raise ValueError(f"Historical reconciliation failed {r.year}: {checks}")
        if r.revenue <= 0 or r.cash < 0:
            raise ValueError("Invalid revenue or cash")


def load_historicals(manual: str | None = None) -> pd.DataFrame:
    """Manual CSV must use the same schema, with a separate source ledger."""
    if manual:
        df = pd.read_csv(manual)
        validate(df)
        ledger_path = Path(manual).with_name("provenance.csv")
        if not ledger_path.exists():
            raise ValueError("Manual import requires adjacent provenance.csv")
        manual_ledger = pd.read_csv(ledger_path)
        if not {"field", "period_end", "source", "units", "currency"}.issubset(
            manual_ledger
        ):
            raise ValueError("Manual source ledger is incomplete")
        return df
    c = config()["company"]
    rows = []
    ledger = []
    if c["ticker"] != "GRMN":
        raise ValueError(
            "Use --manual for other targets and configure company/segments; automatic mapping is Garmin-specific"
        )
    custom = json.loads((ROOT / "data/raw/custom_cash_flows.json").read_text())
    facts = json.loads((ROOT / f"data/raw/{c['ticker']}_companyfacts.json").read_text())
    ends = sorted(
        {
            x["end"]
            for x in facts["facts"]["us-gaap"][TAGS["revenue"][0]]["units"]["USD"]
            if x.get("form") == "10-K"
            and x.get("fp") == "FY"
            and x.get("frame", "").startswith("CY")
            and "Q" not in x.get("frame", "")
        }
    )
    for year in c["historical_years"]:
        end = next((e for e in ends if int(e[:4]) == year), None)
        if end is None:
            raise ValueError(f"No fiscal year end for {year}")
        row = {"year": year, "period_end": end}
        for field, tags in TAGS.items():

            try:
                value, source = fact(
                    c["ticker"], tags, end, c["information_cutoff"], field in INSTANT
                )
            except ValueError:
                if field != "intangibles":
                    raise
                total, source = fact(
                    c["ticker"],
                    ["IntangibleAssetsNetIncludingGoodwill"],
                    end,
                    c["information_cutoff"],
                    True,
                )
                goodwill, _ = fact(
                    c["ticker"], ["Goodwill"], end, c["information_cutoff"], True
                )
                value = total - goodwill
                source["transformation"] = (
                    "Intangibles including goodwill less goodwill"
                )
            row[field] = value
            ledger.append(
                {
                    "field": field,
                    "currency": c["currency"],
                    "units": "USD millions",
                    "period_end": end,
                    **source,
                }
            )
        for x in custom:
            if x["period_end"] == end:
                filed = (
                    "2025-02-19" if x["source_fiscal_year"] == 2024 else "2023-02-22"
                )
                if filed > c["information_cutoff"]:
                    raise ValueError(
                        "Custom cash-flow disclosure is after the information cutoff"
                    )
                source_meta = json.loads(
                    (
                        ROOT
                        / f"data/raw/GRMN_{x['source_fiscal_year']}_10K.source.json"
                    ).read_text()
                )
                x = {**x, "retrieved_at": source_meta["retrieved_at"]}
                row[x["field"]] = x["value"]
                ledger.append(
                    {
                        **x,
                        "currency": c["currency"],
                        "units": "USD millions",
                        "filed": (
                            "2025-02-19"
                            if x["source_fiscal_year"] == 2024
                            else "2023-02-22"
                        ),
                    }
                )
        row["buybacks"] = row["employee_share_withholding"] + row["repurchase_plan"]
        # Garmin discloses no financial borrowings; leases remain operating liabilities.
        row.update(debt=0.0, interest=0.0, debt_issuance=0.0, debt_repayment=0.0)
        row["da"] = row["depreciation"] + row["amortization"]
        row["ebitda"] = row["ebit"] + row["da"]
        row["other_assets"] = row["assets"] - sum(
            row[k]
            for k in [
                "cash",
                "ar",
                "inventory",
                "other_current_assets",
                "ppe",
                "intangibles",
                "goodwill",
                "investments",
            ]
        )
        row["other_current_liabilities"] = (
            row["current_liabilities"] - row["ap"] - row["accrued"]
        )
        row["other_liabilities"] = (
            row["assets"] - row["equity"] - row["current_liabilities"] - row["debt"]
        )
        rows.append(row)
    df = pd.DataFrame(rows)
    validate(df)
    (ROOT / "data/processed").mkdir(exist_ok=True, parents=True)
    df.to_csv(ROOT / "data/processed/historicals.csv", index=False)
    pd.DataFrame(ledger).to_csv(ROOT / "data/processed/provenance.csv", index=False)
    return df


def market(ticker: str) -> dict:
    r = json.loads((ROOT / f"data/raw/{ticker}_market.json").read_text())["chart"][
        "result"
    ][0]
    expected = config()["company"]["market_date"]
    for t, p in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]):
        if datetime.fromtimestamp(t, timezone.utc).date().isoformat() == expected:
            return {
                "ticker": ticker,
                "date": expected,
                "price": p,
                "currency": r["meta"]["currency"],
            }
    raise ValueError("Requested market date absent")


if __name__ == "__main__":
    print(
        load_historicals()[["year", "revenue", "ebitda", "assets"]].to_string(
            index=False
        )
    )
