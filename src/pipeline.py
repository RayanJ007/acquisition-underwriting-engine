"""Reproducible report generation; python -m src.pipeline."""

import argparse, json
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.data import ROOT, load_historicals, config, market
from src.historicals import analyze, commentary
from src.scenarios import run_scenarios
from src.comparables import comparables
from src.diligence import quality_of_earnings
from src.valuation import sensitivity, multiple_sensitivity


def recommendation(cases: dict) -> str:
    b = cases["base"]
    d = cases["downside"]
    if b["lbo"]["funding_required"] > 0 or d["lbo"]["funding_required"] > 0:
        return "Do Not Proceed"
    return (
        "Proceed"
        if b["lbo"]["irr"] >= b["assumptions"]["target_irr"] and d["lbo"]["irr"] >= 0
        else "Do Not Proceed"
    )


def build(manual=None) -> dict:
    for folder in ["outputs/tables", "outputs/charts", "reports", "models"]:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    h = load_historicals(manual)
    hist = analyze(h)
    cases = run_scenarios(h)
    peers, stats = comparables(h.iloc[-1].ebitda)
    bridge, qoe = quality_of_earnings(h)
    b = cases["base"]
    last = h.iloc[-1]
    rates = [0.07, 0.08, 0.09, 0.10, 0.11]
    growths = [0.01, 0.02, 0.025, 0.03, 0.035]
    sens = sensitivity(b["forecast"], rates, growths, b["dcf"]["net_debt"], b["shares"])
    exit_sens = multiple_sensitivity(b["forecast"], rates, [10, 12, 14, 16, 18])
    summary = pd.DataFrame(
        [
            {
                "scenario": k,
                "revenue_year5": v["forecast"].iloc[-1].revenue,
                "dcf_ev": v["dcf"]["enterprise_value"],
                "dcf_per_share": v["dcf"]["per_share"],
                "irr": v["lbo"]["irr"],
                "moic": v["lbo"]["moic"],
                "max_entry_ev": v["maximum_entry_ev"],
                "exit_debt": v["lbo"]["schedule"].iloc[-1].debt,
                "funding_required": v["lbo"]["funding_required"],
            }
            for k, v in cases.items()
        ]
    )
    for name, table in [
        ("historical_analysis", hist),
        ("peers", peers),
        ("peer_statistics", stats),
        ("qoe", bridge),
        ("scenarios", summary),
        ("dcf_sensitivity", sens),
        ("exit_multiple_sensitivity", exit_sens),
    ]:
        table.to_csv(
            ROOT / f"outputs/tables/{name}.csv",
            index=name
            in ["peer_statistics", "dcf_sensitivity", "exit_multiple_sensitivity"],
        )
    for name, v in cases.items():
        v["forecast"].to_csv(ROOT / f"outputs/tables/{name}_forecast.csv", index=False)
        v["lbo"]["schedule"].to_csv(
            ROOT / f"outputs/tables/{name}_debt.csv", index=False
        )
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(h.year, h.revenue, marker="o", label="Historical revenue", color="#20364d")
    for name, v in cases.items():
        ax.plot(
            [last.year, *v["forecast"].year],
            [last.revenue, *v["forecast"].revenue],
            label=name.capitalize(),
            linestyle="--",
        )
    ax.set(
        title="Garmin revenue: historical and underwriting cases",
        ylabel="USD millions",
        xlabel="Fiscal year",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(ROOT / "outputs/charts/revenue.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    im = ax.imshow(sens, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(len(growths)), [f"{x:.1%}" for x in growths])
    ax.set_yticks(range(len(rates)), [f"{x:.0%}" for x in rates])
    for i in range(len(rates)):
        for j in range(len(growths)):
            ax.text(
                j,
                i,
                f"${sens.iloc[i,j]:.0f}",
                ha="center",
                va="center",
                color="white" if i < 2 else "#14283c",
            )
    ax.set(title="DCF implied value per share", xlabel="Terminal growth", ylabel="WACC")
    fig.colorbar(im, ax=ax, label="USD/share")
    fig.tight_layout()
    fig.savefig(ROOT / "outputs/charts/dcf_sensitivity.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4))
    for name, v in cases.items():
        ax.plot(
            v["lbo"]["schedule"].year,
            v["lbo"]["schedule"].debt,
            marker="o",
            label=name.capitalize(),
        )
    ax.set(
        title="Acquisition debt paydown", ylabel="USD millions", xlabel="Fiscal year"
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(ROOT / "outputs/charts/debt_paydown.png", dpi=150)
    plt.close(fig)
    price = market(config()["company"]["ticker"])["price"]
    market_ev = price * b["shares"] + b["dcf"]["net_debt"]
    conclusion = recommendation(cases)
    peer_low = stats.loc["p25", "target_ev_at_ebitda_multiple"]
    peer_high = stats.loc["p75", "target_ev_at_ebitda_multiple"]
    rows = "\n".join(
        f"| {r.scenario.title()} | ${r.dcf_ev:,.0f}m | {r.irr:.1%} | {r.moic:.2f}x | ${r.max_entry_ev:,.0f}m |"
        for r in summary.itertuples()
    )
    memo = f"""# Garmin acquisition investment memo

Historical underwriting case • information cutoff and market observation: 2025-02-28 • USD millions

## Executive Summary

**{conclusion} at the assumed {b['lbo']['entry_multiple']:.1f}x entry EBITDA (${b['lbo']['entry_ev']:,.0f}m EV).** Base sponsor IRR is {b['lbo']['irr']:.1%}, compared with a {b['assumptions']['target_irr']:.0%} hurdle; downside IRR is {cases['downside']['lbo']['irr']:.1%}. The maximum base-case entry EV meeting the hurdle is **${b['maximum_entry_ev']:,.0f}m ({b['maximum_entry_ev']/last.ebitda:.1f}x)**. The equity purchase consideration at that EV is ${b['maximum_entry_ev']-last.debt+last.cash+last.investments:,.0f}m before fees.

The operating franchise has strong margins and a diversified segment mix, but acquisition returns depend heavily on entry discipline and terminal multiples. Base Gordon DCF gives ${b['dcf']['enterprise_value']:,.0f}m EV; peer interquartile reference values are ${peer_low:,.0f}m–${peer_high:,.0f}m. These methods differ substantially and should not be averaged mechanically.

## Company Overview

Garmin designs devices and systems for fitness, outdoor activity, aviation, marine and automotive OEM customers. The five segments support differentiated growth assumptions. A strategic buyer might justify synergies, but none are included in this sponsor case.

## Historical Performance

{commentary(h)} FY2024 net income was ${last.net_income:,.0f}m. Cash and securities total ${last.cash+last.investments:,.0f}m, with no financial borrowings in the historical case.

## Key Value Drivers

Segment-specific growth moderates the latest 20% revenue increase. Base EBITDA margin is {b['forecast'].iloc[0].ebitda/b['forecast'].iloc[0].revenue:.1%}, with R&D retained as an operating cost. The forecast requires inventory investment and CapEx, rather than treating EBITDA as distributable cash. After-tax cash generation drives the debt sweep.

## Quality of Earnings Findings

Derived reported EBITDA of ${last.ebitda:,.0f}m equals adjusted EBITDA: **no unsupported addbacks**. CFO/EBITDA is {qoe['cfo_conversion']:.1%}; FCF/EBITDA is {qoe['fcf_conversion']:.1%}. SBC of ${qoe['sbc']:,.0f}m remains an economic cost. {qoe['inventory_days']:.0f} inventory days warrant product obsolescence and channel diligence. FX and tax volatility affect net earnings but should not be added to EBITDA again.

## Valuation

Gordon DCF at {b['dcf']['wacc']:.2%} WACC and {b['dcf']['terminal_growth']:.1%} terminal growth yields ${b['dcf']['per_share']:.2f}/share. Terminal value contributes {b['dcf']['terminal_share']:.1%} of EV. The exit-multiple DCF gives ${b['dcf_multiple']['enterprise_value']:,.0f}m EV. Both methods add cash and securities and subtract financial debt once.

The dated unadjusted market close is ${price:.2f}; using fiscal-end shares implies ${market_ev:,.0f}m EV. This is a separate public-market reference, not the assumed transaction price. Share counts are approximate at the market date. Logitech and Polaris are limited historical comparables with different business mixes and period ends; see the peer table and provenance ledger.

## Scenario Analysis

| Case | DCF EV | Sponsor IRR | MOIC | Maximum entry EV at hurdle |
|---|---:|---:|---:|---:|
{rows}

## Key Risks

Exit multiple contraction, inventory needs, discretionary demand and higher interest costs drive the downside. The case excludes synergies, purchase-accounting amortization, tax leakage on securities, withholding taxes, exit fees, debt covenants and lender commitment limits. Cash shortfalls are disclosed as additional financing requirements, not assumed proof of financeability. The two-month gap between the fiscal balance sheet and valuation date is approximated. Public information cannot substitute for customer, supplier, tax and legal diligence.

## Final Recommendation

{conclusion} on the modelled terms. Use the maximum-entry solver as an initial negotiation constraint, then rerun the downside at that price and obtain a lender financing case. Passing the base hurdle alone does not establish an acceptable acquisition. The modelled five-year outcome is a scenario, not a prediction.

## Sources and audit trail

- [Garmin FY2024 10-K](https://www.sec.gov/Archives/edgar/data/1121788/000095017025022760/grmn-20241228.htm)
- [Garmin FY2024 segment results](https://www.garmin.com/en-US/newsroom/wp-content/uploads/2025/02/2024-Q4-GRMN-Earnings-Release_Final.pdf)
- Historical and peer field-level accessions: data/processed/provenance.csv and peer_provenance.csv.
- Original SEC and Yahoo responses and retrieval metadata: data/raw. Forecast and valuation judgments: config/assumptions.yaml and docs/methodology.md.
"""
    (ROOT / "reports/investment_memo.md").write_text(memo, encoding="utf-8")

    def clean(x):
        if isinstance(x, pd.DataFrame):
            return clean(x.to_dict("records"))
        if isinstance(x, dict):
            return {k: clean(v) for k, v in x.items()}
        if isinstance(x, list):
            return [clean(v) for v in x]
        if isinstance(x, (float, np.floating)):
            return float(x) if np.isfinite(x) else None
        if isinstance(x, np.integer):
            return int(x)
        return x

    payload = clean(
        {
            "company": config(),
            "history": h,
            "historical_analysis": hist,
            "cases": cases,
            "peers": peers,
            "peer_statistics": stats.reset_index(),
            "qoe": bridge,
            "summary": summary,
            "recommendation": conclusion,
            "market_price": price,
            "market_ev": market_ev,
        }
    )
    (ROOT / "outputs/model.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(summary.to_string(index=False))
    print(conclusion)
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manual", help="Validated historical CSV with matching source ledger"
    )
    build(parser.parse_args().manual)
