"""Historical operating diagnostics. Undefined ratios remain missing."""

import numpy as np
import pandas as pd


def analyze(h: pd.DataFrame) -> pd.DataFrame:
    d = h.copy()

    def div(a, b):
        return a / b.replace(0, np.nan)

    for k in ["revenue", "gross_profit", "ebitda"]:
        d[k + "_growth"] = d[k].pct_change()
    for k in ["gross_profit", "ebitda", "ebit", "net_income", "cfo"]:
        d[k + "_margin"] = div(d[k], d.revenue)
    avg = lambda s: (s + s.shift()) / 2
    d["roa"] = div(d.net_income, avg(d.assets))
    d["roe"] = div(d.net_income, avg(d.equity))
    effective = div(d.taxes, d.net_income + d.taxes)
    d["roic"] = div(
        d.ebit * (1 - effective), avg(d.equity + d.debt - d.cash - d.investments)
    )
    d["net_debt_ebitda"] = div(d.debt - d.cash - d.investments, d.ebitda)
    d["debt_equity"] = div(d.debt, d.equity)
    d["interest_coverage"] = div(d.ebit, d.interest)
    d["fcf"] = d.cfo - d.capex
    d["fcf_conversion"] = div(d.fcf, d.ebitda)
    d["capex_ratio"] = div(d.capex, d.revenue)
    d["dso"] = div(d.ar, d.revenue) * 365
    d["dio"] = div(d.inventory, d.cogs) * 365
    d["dpo"] = div(d.ap, d.cogs) * 365
    d["cash_conversion_cycle"] = d.dso + d.dio - d.dpo
    d["nwc"] = d.ar + d.inventory + d.other_current_assets - d.ap - d.accrued
    d["nwc_ratio"] = div(d.nwc, d.revenue)
    d["ebitda_cfo_conversion"] = div(d.cfo, d.ebitda)
    return d


def commentary(h: pd.DataFrame) -> str:
    a = analyze(h)
    first, last = a.iloc[0], a.iloc[-1]
    worst = a.loc[a.revenue_growth.idxmin()]
    return (
        f"Revenue compounded at {(last.revenue/first.revenue)**(1/(len(a)-1))-1:.1%}; "
        f"EBITDA margin moved from {first.ebitda_margin:.1%} to {last.ebitda_margin:.1%}. "
        f"The weakest revenue growth was {worst.revenue_growth:.1%} in {int(worst.year)}. "
        f"Latest CFO/EBITDA was {last.ebitda_cfo_conversion:.1%}, with "
        f"{last.cash_conversion_cycle:.0f} days in the cash conversion cycle. "
        f"Inventory days moved from {first.dio:.0f} to {last.dio:.0f}; "
        f"FCF was ${last.fcf:,.0f}m against EBITDA of ${last.ebitda:,.0f}m."
    )
