"""
Propagate RescueBox session user id into the face-match plugin via ContextVar.

The face-detection-recognition package reads :data:`facematch_rescuebox_user_id` so Chroma
collection lists and embeddings are isolated per explicit desktop user.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

RESCUEBOX_USER_HEADER = "x-rescuebox-user-id"


class FacematchRescueboxUserMiddleware(BaseHTTPMiddleware):
    """Set ``facematch_rescuebox_user_id`` from ``X-RescueBox-User-Id`` for plugin routes."""

    async def dispatch(self, request: Request, call_next):
        uid = request.headers.get(RESCUEBOX_USER_HEADER)
        if not uid:
            return await call_next(request)
        try:
            from face_detection_recognition.database_functions import (
                facematch_rescuebox_user_id,
            )
        except ImportError:
            return await call_next(request)
        token = facematch_rescuebox_user_id.set(uid)
        try:
            return await call_next(request)
        finally:
            facematch_rescuebox_user_id.reset(token)
