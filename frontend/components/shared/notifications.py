"""Toast helpers with module-level logging."""

from __future__ import annotations

import logging

from frontend.utils.ui import (
    notify_error as _notify_error,
)
from frontend.utils.ui import (
    notify_info as _notify_info,
)
from frontend.utils.ui import (
    notify_success as _notify_success,
)
from frontend.utils.ui import (
    notify_warning as _notify_warning,
)

logger = logging.getLogger(__name__)


def notify_success(message: str, **kwargs):
    logger.debug("Success notification shown: %s", message)
    return _notify_success(message, **kwargs)


def notify_error(message: str, **kwargs):
    logger.debug("Error notification shown: %s", message)
    return _notify_error(message, **kwargs)


def notify_info(message: str, **kwargs):
    logger.debug("Info notification shown: %s", message)
    return _notify_info(message, **kwargs)


def notify_warning(message: str, **kwargs):
    logger.debug("Warning notification shown: %s", message)
    return _notify_warning(message, **kwargs)
