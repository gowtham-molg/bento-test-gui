import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Patch tk.Tk globally before importing gui
with patch("tkinter.Tk", return_value=MagicMock()):
    from gui import PneumaticControlGUI

class DummyRoot:
    def after(self, ms, func):
        func()

@pytest.fixture
def gui_instance():
    gui = PneumaticControlGUI()
    gui.root = DummyRoot()  # replace real Tk root for testing
    gui._update_status = lambda color: setattr(gui, '_test_status', color)
    return gui

def test_on_valve_triggers_async(monkeypatch, gui_instance):
    mock_valve = AsyncMock(return_value={"ret": "OK"})
    monkeypatch.setattr("gui.pneumatic_set_valve", mock_valve)

    gui_instance.on_valve(3, True)

    # Allow coroutine to be scheduled
    import time; time.sleep(0.1)

    # Check the async function was called correctly
    mock_valve.assert_called_with(3, True)
    # Check the GUI status was updated to green (success)
    assert gui_instance._test_status == "green"
