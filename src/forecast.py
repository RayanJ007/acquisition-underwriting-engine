"""Five-year segment forecast with independently rolled balance sheet and cash flow."""

from copy import deepcopy
import math
import pandas as pd
import yaml
from src.data import ROOT, config
from src.debt import debt_schedule


def assumptions(case: str = "base", overrides: dict | None = None) -> dict:
    a = yaml.safe_load((ROOT / "config/assumptions.yaml").read_text())
    scenarios = a.pop("scenarios")
    if case not in scenarios:
        raise ValueError(f"Unknown scenario {case}")
    a.update(scenarios[case])
    a.update(overrides or {})

    def check_finite(value):
        if isinstance(value, dict):
            for v in value.values():
                check_finite(v)
        elif isinstance(value, (int, float)) and not math.isfinite(value):
            raise ValueError("Non-finite assumption")

    check_finite(a)
    if not isinstance(a["forecast_years"], int) or not 1 <= a["forecast_years"] <= 10:
        raise ValueError("Holding period must be 1–10 years")
    for k in [
        "tax_rate",
        "payout_ratio",
        "cogs_ratio",
        "rd_ratio",
        "cash_sga_ratio",
        "capex_ratio",
        "mandatory_amortization",
    ]:
        if not 0 <= a[k] <= 1:
            raise ValueError(f"{k} must be between zero and one")
    if any(v + a["growth_shift"] <= -1 for v in a["segment_growth"].values()):
        raise ValueError("Revenue growth must exceed -100%")
    if any(
        a[k] < 0
        for k in [
            "dso",
            "dio",
            "dpo",
            "minimum_cash",
            "interest_rate",
            "amortization",
            "depreciation_rate",
            "leverage",
            "transaction_fee_rate",
            "financing_fee_rate",
        ]
    ):
        raise ValueError("Negative driver")
    return a


def forecast(history: pd.DataFrame, a: dict) -> pd.DataFrame:
    p = history.iloc[-1].to_dict()
    initial = deepcopy(p)
    segments = deepcopy(config()["segments"])
    if abs(sum(segments.values()) - p["revenue"]) > 0.01:
        raise ValueError("Segment revenue does not reconcile")
    p["nwc"] = (
        p["ar"] + p["inventory"] + p["other_current_assets"] - p["ap"] - p["accrued"]
    )
    rows = []
    for t in range(1, a["forecast_years"] + 1):
        for k in segments:
            segments[k] *= 1 + a["segment_growth"][k] + a["growth_shift"]
        r = {
            "year": int(initial["year"]) + t,
            **{"segment_" + k: v for k, v in segments.items()},
        }
        r["revenue"] = sum(segments.values())
        r["cogs"] = r["revenue"] * a["cogs_ratio"]
        r["rd"] = r["revenue"] * a["rd_ratio"]
        r["cash_sga"] = r["revenue"] * (a["cash_sga_ratio"] - a["margin_shift"])
        r["capex"] = r["revenue"] * a["capex_ratio"]
        r["depreciation"] = min(
            p["ppe"] + r["capex"],
            (p["ppe"] + 0.5 * r["capex"]) * a["depreciation_rate"],
        )
        r["amortization"] = min(p["intangibles"], a["amortization"])
        r["da"] = r["depreciation"] + r["amortization"]
        r["ebitda"] = r["revenue"] - r["cogs"] - r["rd"] - r["cash_sga"]
        r["ebit"] = r["ebitda"] - r["da"]
        r["interest"] = p["debt"] * a["interest_rate"]
        r["taxes"] = max(0.0, r["ebit"] - r["interest"]) * a["tax_rate"]
        r["net_income"] = r["ebit"] - r["interest"] - r["taxes"]
        r["ar"] = r["revenue"] / 365 * a["dso"]
        r["inventory"] = r["cogs"] / 365 * a["dio"]
        r["ap"] = r["cogs"] / 365 * a["dpo"]
        r["other_current_assets"] = r["revenue"] * a["other_current_assets_ratio"]
        r["accrued"] = r["revenue"] * a["accrued_ratio"]
        r["nwc"] = (
            r["ar"]
            + r["inventory"]
            + r["other_current_assets"]
            - r["ap"]
            - r["accrued"]
        )
        r["change_nwc"] = r["nwc"] - p["nwc"]
        r["cfo"] = r["net_income"] + r["da"] - r["change_nwc"]
        r["fcff"] = (
            r["ebit"]
            - max(0.0, r["ebit"]) * a["tax_rate"]
            + r["da"]
            - r["capex"]
            - r["change_nwc"]
        )
        r["dividends"] = max(0.0, r["net_income"]) * a["payout_ratio"]
        r.update(
            debt_schedule(
                p["debt"],
                p["cash"] + r["cfo"] - r["capex"] - r["dividends"],
                a["minimum_cash"],
                a["interest_rate"],
                initial["debt"],
                a["mandatory_amortization"],
            )
        )
        r["cfi"] = -r["capex"]
        r["cff"] = (
            r["borrowing"]
            - r["mandatory_repayment"]
            - r["optional_repayment"]
            - r["dividends"]
        )
        r["cash_change"] = r["cfo"] + r["cfi"] + r["cff"]
        r["ppe"] = p["ppe"] + r["capex"] - r["depreciation"]
        r["intangibles"] = p["intangibles"] - r["amortization"]
        for k in [
            "goodwill",
            "investments",
            "other_assets",
            "other_current_liabilities",
            "other_liabilities",
        ]:
            r[k] = p[k]
        r["equity"] = p["equity"] + r["net_income"] - r["dividends"]
        r["current_liabilities"] = (
            r["ap"] + r["accrued"] + r["other_current_liabilities"]
        )
        r["assets"] = sum(
            r[k]
            for k in [
                "cash",
                "ar",
                "inventory",
                "other_current_assets",
                "ppe",
                "intangibles",
                "goodwill",
                "investments",
                "other_assets",
            ]
        )
        r["check_balance"] = (
            r["assets"]
            - r["current_liabilities"]
            - r["other_liabilities"]
            - r["debt"]
            - r["equity"]
        )
        r["check_cash"] = p["cash"] + r["cash_change"] - r["cash"]
        r["check_equity"] = r["equity"] - p["equity"] - r["net_income"] + r["dividends"]
        r["check_debt"] = (
            p["debt"]
            + r["borrowing"]
            - r["mandatory_repayment"]
            - r["optional_repayment"]
            - r["debt"]
        )
        r["check_ppe"] = r["ppe"] - p["ppe"] - r["capex"] + r["depreciation"]
        rows.append(r)
        p = r
    result = pd.DataFrame(rows)
    if result.filter(like="check_").abs().to_numpy().max() > 1e-7:
        raise ArithmeticError("Forecast does not reconcile")
    return result
