"""Historical peer reference multiples with exact period/source disclosure."""

import pandas as pd
from src.data import fact, config, market, ROOT


def share_count(ticker: str, end: str, cutoff: str) -> tuple[float, list[dict]]:
    try:
        v, s = fact(
            ticker, ["CommonStockSharesOutstanding"], end, cutoff, True, "shares"
        )
        return v, [s]
    except ValueError:
        issued, s = fact(
            ticker, ["CommonStockSharesIssued"], end, cutoff, True, "shares"
        )
        treasury, t = fact(
            ticker, ["TreasuryStockCommonShares"], end, cutoff, True, "shares"
        )
        return issued - treasury, [s, t]


def comparables(target_ebitda: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    c = config()
    cutoff = c["company"]["information_cutoff"]
    rows = []
    ledger = []
    for peer in c["peers"]:
        ticker = peer["ticker"]
        end = peer["fiscal_end"]
        row = {
            "ticker": ticker,
            "period_end": end,
            "basis": "Historical FY",
            "rationale": peer["rationale"],
        }

        def get(field, tags, instant=False):
            value, s = fact(ticker, tags, end, cutoff, instant)
            ledger.append({"ticker": ticker, "field": field, **s})
            row[field] = value

        get(
            "revenue",
            ["RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
        )
        get("ebit", ["OperatingIncomeLoss"])
        get("net_income", ["NetIncomeLoss"])
        get("depreciation", ["Depreciation"])
        get("amortization", ["AmortizationOfIntangibleAssets"])
        get("cash", ["CashAndCashEquivalentsAtCarryingValue"], True)
        if ticker == "LOGI":
            row["debt"] = 0.0
            ledger.append(
                {
                    "ticker": ticker,
                    "field": "debt",
                    "source": "https://www.sec.gov/Archives/edgar/data/1032975/",
                    "rationale": "FY2024 balance sheet: no financial debt; operating leases excluded",
                }
            )
        else:
            get("debt", ["LongTermDebt"], True)
        row["shares"], sources = share_count(ticker, end, cutoff)
        ledger.extend({"ticker": ticker, "field": "shares", **s} for s in sources)
        row.update(market(ticker))
        row["market_cap"] = row["price"] * row["shares"]
        row["enterprise_value"] = row["market_cap"] + row["debt"] - row["cash"]
        row["ebitda"] = row["ebit"] + row["depreciation"] + row["amortization"]
        for label, num, den in [
            ("ev_revenue", "enterprise_value", "revenue"),
            ("ev_ebitda", "enterprise_value", "ebitda"),
            ("ev_ebit", "enterprise_value", "ebit"),
            ("pe", "market_cap", "net_income"),
        ]:
            row[label] = row[num] / row[den] if row[den] > 0 else float("nan")
        rows.append(row)
    df = pd.DataFrame(rows)
    m = df[["ev_revenue", "ev_ebitda", "ev_ebit", "pe"]]
    stats = pd.DataFrame(
        {
            "mean": m.mean(),
            "median": m.median(),
            "p25": m.quantile(0.25),
            "p75": m.quantile(0.75),
        }
    ).T
    stats["target_ev_at_ebitda_multiple"] = stats.ev_ebitda * target_ebitda
    pd.DataFrame(ledger).to_csv(
        ROOT / "data/processed/peer_provenance.csv", index=False
    )
    return df, stats
