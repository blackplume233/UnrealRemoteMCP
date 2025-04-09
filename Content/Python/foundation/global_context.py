
import asyncio


counter = 0# Static counter variable
loop = asyncio.SelectorEventLoop()
asyncio.set_event_loop(loop)
def get_counter() -> int:
    """Get the current value of the static counter."""
    global counter
    return counter

def increment_counter() -> int:
    """Increment the static counter by 1."""
    global counter
    counter += 1
    return counter

def get_event_loop() -> asyncio.BaseEventLoop:
    """Get the current event loop name."""
    global loop
    return loop