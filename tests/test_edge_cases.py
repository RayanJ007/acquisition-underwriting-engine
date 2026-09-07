import math
import pytest
from src.data import load_historicals, fact, config, validate
from src.forecast import assumptions, forecast
from src.lbo import lbo


def test_source_cutoff_and_custom_cashflows():
    h = load_historicals()
    last = h.iloc[-1]
    assert last.acquisitions == 16.444
    assert last.buybacks == pytest.approx(104.465)
    assert h.iloc[0].repurchase_plan == 0
    _, s = fact("GRMN", ["OperatingIncomeLoss"], "2024-12-28", "2025-02-28")
    assert s["filed"] <= "2025-02-28"
    assert s["retrieved_at"]
    with pytest.raises(ValueError):
        fact("GRMN", ["OperatingIncomeLoss"], "2024-12-28", "2024-12-01")


@pytest.mark.parametrize(
    "overrides",
    [
        {"tax_rate": 1.1},
        {"growth_shift": -2},
        {"dso": -1},
        {"leverage": -1},
        {"forecast_years": 2.5},
        {"interest_rate": math.nan},
    ],
)
def test_invalid_assumptions_rejected(overrides):
    with pytest.raises(ValueError):
        assumptions(overrides=overrides)


def test_loss_case_requires_funding_and_reconciles():
    h = load_historicals()
    a = assumptions(overrides={"margin_shift": -0.5, "growth_shift": -0.1})
    f = forecast(h, a)
    r = lbo(h, f, a)
    assert (f.ebit < 0).all()
    assert (f.taxes == 0).all()
    assert r["funding_required"] > 0
    assert (r["schedule"].debt >= 0).all()
    assert f.filter(like="check_").abs().to_numpy().max() < 1e-7
    assert f.iloc[0].fcff == pytest.approx(
        f.iloc[0].ebit + f.iloc[0].da - f.iloc[0].capex - f.iloc[0].change_nwc
    )


def test_nonfinite_history_rejected():
    h = load_historicals()
    h.loc[0, "revenue"] = float("inf")
    with pytest.raises(ValueError):
        validate(h)
