"""Database package — lazy re-exports (submodules avoid pulling the full graph)."""

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .case_db import (
        CaseDB,
        CaseRecord,
        get_case_db,
    )
    from .case_db import (
        init_database as init_case_database,
    )
    from .chat_history_db import (
        ChatMessageRecord,
        ConversationRecord,
        get_chat_history_db,
    )
    from .job_db import get_job_db
    from .job_db import init_database as init_job_database
    from .job_models import JobRecord, JobStatus
    from .model_cache import (
        cache_models,
        get_cached_model_by_uid,
        get_cached_models,
        init_db,
    )

__all__ = [
    "CaseDB",
    "CaseRecord",
    "ChatMessageRecord",
    "ConversationRecord",
    "JobRecord",
    "JobStatus",
    "cache_models",
    "get_cached_model_by_uid",
    "get_cached_models",
    "get_case_db",
    "get_chat_history_db",
    "get_job_db",
    "init_case_database",
    "init_db",
    "init_job_database",
]

# name -> (submodule, attribute on submodule; default same as name)
_EXPORTS: dict[str, tuple[str, str]] = {
    "init_db": ("model_cache", "init_db"),
    "cache_models": ("model_cache", "cache_models"),
    "get_cached_models": ("model_cache", "get_cached_models"),
    "get_cached_model_by_uid": ("model_cache", "get_cached_model_by_uid"),
    "JobRecord": ("job_models", "JobRecord"),
    "JobStatus": ("job_models", "JobStatus"),
    "get_job_db": ("job_db", "get_job_db"),
    "init_job_database": ("job_db", "init_database"),
    "ConversationRecord": ("chat_history_db", "ConversationRecord"),
    "ChatMessageRecord": ("chat_history_db", "ChatMessageRecord"),
    "get_chat_history_db": ("chat_history_db", "get_chat_history_db"),
    "CaseRecord": ("case_db", "CaseRecord"),
    "CaseDB": ("case_db", "CaseDB"),
    "get_case_db": ("case_db", "get_case_db"),
    "init_case_database": ("case_db", "init_database"),
}


def __getattr__(name: str) -> Any:
    spec = _EXPORTS.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    submodule, attr = spec
    mod = importlib.import_module(f".{submodule}", __name__)
    return getattr(mod, attr)
