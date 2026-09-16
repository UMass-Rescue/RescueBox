"""Public utils API — lazy exports so submodule imports avoid loading the full graph."""

import importlib
from typing import TYPE_CHECKING, Any

from nicegui import app as _NICEGUI_APP

app = _NICEGUI_APP

if TYPE_CHECKING:
    from .backend import (
        BACKEND_AVAILABLE,
        is_backend_available,
        prefetch_and_cache_models,
        set_backend_available,
        setup_backend_routes,
    )
    from .browser import (
        browse_directory,
        browse_directory_simple,
        browse_file,
        browse_file_simple,
        get_assigned_demo_folder,
        release_demo_folder_for_client,
        resolve_demo_folder_for_browser,
    )
    from .logging import (
        clear_logging_context,
        configure_logging_with_context,
        format_audit_trail_markdown,
        generate_audit_trail_for_job,
        get_logging_context,
        parse_log_level,
        read_logs_filtered,
        set_logging_context,
    )
    from .paths import (
        apply_ufdr_mount_autofill_after_inputs_built,
        is_outputs_results_directory,
        maybe_autofill_output_dir_field,
        maybe_autofill_ufdr_mount_name_field,
        suggested_outputs_dir_path,
        suggested_ufdr_mount_folder_path,
    )
    from .storage import (
        clear_active_case_id,
        clear_conversation_to_load,
        clear_explicit_user_id,
        clear_form_draft,
        ensure_explicit_user_id_for_tests,
        get_active_case,
        get_active_case_id,
        get_conversation_to_load,
        get_current_conversation_id,
        get_draft_message,
        get_explicit_user_id,
        get_form_draft,
        get_user_id,
        get_user_id_for_jobs,
        get_user_preference,
        get_user_preferences,
        release_explicit_user_id_claim,
        reset_user_preferences,
        set_active_case_id,
        set_conversation_to_load,
        set_current_conversation_id,
        set_draft_message,
        set_explicit_user_id,
        set_form_draft,
        set_user_preference,
        set_user_preferences,
        try_claim_explicit_user_id,
    )
    from .ui import (
        apply_saved_theme,
        ensure_active_case_id,
        ensure_session_user_id,
        ensure_user_id,
        handle_api_error,
        handle_validation_error,
        notify_error,
        notify_info,
        notify_success,
        notify_warning,
        require_demo_user_session,
        select,
        show_error_to_user,
        show_success_to_user,
    )
    from .ui_readability_css import inject_global_readability_css
    from .validators import (
        paired_output_directory_field_id,
        paired_ufdr_mount_name_field_id,
        validate_form_data,
        validate_request_body,
        validate_response_body,
    )

__all__ = [
    "BACKEND_AVAILABLE",
    "app",
    "apply_saved_theme",
    "apply_ufdr_mount_autofill_after_inputs_built",
    "browse_directory",
    "browse_directory_simple",
    "browse_file",
    "browse_file_simple",
    "clear_active_case_id",
    "clear_conversation_to_load",
    "clear_explicit_user_id",
    "clear_form_draft",
    "clear_logging_context",
    "configure_logging_with_context",
    "ensure_active_case_id",
    "ensure_explicit_user_id_for_tests",
    "ensure_session_user_id",
    "ensure_user_id",
    "format_audit_trail_markdown",
    "generate_audit_trail_for_job",
    "get_active_case",
    "get_active_case_id",
    "get_assigned_demo_folder",
    "get_conversation_to_load",
    "get_current_conversation_id",
    "get_draft_message",
    "get_explicit_user_id",
    "get_form_draft",
    "get_logging_context",
    "get_user_id",
    "get_user_id_for_jobs",
    "get_user_preference",
    "get_user_preferences",
    "handle_api_error",
    "handle_validation_error",
    "inject_global_readability_css",
    "is_backend_available",
    "is_outputs_results_directory",
    "maybe_autofill_output_dir_field",
    "maybe_autofill_ufdr_mount_name_field",
    "notify_error",
    "notify_info",
    "notify_success",
    "notify_warning",
    "paired_output_directory_field_id",
    "paired_ufdr_mount_name_field_id",
    "parse_log_level",
    "prefetch_and_cache_models",
    "read_logs_filtered",
    "release_demo_folder_for_client",
    "release_explicit_user_id_claim",
    "require_demo_user_session",
    "reset_user_preferences",
    "resolve_demo_folder_for_browser",
    "select",
    "set_active_case_id",
    "set_backend_available",
    "set_conversation_to_load",
    "set_current_conversation_id",
    "set_draft_message",
    "set_explicit_user_id",
    "set_form_draft",
    "set_logging_context",
    "set_user_preference",
    "set_user_preferences",
    "setup_backend_routes",
    "show_error_to_user",
    "show_success_to_user",
    "suggested_outputs_dir_path",
    "suggested_ufdr_mount_folder_path",
    "try_claim_explicit_user_id",
    "validate_form_data",
    "validate_request_body",
    "validate_response_body",
]

_SYMBOL_SUBMODULE: dict[str, str] = {}
for _name in (
    "set_logging_context",
    "get_logging_context",
    "clear_logging_context",
    "configure_logging_with_context",
    "generate_audit_trail_for_job",
    "read_logs_filtered",
    "format_audit_trail_markdown",
    "parse_log_level",
):
    _SYMBOL_SUBMODULE[_name] = "logging"
for _name in (
    "is_outputs_results_directory",
    "suggested_outputs_dir_path",
    "maybe_autofill_output_dir_field",
    "suggested_ufdr_mount_folder_path",
    "apply_ufdr_mount_autofill_after_inputs_built",
    "maybe_autofill_ufdr_mount_name_field",
):
    _SYMBOL_SUBMODULE[_name] = "paths"
for _name in (
    "browse_directory",
    "browse_file",
    "browse_directory_simple",
    "browse_file_simple",
    "resolve_demo_folder_for_browser",
    "get_assigned_demo_folder",
    "release_demo_folder_for_client",
):
    _SYMBOL_SUBMODULE[_name] = "browser"
for _name in (
    "validate_form_data",
    "validate_response_body",
    "validate_request_body",
    "paired_output_directory_field_id",
    "paired_ufdr_mount_name_field_id",
    "_create_input_model",
    "_validate_parameter_value",
    "_format_validation_error",
):
    _SYMBOL_SUBMODULE[_name] = "validators"
for _name in (
    "get_user_id",
    "get_explicit_user_id",
    "set_explicit_user_id",
    "clear_explicit_user_id",
    "ensure_explicit_user_id_for_tests",
    "try_claim_explicit_user_id",
    "release_explicit_user_id_claim",
    "get_user_id_for_jobs",
    "get_user_preferences",
    "set_user_preference",
    "get_current_conversation_id",
    "set_current_conversation_id",
    "get_draft_message",
    "set_draft_message",
    "set_conversation_to_load",
    "get_conversation_to_load",
    "clear_conversation_to_load",
    "get_active_case_id",
    "set_active_case_id",
    "clear_active_case_id",
    "get_active_case",
    "get_form_draft",
    "set_form_draft",
    "clear_form_draft",
    "get_user_preference",
    "set_user_preferences",
    "reset_user_preferences",
):
    _SYMBOL_SUBMODULE[_name] = "storage"
for _name in (
    "notify_success",
    "notify_error",
    "notify_info",
    "notify_warning",
    "handle_api_error",
    "show_error_to_user",
    "show_success_to_user",
    "handle_validation_error",
    "ensure_session_user_id",
    "ensure_active_case_id",
    "ensure_user_id",
    "apply_saved_theme",
    "select",
    "require_demo_user_session",
):
    _SYMBOL_SUBMODULE[_name] = "ui"
_SYMBOL_SUBMODULE["inject_global_readability_css"] = "ui_readability_css"
for _name in (
    "set_backend_available",
    "is_backend_available",
    "BACKEND_AVAILABLE",
    "prefetch_and_cache_models",
    "setup_backend_routes",
):
    _SYMBOL_SUBMODULE[_name] = "backend"


def __getattr__(name: str) -> Any:
    if name == "app":
        return _NICEGUI_APP
    submodule = _SYMBOL_SUBMODULE.get(name)
    if submodule is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = importlib.import_module(f".{submodule}", __name__)
    return getattr(mod, name)
