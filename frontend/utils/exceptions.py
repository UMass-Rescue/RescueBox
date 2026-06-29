"""Exception types commonly caught in defensive frontend utilities."""

import subprocess

UI_RENDER_ERRORS = (
    AssertionError,
    AttributeError,
    IndexError,
    KeyError,
    OSError,
    RuntimeError,
    TypeError,
    ValueError,
    subprocess.CalledProcessError,
)

HTTP_CLIENT_ERRORS = (*UI_RENDER_ERRORS, ConnectionError, TimeoutError)
