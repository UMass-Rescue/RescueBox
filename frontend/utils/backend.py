import logging

logger = logging.getLogger(__name__)

_BACKEND_AVAILABLE = False
BACKEND_AVAILABLE = _BACKEND_AVAILABLE


def set_backend_available(value: bool):
    global _BACKEND_AVAILABLE, BACKEND_AVAILABLE
    _BACKEND_AVAILABLE = value
    BACKEND_AVAILABLE = value
    logger.info("Backend availability set to: %s", value)


def is_backend_available() -> bool:
    return _BACKEND_AVAILABLE


async def prefetch_and_cache_models(api_client=None, backend_url="", api_timeout=30):
    """Prefetch all model metadata and cache it in the database."""
    from frontend.database import cache_models

    if api_client is None:
        from frontend.api_client import api_client as default_client

        api_client = default_client

    try:
        logger.info("Prefetching model metadata...")
        response = await api_client.get("/models", use_api_prefix=True)
        response.raise_for_status()

        models_data = await api_client.json(response)
        if models_data:
            logger.info(
                "Successfully pre-fetched %s models from the backend.", len(models_data)
            )
            await cache_models(models_data)
        else:
            logger.warning(
                "Pre-fetching models returned no data. Skipping cache update."
            )
    except Exception as e:
        logger.warning("Failed to prefetch models: %s", e)


def setup_backend_routes(api_base_url: str = ""):
    """Placeholder for dynamic backend route registration."""
    logger.debug("setup_backend_routes called with %s", api_base_url)
