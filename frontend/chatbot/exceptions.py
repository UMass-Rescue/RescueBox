"""Exception types commonly caught in chatbot API and orchestration code."""

import httpx

from frontend.utils.exceptions import HTTP_CLIENT_ERRORS

CHATBOT_ERRORS = (*HTTP_CLIENT_ERRORS, httpx.HTTPError)
