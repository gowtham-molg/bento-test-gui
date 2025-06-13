import asyncio
import logging
from utils.threading_loop import get_loop

logger = logging.getLogger(__name__)

# Schedule coroutine on the background event loop
def schedule_coro(coro):
    loop = get_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)

    def _on_done(fut):
        try:
            fut.result()
        except Exception:
            logger.exception("Async task failed")

    future.add_done_callback(_on_done)