import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Patch tkinter.Tk globally BEFORE importing gui
with patch("tkinter.Tk", return_value=MagicMock()):
    from gui import PneumaticControlGUI


@pytest.fixture
def gui_instance():
    gui = PneumaticControlGUI()
    gui._update_status = lambda color: setattr(gui, '_test_status', color)
    return gui


def test_on_valve_triggers_async(monkeypatch, gui_instance):
    mock_valve = AsyncMock(return_value={"ret": "OK"})
    monkeypatch.setattr("gui.pneumatic_set_valve", mock_valve)

    gui_instance.on_valve(3, True)

    # Wait briefly to allow async task to execute
    import time
    time.sleep(0.1)

    # Check async valve function was called correctly
    mock_valve.assert_called_with(3, True)
    assert gui_instance._test_status == "green"