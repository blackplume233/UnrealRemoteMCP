
counter = 0# Static counter variable

def get_counter() -> int:
    """Get the current value of the static counter."""
    global counter
    return counter

def increment_counter() -> int:
    """Increment the static counter by 1."""
    global counter
    counter += 1
    return counter