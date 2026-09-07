import pandas as pd
import pytest
from src.valuation import dcf, sensitivity, wacc
from src.comparables import comparables


def test_dcf_hand_calculation():
    f = pd.DataFrame({"fcff": [100, 110], "ebitda": [150, 160]})
    r = dcf(f, 0.1, 0.02, 50, 10)
    assert r["pv_fcff"] == pytest.approx(100 / 1.1 + 110 / 1.1**2)
    assert r["terminal_value"] == pytest.approx(110 * 1.02 / 0.08)
    assert r["equity_value"] == pytest.approx(r["enterprise_value"] - 50)
    assert r["per_share"] == pytest.approx(r["equity_value"] / 10)
    assert (
        dcf(f, 0.1, 0.02, method="multiple", exit_multiple=10)["terminal_value"] == 1600
    )


def test_sensitivities_and_invalid_growth():
    f = pd.DataFrame({"fcff": [100] * 5, "ebitda": [150] * 5})
    s = sensitivity(f, [0.08, 0.10], [0.01, 0.03])
    assert (s.iloc[0] > s.iloc[1]).all()
    assert (s.iloc[:, 1] > s.iloc[:, 0]).all()
    with pytest.raises(ValueError):
        dcf(f, 0.02, 0.03)


def test_peers_sourced_and_positive():
    peers, stats = comparables(1000)
    assert set(peers.ticker) == {"LOGI", "PII"}
    assert (peers.ev_ebitda > 0).all()
    assert stats.loc["median", "target_ev_at_ebitda_multiple"] == pytest.approx(
        peers.ev_ebitda.median() * 1000
    )


def test_zero_fcff_and_nonfinite_dcf():
    f = pd.DataFrame({"fcff": [0.0] * 5, "ebitda": [0.0] * 5})
    assert dcf(f, 0.1, 0.02)["enterprise_value"] == 0
    assert dcf(f, 0.1, 0.02)["terminal_share"] is None
    with pytest.raises(ValueError):
        dcf(f, float("nan"), 0.02)
