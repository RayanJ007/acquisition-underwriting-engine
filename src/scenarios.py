"""All scenarios rerun operating statements, valuation and transaction financing."""

from src.forecast import assumptions, forecast
from src.valuation import dcf, wacc
from src.lbo import lbo, maximum_entry_ev
from src.comparables import share_count
from src.data import config


def run_case(h, case="base", overrides=None, entry_ev=None, solve=True):
    a = assumptions(case, overrides)
    f = forecast(h, a)
    last = h.iloc[-1]
    c = config()["company"]
    shares, _ = share_count(c["ticker"], c["fiscal_year_end"], c["information_cutoff"])
    nd = last.debt - last.cash - last.investments
    d = dcf(f, a.get("wacc", wacc(a)), a["terminal_growth"], nd, shares)
    tx = lbo(h, f, a, entry_ev)
    result = {
        "assumptions": a,
        "forecast": f,
        "dcf": d,
        "lbo": tx,
        "shares": shares,
        "dcf_multiple": dcf(
            f,
            a.get("wacc", wacc(a)),
            a["terminal_growth"],
            nd,
            shares,
            "multiple",
            a["exit_multiple"],
        ),
    }
    if solve:
        result["maximum_entry_ev"] = maximum_entry_ev(h, f, a)
    return result


def run_scenarios(h, overrides=None, entry_ev=None):
    return {
        case: run_case(h, case, overrides, entry_ev)
        for case in ["base", "upside", "downside"]
    }
