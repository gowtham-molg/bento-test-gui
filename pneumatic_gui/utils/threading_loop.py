import asyncio
import threading

# Create a dedicated asyncio event loop for the application
loop = asyncio.new_event_loop()

def start_background_event_loop():
    def _start_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    threading.Thread(target=_start_loop, daemon=True).start()

# Allow other modules to schedule coroutines on this loop
def get_loop():
    return loop
