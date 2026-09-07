"""Enterprise valuation with explicit unlevered cash flows and equity bridges."""

import numpy as np
import pandas as pd


def wacc(a: dict) -> float:
    w = a["target_debt_weight"]
    if not 0 <= w <= 1:
        raise ValueError("Debt weight must lie in [0,1]")
    return (1 - w) * (a["risk_free"] + a["beta"] * a["equity_risk_premium"]) + w * a[
        "cost_of_debt"
    ] * (1 - a["tax_rate"])


def dcf(
    f: pd.DataFrame,
    rate: float,
    growth: float,
    net_debt: float = 0,
    shares: float = 1,
    method: str = "gordon",
    exit_multiple: float = 14,
) -> dict:
    if (
        not np.isfinite([rate, growth, net_debt, shares, exit_multiple]).all()
        or rate <= -1
        or shares <= 0
        or len(f) == 0
        or not np.isfinite(f[["fcff", "ebitda"]].to_numpy()).all()
    ):
        raise ValueError("Invalid DCF inputs")
    if method == "gordon":
        if rate <= growth or growth <= -1:
            raise ValueError("Gordon growth requires WACC > growth > -100%")
        terminal = f.iloc[-1].fcff * (1 + growth) / (rate - growth)
    elif method == "multiple":
        if exit_multiple <= 0:
            raise ValueError("Exit multiple must be positive")
        terminal = f.iloc[-1].ebitda * exit_multiple
    else:
        raise ValueError("Unknown terminal method")
    factors = (1 + rate) ** np.arange(1, len(f) + 1)
    pv = float(np.sum(f.fcff.to_numpy() / factors))
    tv = float(terminal / factors[-1])
    ev = pv + tv
    equity = ev - net_debt
    return dict(
        wacc=rate,
        terminal_growth=growth,
        pv_fcff=pv,
        terminal_value=float(terminal),
        pv_terminal=tv,
        enterprise_value=ev,
        net_debt=net_debt,
        equity_value=equity,
        per_share=equity / shares,
        terminal_share=tv / ev if ev != 0 else None,
    )


def sensitivity(
    f: pd.DataFrame,
    rates: list[float],
    growths: list[float],
    net_debt: float = 0,
    shares: float = 1,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            [
                dcf(f, r, g, net_debt, shares)["per_share"] if r > g else np.nan
                for g in growths
            ]
            for r in rates
        ],
        index=rates,
        columns=growths,
    )


def multiple_sensitivity(
    f: pd.DataFrame, rates: list[float], multiples: list[float]
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            [
                dcf(f, r, 0, method="multiple", exit_multiple=m)["enterprise_value"]
                for m in multiples
            ]
            for r in rates
        ],
        index=rates,
        columns=multiples,
    )
