"""Cash-free/debt-free acquisition waterfall and numerical entry-price solving."""

import pandas as pd
from src.debt import debt_schedule


def returns(sponsor_equity: float, exit_equity: float, years: int) -> dict:
    if sponsor_equity <= 0 or years <= 0 or exit_equity < 0:
        raise ValueError("Invalid sponsor cash flows")
    moic = exit_equity / sponsor_equity
    return {"moic": moic, "irr": moic ** (1 / years) - 1}


def lbo(
    h: pd.DataFrame, f: pd.DataFrame, a: dict, entry_ev: float | None = None
) -> dict:
    last = h.iloc[-1]
    ev = entry_ev if entry_ev is not None else last.ebitda * a["entry_multiple"]
    if ev <= 0 or a["leverage"] < 0 or a["exit_multiple"] <= 0:
        raise ValueError("Invalid transaction inputs")
    debt = min(last.ebitda * a["leverage"], ev * 0.70)
    fee = ev * a["transaction_fee_rate"] + debt * a["financing_fee_rate"]
    target_cash = last.cash + last.investments
    uses = {
        "purchase_equity": ev - last.debt + target_cash,
        "refinance_debt": float(last.debt),
        "fees": fee,
        "minimum_cash": a["minimum_cash"],
    }
    equity = sum(uses.values()) - debt - target_cash
    sources = {
        "term_debt": debt,
        "target_cash_and_securities": target_cash,
        "sponsor_equity": equity,
    }
    if equity <= 0 or uses["purchase_equity"] < 0:
        raise ValueError("Nonpositive sponsor equity or equity purchase value")
    p_debt = debt
    cash = a["minimum_cash"]
    rows = []
    for _, r in f.iterrows():
        interest = p_debt * a["interest_rate"]
        taxes = max(0.0, r.ebit - interest) * a["tax_rate"]
        fcf = r.ebitda - taxes - r.capex - r.change_nwc - interest
        d = debt_schedule(
            p_debt,
            cash + fcf,
            a["minimum_cash"],
            a["interest_rate"],
            debt,
            a["mandatory_amortization"],
        )
        rows.append(
            {
                "year": int(r.year),
                "ebitda": r.ebitda,
                "ebit": r.ebit,
                "taxes": taxes,
                "fcf": fcf,
                **d,
                "leverage": d["debt"] / r.ebitda if r.ebitda > 0 else None,
                "interest_coverage": r.ebit / interest if interest > 0 else None,
            }
        )
        p_debt = d["debt"]
        cash = d["cash"]
    schedule = pd.DataFrame(rows)
    exit_ev = f.iloc[-1].ebitda * a["exit_multiple"]
    exit_equity = max(0.0, exit_ev - p_debt + cash)
    return {
        "entry_ev": ev,
        "entry_multiple": ev / last.ebitda,
        "sources": sources,
        "uses": uses,
        "sources_uses_check": sum(sources.values()) - sum(uses.values()),
        "schedule": schedule,
        "exit_ev": exit_ev,
        "exit_equity": exit_equity,
        "funding_required": float(schedule.borrowing.sum()),
        **returns(equity, exit_equity, len(f)),
    }


def maximum_entry_ev(
    h: pd.DataFrame, f: pd.DataFrame, a: dict, target_irr: float | None = None
) -> float:
    target = a["target_irr"] if target_irr is None else target_irr
    if target <= -1:
        raise ValueError("Target IRR must exceed -100%")
    low = max(
        0.01, float(h.iloc[-1].debt - h.iloc[-1].cash - h.iloc[-1].investments) + 0.01
    )
    high = max(h.iloc[-1].ebitda * 50, low * 2)
    objective = lambda ev: lbo(h, f, a, ev)["irr"] - target
    if objective(low) < 0:
        raise ValueError("No positive price achieves the return hurdle")
    for _ in range(30):
        if objective(high) < 0:
            break
        high *= 2
    else:
        raise ValueError("Could not bracket target return")
    for _ in range(100):
        mid = (low + high) / 2
        if objective(mid) > 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2
