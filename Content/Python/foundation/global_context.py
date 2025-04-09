
import asyncio
import importlib
import sys


counter = 0# Static counter variable
loop = asyncio.SelectorEventLoop()

def get_counter() -> int:
    """Get the current value of the static counter."""
    global counter
    return counter

def increment_counter() -> int:
    """Increment the static counter by 1."""
    global counter
    counter += 1
    return counter

def rebuild_event_loop() -> None:
    """Rebuild the event loop."""
    global loop
    loop.run_until_complete(loop.shutdown_asyncgens()) 
    loop.stop()
    loop.close()
    loop = asyncio.SelectorEventLoop()
    asyncio.set_event_loop(loop)

def get_event_loop() -> asyncio.BaseEventLoop:
    """Get the current event loop name."""
    asyncio.set_event_loop(loop)
    return loop

def reload_all_modules():
    """递归重新加载所有已加载的模块"""
    for module_name in list(sys.modules.keys()):
        if module_name.startswith("foundation") or module_name.startswith("tools"):
            try:
                module = sys.modules[module_name]
                if module is not None:
                    importlib.reload(module)
                    print(f"Reloaded: {module_name}")
            except Exception as e:
                print(f"Failed to reload {module_name}: {e}")