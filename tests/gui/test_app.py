"""The Streamlit script itself, driven headlessly with Streamlit's AppTest."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from multiverse_studio.gui.state import Workbench  # noqa: E402

APP = str(Path(__file__).resolve().parents[2] / "src" / "multiverse_studio" / "gui" / "app.py")


@pytest.fixture
def at(tmp_path) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["wb"] = Workbench(data_dir=tmp_path)
    app.run()
    assert not app.exception
    return app


def test_welcome_then_full_workflow(at):
    assert at.button(key="run").disabled
    at.radio[0].set_value("collider").run()
    at.button(key="use_example_0").click().run()
    wb: Workbench = at.session_state["wb"]
    assert wb.data_name == "example_collider.csv" and not at.exception

    at.selectbox(key="q_y_1").set_value("grade").run()
    at.selectbox(key="q_x_1").set_value("sleep_hours").run()
    assert wb.session.family == "linear"
    at.button(key="confirm_choices_1").click().run()
    for j, word in enumerate(["No", "Yes", "Yes"]):
        at.button_group(key=f"g_1_scholarship_{j}").set_value(word).run()
    assert wb.assessment("scholarship").keep is False
    at.button(key="confirm_fair_1").click().run()
    at.selectbox(key="perm_1").set_value("Skip").run()
    assert not at.button(key="run").disabled

    at.button(key="run").click().run()
    assert wb.session.blind is not None
    wb.job.wait(120)
    at.run()
    at.run()
    assert not at.exception
    assert wb.session.verdict is not None
    assert len(at.get("download_button")) == 3
    at.number_input(key=f"reported_{wb.run_id}").set_value(99.0).run()
    assert wb.session.cherry_pick.flagged and not at.exception

    at.button(key="start_over").click().run()
    assert wb.df is None and not at.exception


def test_bad_upload_shows_error(at):
    wb: Workbench = at.session_state["wb"]
    wb.load_upload("data.pdf", b"x")
    at.run()
    assert not at.exception and wb.notice[0] == "critical"
