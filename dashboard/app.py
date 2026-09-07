"""Run with python -m streamlit run dashboard/app.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st
import pandas as pd
from src.data import load_historicals, market, config
from src.scenarios import run_case
from src.forecast import assumptions
from src.valuation import sensitivity, wacc
from src.pipeline import recommendation

st.set_page_config(page_title="Garmin acquisition underwriting", layout="wide")
st.title("Garmin acquisition underwriting")
st.caption(
    "Historical case · 2025-02-28 information cutoff · USD millions · prospective assumptions"
)


@st.cache_data
def history():
    return load_historicals()


h = history()
a = assumptions()
with st.sidebar:
    st.header("Transaction and operating drivers")
    case = st.selectbox("Operating scenario", ["base", "upside", "downside"])
    ev = st.number_input(
        "Entry enterprise value ($m)",
        min_value=100.0,
        value=float(h.iloc[-1].ebitda * 15),
        step=500.0,
    )
    growth = (
        st.slider(
            "Growth shift across segments (percentage points)", -15.0, 15.0, 0.0, 0.5
        )
        / 100
    )
    margin = st.slider("EBITDA margin (%)", 10.0, 40.0, 28.0, 0.5) / 100
    rate = st.slider("WACC (%)", 5.0, 18.0, float(round(wacc(a) * 100, 2)), 0.1) / 100
    terminal = st.slider("Terminal growth (%)", 0.0, 5.0, 2.5, 0.1) / 100
    leverage = st.slider("Entry debt / EBITDA", 0.0, 6.0, 3.0, 0.25)
    interest = st.slider("Interest rate (%)", 2.0, 15.0, 7.5, 0.25) / 100
    exit_multiple = st.slider("Exit EV / EBITDA", 5.0, 25.0, 14.0, 0.5)
    years = st.slider("Holding period (years)", 1, 10, 5)
try:
    selected = assumptions(case)
    overrides = {
        "growth_shift": selected["growth_shift"] + growth,
        "margin_shift": margin - 0.28 + selected["margin_shift"],
        "wacc": rate,
        "terminal_growth": terminal,
        "leverage": leverage,
        "interest_rate": interest,
        "exit_multiple": exit_multiple,
        "forecast_years": years,
    }
    r = run_case(h, case, overrides, ev)
    down_overrides = {
        **overrides,
        "growth_shift": assumptions("downside")["growth_shift"] + growth,
        "margin_shift": margin - 0.28 + assumptions("downside")["margin_shift"],
        "interest_rate": interest + 0.02,
        "exit_multiple": max(1.0, exit_multiple - 4),
    }
    down = run_case(h, "downside", down_overrides, ev, solve=False)
    st.caption(
        f"Selected-case effective EBITDA margin: {r['forecast'].iloc[0].ebitda/r['forecast'].iloc[0].revenue:.1%}. Downside stress adds 2pp interest and subtracts 4x exit multiple from controls."
    )
    cols = st.columns(4)
    for col, label, value in zip(
        cols,
        ["DCF enterprise value", "DCF / share", "Sponsor IRR", "Sponsor MOIC"],
        [
            f"${r['dcf']['enterprise_value']:,.0f}m",
            f"${r['dcf']['per_share']:.2f}",
            f"{r['lbo']['irr']:.1%}",
            f"{r['lbo']['moic']:.2f}x",
        ],
    ):
        col.metric(label, value)
    cols = st.columns(3)
    cols[0].metric("Downside IRR", f"{down['lbo']['irr']:.1%}")
    cols[1].metric("Maximum EV at 20% IRR", f"${r['maximum_entry_ev']:,.0f}m")
    cols[2].metric(
        "Year-one EBIT / interest",
        (
            f"{r['lbo']['schedule'].iloc[0].interest_coverage:.2f}x"
            if pd.notna(r["lbo"]["schedule"].iloc[0].interest_coverage)
            else "No debt"
        ),
    )
    decision = recommendation({"base": r, "downside": down})
    st.subheader(f"{decision} on these terms")
    if r["lbo"]["funding_required"] > 0 or down["lbo"]["funding_required"] > 0:
        st.warning(
            "Additional financing is required. Facility availability has not been underwritten."
        )
    tabs = st.tabs(
        [
            "Operations",
            "Debt and returns",
            "Valuation sensitivity",
            "Statements and checks",
        ]
    )
    with tabs[0]:
        st.line_chart(r["forecast"].set_index("year")[["revenue", "ebitda", "fcff"]])
        st.dataframe(
            r["forecast"][["year", "revenue", "ebitda", "capex", "change_nwc", "fcff"]],
            hide_index=True,
        )
    with tabs[1]:
        st.line_chart(r["lbo"]["schedule"].set_index("year")[["debt"]])
        st.dataframe(r["lbo"]["schedule"], hide_index=True)
        st.write("Sources", r["lbo"]["sources"])
        st.write("Uses", r["lbo"]["uses"])
    with tabs[2]:
        grid = sensitivity(
            r["forecast"],
            [rate - 0.01, rate, rate + 0.01],
            [terminal - 0.005, terminal, terminal + 0.005],
            r["dcf"]["net_debt"],
            r["shares"],
        )
        grid.index = [f"{v:.1%}" for v in grid.index]
        grid.columns = [f"{v:.1%}" for v in grid.columns]
        st.caption("Rows: WACC. Columns: terminal growth. Values: USD/share.")
        st.dataframe(grid.style.format("${:,.2f}").background_gradient(cmap="YlGnBu"))
    with tabs[3]:
        st.dataframe(r["forecast"].set_index("year").T)
        st.download_button(
            "Download scenario CSV",
            r["forecast"].to_csv(index=False),
            "scenario.csv",
            "text/csv",
        )
except (ValueError, ArithmeticError) as exc:
    st.error(str(exc))
st.caption(
    "Public-information analysis. See the investment memo and methodology for source dates, peer limitations and financing assumptions."
)
