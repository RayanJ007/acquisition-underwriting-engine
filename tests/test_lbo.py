import pytest
from src.data import load_historicals
from src.forecast import assumptions, forecast
from src.lbo import lbo, returns, maximum_entry_ev
from src.scenarios import run_scenarios
from src.diligence import quality_of_earnings


@pytest.fixture
def setup():
    h = load_historicals()
    a = assumptions()
    return h, forecast(h, a), a


def test_returns_known_cashflows():
    assert returns(100, 200, 5)["moic"] == 2
    assert returns(100, 200, 5)["irr"] == pytest.approx(2**0.2 - 1)
    assert returns(100, 0, 5)["irr"] == -1


def test_sources_uses_and_sweep(setup):
    h, f, a = setup
    r = lbo(h, f, a)
    assert abs(r["sources_uses_check"]) < 1e-8
    s = r["schedule"]
    assert (s.debt >= 0).all()
    assert (
        s.opening_debt
        + s.borrowing
        - s.mandatory_repayment
        - s.optional_repayment
        - s.debt
    ).abs().max() < 1e-7
    assert r["sources"]["sponsor_equity"] == pytest.approx(
        r["entry_ev"]
        + r["uses"]["fees"]
        + a["minimum_cash"]
        - r["sources"]["term_debt"]
    )


def test_entry_price_solver_and_directionality(setup):
    h, f, a = setup
    ev = maximum_entry_ev(h, f, a)
    assert lbo(h, f, a, ev)["irr"] == pytest.approx(0.2, abs=1e-8)
    assert lbo(h, f, a, ev * 1.1)["irr"] < lbo(h, f, a, ev)["irr"]


def test_scenarios_recalculate(setup):
    h, _, _ = setup
    s = run_scenarios(h)
    assert (
        s["upside"]["lbo"]["irr"]
        > s["base"]["lbo"]["irr"]
        > s["downside"]["lbo"]["irr"]
    )
    assert (
        s["downside"]["forecast"].iloc[-1].revenue
        < s["base"]["forecast"].iloc[-1].revenue
    )


def test_qoe_no_unsubstantiated_adjustments(setup):
    h, _, _ = setup
    bridge, summary = quality_of_earnings(h)
    assert summary["adjusted_ebitda"] == h.iloc[-1].ebitda
    with pytest.raises(ValueError):
        quality_of_earnings(h, [{"amount": 50}])
