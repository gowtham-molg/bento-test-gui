from gui.gui import PneumaticControlGUI
from utils.threading_loop import start_background_event_loop

# Start the asyncio loop in a background thread
start_background_event_loop()

# Launch the GUI
if __name__ == "__main__":
    PneumaticControlGUI()
