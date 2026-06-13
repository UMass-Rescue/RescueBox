"""
Models aggregation routes for frontend compatibility.

Provides unified endpoints to discover and access plugin metadata,
matching the frontend's expectations for /models and /servers endpoints.
"""

import logging
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException, status
from rb.api.models import API_APPMETDATA
from rescuebox.main import app as rescuebox_app
from rb.api.routes.cli import static_endpoint

logger = logging.getLogger(__name__)

# Logging: configured in ``frontend.main`` (unified app) or ``rb.api.main`` (standalone API).

models_router = APIRouter()


def _get_plugin_metadata(plugin_name: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a plugin by calling its app_metadata endpoint.

    Args:
        plugin_name: The plugin's CLI name (e.g., "audio_transcription")

    Returns:
        Dict with plugin metadata or None if not available

    Tips:
    - Searches through registered groups to find the plugin
    - Calls the app_metadata command directly using static_endpoint
    - Handles different return types (dict, ResponseBody, Pydantic models)
    """
    try:
        logger.debug(f"Fetching metadata for plugin: {plugin_name}")
        # Find the plugin in registered groups
        for plugin in rescuebox_app.registered_groups:
            if plugin.name == plugin_name:
                # Find the app_metadata command
                for command in plugin.typer_instance.registered_commands:
                    if command.name and command.name.endswith(API_APPMETDATA):
                        logger.debug(f"Found app_metadata command: {command.name}")
                        # Call the command directly
                        result = static_endpoint(command.callback)

                        # Handle different return types
                        if isinstance(result, dict):
                            logger.debug(f"Metadata returned as dict for {plugin_name}")
                            return result
                        elif hasattr(result, "root") and isinstance(result.root, dict):
                            logger.debug(
                                f"Metadata returned as ResponseBody with dict root for {plugin_name}"
                            )
                            return result.root
                        elif hasattr(result, "model_dump"):
                            logger.debug(
                                f"Metadata returned as Pydantic model for {plugin_name}"
                            )
                            return result.model_dump()
                        logger.warning(
                            f"Unexpected metadata format for {plugin_name}: {type(result)}"
                        )
                        return None
        logger.warning(f"Plugin {plugin_name} not found in registered groups")
        return None
    except Exception as e:
        logger.warning(f"Error fetching metadata for plugin {plugin_name}: {e}")
        return None


@models_router.get("/models")
async def get_models() -> List[Dict[str, Any]]:
    """
    Get list of all available models/plugins.

    Aggregates metadata from all registered plugins and returns
    a unified list compatible with frontend expectations.

    Returns:
        List of model dictionaries with uid, name, version, etc.

    Tips:
    - Iterates through all registered plugin groups
    - Fetches metadata for each plugin
    - Returns unified format expected by frontend
    - Includes fallback values if metadata unavailable
    """
    logger.info(
        "API Endpoint /models called: Aggregating metadata from all registered plugins"
    )
    models = []

    for plugin in rescuebox_app.registered_groups:
        plugin_name = plugin.name
        logger.debug(f"Processing plugin: {plugin_name}")
        metadata = _get_plugin_metadata(plugin_name)

        if metadata:
            # Transform to frontend-expected format
            model_dict = {
                "uid": plugin_name,  # Use plugin name as UID
                "name": metadata.get("name", plugin_name),
                "plugin_name": metadata.get("plugin_name", plugin_name),
                "version": metadata.get("version", "unknown"),
                "author": metadata.get("author", "unknown"),
                "info": metadata.get("info", ""),
                "gpu": metadata.get("gpu", False),
            }
            models.append(model_dict)
            logger.debug(f"Added model: {model_dict['name']} (uid: {plugin_name})")
        else:
            # Fallback if metadata not available
            logger.warning(
                f"No metadata found for plugin {plugin_name}, using defaults"
            )
            models.append(
                {
                    "uid": plugin_name,
                    "name": plugin_name,
                    "plugin_name": plugin_name,
                    "version": "unknown",
                    "author": "unknown",
                    "info": "",
                    "gpu": False,
                }
            )

    logger.info(f"Returning {len(models)} models")
    return models


@models_router.get("/models/{model_uid}")
async def get_model_by_uid(model_uid: str) -> Dict[str, Any]:
    """
    Get metadata for a specific model by UID (plugin name).

    Args:
        model_uid: Plugin name (e.g., "audio_transcription")

    Returns:
        Model metadata dictionary

    Raises:
        HTTPException: If model not found

    Tips:
    - Uses plugin name as model UID
    - Returns same format as /models endpoint
    - Raises 404 if plugin doesn't exist
    """
    logger.info(f"Fetching model: {model_uid}")
    metadata = _get_plugin_metadata(model_uid)

    if not metadata:
        logger.error(f"Model not found: {model_uid}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model not found: {model_uid}",
        )

    # Transform to frontend-expected format
    result = {
        "uid": model_uid,
        "name": metadata.get("name", model_uid),
        "plugin_name": metadata.get("plugin_name", model_uid),
        "version": metadata.get("version", "unknown"),
        "author": metadata.get("author", "unknown"),
        "info": metadata.get("info", ""),
        "gpu": metadata.get("gpu", False),
    }
    logger.debug(f"Returning model metadata for {model_uid}")
    return result


@models_router.get("/models/{model_uid}/info")
async def get_model_info(model_uid: str) -> Dict[str, Any]:
    """
    Alternative endpoint for model metadata (alias for /models/{model_uid}).

    Args:
        model_uid: Plugin name

    Returns:
        Model metadata dictionary

    Tips:
    - Provides compatibility with frontend that may call /info endpoint
    - Simply delegates to get_model_by_uid
    """
    logger.debug(f"Fetching model info via /info endpoint: {model_uid}")
    return await get_model_by_uid(model_uid)


@models_router.get("/servers")
async def get_servers() -> List[Dict[str, Any]]:
    """
    Get list of all registered servers.

    Returns all models with the current backend server (localhost:8000)
    as their server, since all plugins are served by this backend.

    Returns:
        List of server dictionaries, one per registered plugin/model

    Tips:
    - All plugins are served by the same backend server (localhost:8000)
    - Returns one server entry per registered plugin
    - Each entry includes modelUid (plugin name) and indicates the backend server
    - Frontend expects list of dicts with 'modelUid' key
    """
    logger.info("Fetching servers")
    servers = []

    # Return one server entry per registered plugin
    # All plugins are served by the current backend server
    for plugin in rescuebox_app.registered_groups:
        plugin_name = plugin.name
        servers.append(
            {
                "modelUid": plugin_name,
                "serverAddress": "localhost",
                "serverPort": 8000,
                "isUserConnected": True,
                "pluginName": plugin_name,
            }
        )
        logger.debug(f"Added server entry for plugin: {plugin_name}")

    logger.info(f"Returning {len(servers)} server entries")
    return servers


@models_router.get("/servers/{model_uid}/status")
async def get_server_status(model_uid: str) -> Dict[str, Any]:
    """
    Get server status for a specific model.

    Args:
        model_uid: Plugin name

    Returns:
        Status dictionary with 'status' key ('Online' or 'Offline')

    Note: Returns 'Online' for all registered plugins since they are
    all served by the current backend server. If the plugin doesn't exist,
    returns 404.

    Tips:
    - Checks if plugin exists in registered groups
    - Returns Online for all existing plugins (served by current backend)
    - Returns 404 if plugin doesn't exist
    """
    logger.info(f"Checking server status for: {model_uid}")

    # Check if plugin exists
    for plugin in rescuebox_app.registered_groups:
        if plugin.name == model_uid:
            # Plugin exists and is served by the current backend server
            # Return Online status since the backend is running
            logger.debug(f"Plugin {model_uid} exists, returning Online status")
            return {
                "status": "Online",
                "modelUid": model_uid,
                "serverAddress": "localhost",
                "serverPort": 8000,
            }

    logger.warning(f"Server not found for model: {model_uid}")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Server not found for model: {model_uid}",
    )
