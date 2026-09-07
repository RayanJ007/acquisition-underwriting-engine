from streamlit.testing.v1 import AppTest
from pathlib import Path


def test_dashboard_controls_and_error_state():
    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "dashboard/app.py", default_timeout=30
    ).run()
    assert not app.exception
    before = app.metric[2].value
    app.slider[0].set_value(2.0).run()
    assert not app.exception
    assert app.metric[2].value != before
    app.slider[2].set_value(5.0)
    app.slider[3].set_value(5.0).run()
    assert app.error
