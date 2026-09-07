import pytest
from src.data import load_historicals, validate, market


def test_real_five_year_data():
    d = load_historicals()
    assert len(d) == 5
    assert d.iloc[-1].revenue == pytest.approx(6296.903)
    assert d.iloc[-1].ebit == pytest.approx(1593.994)
    assert market("GRMN")["date"] == "2025-02-28"


def test_bad_historical_balance_rejected():
    d = load_historicals()
    d.loc[0, "equity"] += 100
    with pytest.raises(ValueError):
        validate(d)
