"""Public-information QoE bridge; no unsupported addbacks."""

import pandas as pd
from src.historicals import analyze


def quality_of_earnings(
    history: pd.DataFrame, adjustments: list[dict] | None = None
) -> tuple[pd.DataFrame, dict]:
    r = analyze(history).iloc[-1]
    rows = [
        {
            "item": "Reported EBIT plus operating D&A",
            "amount": r.ebitda,
            "classification": "Derived reported EBITDA",
            "rationale": "Depreciation plus intangible amortization; excludes securities amortization.",
            "source": "data/processed/provenance.csv",
        }
    ]
    for adj in adjustments or []:
        if not all(
            k in adj
            for k in ["item", "amount", "classification", "rationale", "source"]
        ):
            raise ValueError(
                "Every adjustment requires amount, classification, rationale and source"
            )
        if not adj["source"] or not adj["rationale"]:
            raise ValueError("Unsupported adjustment")
        if adj["classification"] not in [
            "non-recurring disclosed",
            "scenario assumption",
            "recurring",
        ]:
            raise ValueError("Unrecognized adjustment classification")
        rows.append(adj)
    adjusted = sum(x["amount"] for x in rows)
    rows.append(
        {
            "item": "Adjusted EBITDA",
            "amount": adjusted,
            "classification": "Total",
            "rationale": "No public-disclosure-supported EBITDA addbacks applied in the default case.",
            "source": "Public-information diligence judgment",
        }
    )
    return pd.DataFrame(rows), {
        "cfo_conversion": float(r.ebitda_cfo_conversion),
        "fcf_conversion": float(r.fcf_conversion),
        "inventory_days": float(r.dio),
        "capex_ratio": float(r.capex_ratio),
        "sbc": float(r.sbc),
        "adjusted_ebitda": adjusted,
    }
