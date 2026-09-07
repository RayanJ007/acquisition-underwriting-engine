import pytest
from src.data import load_historicals
from src.forecast import assumptions, forecast
from src.debt import debt_schedule


@pytest.mark.parametrize("case", ["base", "upside", "downside"])
def test_statements(case):
    h = load_historicals()
    f = forecast(h, assumptions(case))
    assert len(f) == 5
    assert f.filter(like="check_").abs().to_numpy().max() < 1e-7
    assert f.cash.min() >= 300
    assert f.iloc[0].revenue == pytest.approx(
        sum(
            v
            * (
                1
                + assumptions(case)["segment_growth"][k]
                + assumptions(case)["growth_shift"]
            )
            for k, v in __import__("src.data", fromlist=["config"])
            .config()["segments"]
            .items()
        )
    )


def test_debt_shortfall_and_full_repayment():
    d = debt_schedule(100, -10, 20, 0.1, 100, 0.1)
    assert d["borrowing"] == 40
    assert d["debt"] == 130
    assert d["cash"] == 20
    d = debt_schedule(100, 1000, 20, 0.1, 100, 0.1)
    assert d["debt"] == 0
    assert d["cash"] == 900


def test_interest_and_cash_with_levered_opening():
    h = load_historicals()
    h.loc[h.index[-1], "debt"] = 1000
    h.loc[h.index[-1], "equity"] -= 1000
    f = forecast(h, assumptions())
    assert f.iloc[0].interest == 75
    assert f.filter(like="check_").abs().to_numpy().max() < 1e-7
