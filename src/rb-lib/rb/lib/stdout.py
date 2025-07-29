import io
import sys
from io import StringIO
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


def capture_stdout_as_generator(func, *args, **kwargs):
    import sys

    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    logger.debug(
                f"Executing capture_stdout_as_generator,with args={args}, kwargs={kwargs}"
            )
    try:
        func(*args, **kwargs)  # Run the function
        sys.stdout.flush()
        buffer.seek(0)

        while True:
            line = buffer.readline()
            if not line:
                break  # Stop streaming when done

            logger.debug(
                f"Captured line: {line.strip()}")  # Debugging print
            yield line.strip()  # Ensure it's yielding non-empty lines

    finally:
        sys.stdout = old_stdout
