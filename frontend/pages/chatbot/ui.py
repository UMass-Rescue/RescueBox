from __future__ import annotations
import logging
import asyncio
import json
from typing import Any, Dict, Optional
from nicegui import ui

from frontend.chatbot.config import ChatbotConfig, ToolRegistry
from frontend.chatbot.core import ChatbotCore
from frontend.components.errors import render_error_message
from frontend.components.shared import create_navbar
from frontend.design_tokens import Design
from frontend.pages.chatbot.state import ChatbotStateManager, ChatMessage
from frontend.utils import (
    get_conversation_to_load,
    handle_api_error as _handle_api_error,
    show_error_to_user as _show_error_to_user,
)

separator = ui.separator
label = ui.label
row = ui.row
column = ui.column
card = ui.card
button = ui.button
badge = ui.badge
icon = ui.icon
image = ui.image
markdown = ui.markdown
html = ui.html
input = ui.input
textarea = ui.textarea
checkbox = ui.checkbox
switch = ui.switch
select = ui.select
radio = ui.radio
slider = ui.slider
number = ui.number
date = ui.date
time = ui.time
upload = ui.upload
spinner = ui.spinner
link = ui.link
dialog = ui.dialog
menu = ui.menu
menu_item = ui.menu_item
tabs = ui.tabs
tab = ui.tab
tab_panels = ui.tab_panels
tab_panel = ui.tab_panel
scroll_area = ui.scroll_area
expansion = ui.expansion
stepper = ui.stepper
step = ui.step
stepper_navigation = ui.stepper_navigation
linear_progress = ui.linear_progress
circular_progress = ui.circular_progress
notify = ui.notify
timer = ui.timer
query = ui.query
navigate = ui.navigate
run_javascript = ui.run_javascript
element = ui.element
page = ui.page
chat_message = ui.chat_message
code = ui.code

def show_error_to_user(*args, **kwargs):
    return _show_error_to_user(*args, **kwargs)

async def handle_api_error(*args, **kwargs):
    return await _handle_api_error(*args, **kwargs)

# Storage safety for tests handled via try/except in storage utils

logger = logging.getLogger(__name__)

class FormConfig:
    """Configuration and styling constants for chatbot forms."""
    FORM_REVEAL_OUTER_CLASSES = "w-full space-y-4 opacity-0 transition-opacity duration-300 rb-form-reveal-outer"
    FORM_SCROLL_AFTER_REVEAL_DELAY_S = 0.35

class UIOperations:
    """UI operations for the chatbot interface."""
    @staticmethod
    def scroll_to_bottom(client=None):
        js = "window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});"
        if client:
            client.run_javascript(js)
        else:
            ui.run_javascript(js)

    @staticmethod
    def scroll_form_into_view(client=None):
        js = "const el = document.querySelector('.rb-form-wrapper'); if(el) el.scrollIntoView({behavior: 'smooth', block: 'center'});"
        if client:
            client.run_javascript(js)
        else:
            ui.run_javascript(js)

    @staticmethod
    def scroll_form_into_view_with_retries(client=None):
        for delay in [0.1, 0.3, 0.7]:
            ui.timer(delay, lambda: UIOperations.scroll_form_into_view(client), once=True)

    @staticmethod
    def safe_notify(message: str, type: str = 'info', **kwargs):
        try:
            ui.notify(message, type=type, **kwargs)
        except Exception:
            pass

    @staticmethod
    async def safe_container_update(container):
        try:
            container.update()
        except Exception:
            pass

def render_message(container: element, message: ChatMessage):
    """Render a message in the chat container."""
    with container:
        if message.role == 'user':
            chat_message(message.content, name='You', sent=True)
        else:
            chat_message(message.content, name='Assistant')


def _history_record_to_chat_message(msg: Any) -> ChatMessage:
    """Map DB ``ChatMessageRecord`` to in-memory :class:`ChatMessage` (preserve type & payload)."""
    meta: Dict[str, Any] = {}
    raw = getattr(msg, "metadata", None)
    if isinstance(raw, dict):
        meta.update(raw)
    if getattr(msg, "tool_call_endpoint", None):
        meta["tool_call_endpoint"] = msg.tool_call_endpoint
    ta = getattr(msg, "tool_call_arguments", None)
    if ta is not None:
        meta["tool_call_arguments"] = ta
    tcs = getattr(msg, "tool_calls", None)
    if tcs:
        meta["tool_calls"] = tcs
    return ChatMessage(
        role=getattr(msg, "role", "assistant"),
        content=getattr(msg, "content", "") or "",
        id=getattr(msg, "message_id", None),
        metadata=meta or None,
        message_type=getattr(msg, "message_type", "text") or "text",
    )


def _is_adjacent_job_started_then_completed(started: Any, completed: Any) -> bool:
    """True when DB has back-to-back tool_result rows for the same job (run → done)."""
    if getattr(started, "message_type", "") != "tool_result":
        return False
    if getattr(completed, "message_type", "") != "tool_result":
        return False
    js = (getattr(started, "metadata", None) or {}).get("job_id")
    jc = (getattr(completed, "metadata", None) or {}).get("job_id")
    if not js or js != jc:
        return False
    sa = (getattr(started, "metadata", None) or {}).get("status", "")
    sc = (getattr(completed, "metadata", None) or {}).get("status", "")
    if str(sa).upper() == "RUNNING" and str(sc).lower() == "completed":
        return True
    ta = (getattr(started, "content", "") or "").lower()
    tb = (getattr(completed, "content", "") or "").lower()
    if "started" in ta and ("completed" in tb or "successfully" in tb):
        return True
    return False


def render_merged_job_tool_results(container: element, started_msg: Any, completed_msg: Any) -> None:
    """
    Single card for a job lifecycle row pair: no duplicate job-details buttons.

    Uses ``started_msg`` for inputs/parameters (only the start row stores the snapshot).
    """
    with container:
        with card().classes(
            "w-full max-w-3xl border border-zinc-200 rounded-xl p-4 bg-white "
            "shadow-sm space-y-2"
        ):
            label("Assistant").classes("text-xs font-semibold text-zinc-500 uppercase")
            label((getattr(started_msg, "content", "") or "").strip()).classes(
                "text-sm text-zinc-900 whitespace-pre-wrap break-words"
            )
            label((getattr(completed_msg, "content", "") or "").strip()).classes(
                "text-sm text-green-800 font-medium whitespace-pre-wrap break-words"
            )
            ep = getattr(started_msg, "tool_call_endpoint", None)
            if ep:
                try:
                    dn = ToolRegistry.display_name_for_endpoint(ep)
                except Exception:
                    dn = ep
                label(f"Plugin: {dn}").classes("text-xs text-zinc-500")
            args = getattr(started_msg, "tool_call_arguments", None)
            if isinstance(args, dict) and (
                args.get("inputs") is not None or args.get("parameters") is not None
            ):
                with expansion("Job inputs & parameters", value=False).classes("w-full"):
                    code(json.dumps(args, indent=2, default=str)).classes(
                        "text-xs w-full whitespace-pre-wrap break-all"
                    )
            meta = getattr(started_msg, "metadata", None) or {}
            jid = meta.get("job_id") if isinstance(meta, dict) else None
            if jid:

                def _open_job() -> None:
                    navigate.to(f"/jobs/{jid}")

                button("Open job details", icon="open_in_new", on_click=_open_job).classes(
                    f"mt-1 {Design.BTN_MEDIUM_GRAY}"
                )


def render_persisted_history_message(container: element, msg: Any) -> None:
    """
    Render one persisted row in the main chat (matches v3_demo rich history: job payload, tool calls).

    Plain :func:`render_message` only sees role+text, so loaded chats would lose
    ``tool_call_arguments`` (saved job inputs) and message type.
    """
    mt = getattr(msg, "message_type", None) or "text"
    role = getattr(msg, "role", "assistant")
    content = (getattr(msg, "content", None) or "").strip()

    if mt == "tool_result":
        with container:
            with card().classes(
                "w-full max-w-3xl border border-zinc-200 rounded-xl p-4 bg-white "
                "shadow-sm space-y-2"
            ):
                label("Assistant").classes("text-xs font-semibold text-zinc-500 uppercase")
                label(content).classes("text-sm text-zinc-900 whitespace-pre-wrap break-words")
                ep = getattr(msg, "tool_call_endpoint", None)
                if ep:
                    try:
                        dn = ToolRegistry.display_name_for_endpoint(ep)
                    except Exception:
                        dn = ep
                    label(f"Plugin: {dn}").classes("text-xs text-zinc-500")
                args = getattr(msg, "tool_call_arguments", None)
                if isinstance(args, dict) and (
                    args.get("inputs") is not None or args.get("parameters") is not None
                ):
                    with expansion("Job inputs & parameters", value=False).classes("w-full"):
                        code(json.dumps(args, indent=2, default=str)).classes(
                            "text-xs w-full whitespace-pre-wrap break-all"
                        )
                meta = getattr(msg, "metadata", None) or {}
                if isinstance(meta, dict) and meta.get("job_id"):
                    jid = meta["job_id"]

                    def _open_job() -> None:
                        navigate.to(f"/jobs/{jid}")

                    button("Open job details", icon="open_in_new", on_click=_open_job).classes(
                        f"mt-1 {Design.BTN_MEDIUM_GRAY}"
                    )
        return

    if mt == "tool_call":
        with container:
            with card().classes(
                "w-full max-w-3xl border border-zinc-200 rounded-xl p-4 "
                "bg-amber-50/80 space-y-2"
            ):
                label("Tool call").classes("text-xs font-semibold text-[#881c1c]")
                tcalls = getattr(msg, "tool_calls", None) or []
                if tcalls:
                    code(json.dumps(tcalls, indent=2, default=str)).classes(
                        "text-xs w-full whitespace-pre-wrap"
                    )
                elif content:
                    label(content).classes("text-sm text-zinc-800")
                message_id = getattr(msg, "message_id", None)
                if message_id:
                    from frontend.components.chat import rerun_tool_call

                    async def _do_rerun(mid: str = message_id) -> None:
                        await rerun_tool_call(mid)

                    button("Re-run Job", icon="replay", on_click=_do_rerun).classes(
                        f"mt-1 {Design.BTN_MEDIUM_GRAY}"
                    )
        return

    if mt == "error":
        with container:
            with card().classes("w-full max-w-3xl border border-red-200 bg-red-50 p-4 space-y-1"):
                label("Error").classes("text-xs font-semibold text-red-800")
                label(content).classes("text-sm text-red-900 whitespace-pre-wrap")
        return

    with container:
        if role == "user":
            chat_message(content, name="You", sent=True)
        else:
            chat_message(content, name="Assistant")


def show_error_message(container: element, message: str):
    """Show an error message in the chat container."""
    render_error_message(container, message)

async def show_tool_picker(container: ui.element, tool_registry, on_tool_selected):
    from frontend.pages.chatbot.handlers import ToolPicker
    picker = ToolPicker(container, tool_registry, on_tool_selected)
    await picker.show()

async def show_analysis_picker(container: ui.element, on_analysis_selected):
    from frontend.pages.chatbot.handlers import AnalysisPicker
    picker = AnalysisPicker(container, on_analysis_selected)
    await picker.show()

async def show_tool_selection(container: element, endpoint: str):
    from frontend.components.results import render_tool_selection_message
    try:
        render_tool_selection_message(container, endpoint)
    except Exception:
        with container:
            label(f"Running {endpoint}...").classes('text-sm text-zinc-500 italic')

async def load_and_show_form(container, core, endpoint, arguments, on_form_submit, on_form_cancel=None):
    try:
        task_schema = await core.get_task_schema_from_endpoint(endpoint)
        if not task_schema:
            await handle_api_error(ValueError(f"Could not load tool configuration for {endpoint}"), "Form loading")
            return
        
        initial_values = core.convert_arguments_to_initial_values(arguments, task_schema, endpoint)
        
        async def _wrapped_submit(form_data, endpoint=None, task_schema=None, **kwargs):
            # chatbot/forms.py's handle_submit passes (validated, endpoint, task_schema)
            # as positional arguments.
            return await on_form_submit(form_data, endpoint=endpoint, task_schema=task_schema, **kwargs)
        
        await core.create_input_form(
            task_schema, endpoint, initial_values=initial_values,
            on_submit=_wrapped_submit, on_cancel=on_form_cancel, container=container
        )
    except Exception as e:
        logger.exception("Error in load_and_show_form: %s", e)
        await handle_api_error(e, "Form loading")
        show_error_message(container, f"Failed to load form: {str(e)}")

async def show_results(
    container: element,
    response_body,
    job_id: Optional[str] = None,
    **kwargs
):
    """
    Show a compact job completed strip with one green button to open full results.
    Kept for API compatibility with legacy tests.
    """
    try:
        with container:
            await _show_results_body(container, response_body, job_id, **kwargs)
    except Exception as e:
        logger.error("Error showing results: %s", e)
        await handle_api_error(e, "Results rendering")

async def _show_results_body(
    container: element,
    response_body,
    job_id: Optional[str],
    **kwargs
) -> None:
    """Accented card indicating job completion."""
    with container:
        # rb-job-result-anchor: scroll helpers target this after async render
        with card().classes(
            'rb-job-result-anchor w-full max-w-md rounded-xl border-2 border-green-400 '
            'bg-gradient-to-br from-green-50 to-emerald-50 p-4 shadow-sm flex flex-col gap-3'
        ):
            label('Job completed').classes('text-base font-semibold text-green-900')

            if job_id:
                def _open_results() -> None:
                    navigate.to(f'/jobs/{job_id}')

                button(
                    'View results',
                    icon='open_in_new',
                    on_click=_open_results,
                ).classes(
                    'w-full bg-green-600 hover:bg-green-700 text-white '
                    'font-medium py-3 rounded-lg shadow-sm'
                )

class ChatUIBuilder:
    def __init__(self, on_send, on_new_conversation, on_conversation_select, on_rerun_tool, tool_registry, core, form_submit_handler, status_text_ref=None, state_manager=None):
        self.on_send = on_send
        self.on_new_conversation = on_new_conversation
        self.on_conversation_select = on_conversation_select
        self.on_rerun_tool = on_rerun_tool
        self.tool_registry = tool_registry
        self.core = core
        self.form_submit_handler = form_submit_handler
        self.status_text_ref = status_text_ref
        self.state_manager = state_manager
        self.models_btn = None
        self.analyze_btn = None
        self.history_btn = None

    def build_ui(self):
        from frontend.components.chat import create_chat_header, create_chat_window, create_input_area
        
        with column().classes("rb-chat-layout-core min-h-screen w-full flex flex-col -mt-16 bg-zinc-50 relative"):
            self.models_btn, self.analyze_btn, self.history_btn = create_chat_header(
                on_show_history=self._show_history_dialog
            )
            
            with column().classes('container mx-auto w-full px-4 flex-1 flex flex-col min-h-0 pb-4'):
                with card().classes(Design.PANEL_SHELL_CHAT_CARD):
                    with row().classes(Design.PANEL_SHELL_HEADER):
                        label('RescueBox Assistant').classes(Design.PANEL_SHELL_HEADER_TITLE)
                        self.mode_indicator = badge('Chat mode', color=None).classes('text-xs font-medium rb-chat-mode-badge')

                    chat_container = create_chat_window()
                    input_area = create_input_area(self.status_text_ref, self.on_send)
                    self.input_field = input_area.input_field

                below_input_area = column().classes('rb-chat-below-input-area w-full max-w-none space-y-4 mt-2 mb-4')

            self._setup_mode_handlers(chat_container)

        self.chat_container = chat_container
        return chat_container, self.input_field, self.status_text_ref, input_area, below_input_area

    def _setup_mode_handlers(self, chat_container):
        async def handle_models_click():
            self.mode_indicator.set_text('Menu mode')
            chat_container.clear()
            await asyncio.sleep(0.01) # Give NiceGUI a moment
            from .handlers import ToolPicker
            picker = ToolPicker(chat_container, self.tool_registry, self._on_tool_selected)
            await picker.show()

        async def handle_analyze_click():
            self.mode_indicator.set_text('Chat mode')
            chat_container.clear()
            from frontend.components.chat import render_welcome_message
            render_welcome_message(chat_container)

        self.models_btn.on_click(handle_models_click)
        self.analyze_btn.on_click(handle_analyze_click)

    async def _on_tool_selected(self, endpoint, arguments):
        async def handle_form_submit(request_body, endpoint=None, task_schema=None, **kwargs):
            return await self.form_submit_handler.submit_form(
                request_body, endpoint, task_schema, self.chat_container, self.core, **kwargs
            )
        
        def _on_cancel():
            if self.state_manager:
                self.state_manager.set_input_enabled(True)

        # Stage 1: Grey out input area while form is being filled
        if self.state_manager:
            self.state_manager.set_input_enabled(False, hide_completely=False)

        await load_and_show_form(self.chat_container, self.core, endpoint, arguments or {}, handle_form_submit, on_form_cancel=_on_cancel)
        UIOperations.scroll_form_into_view_with_retries()

    async def _show_history_dialog(self):
        from frontend.components.chat import show_history_dialog
        await show_history_dialog(
            on_conversation_select=self.on_conversation_select,
        )

class ChatbotPage:
    _instance = None

    @classmethod
    def get_instance(cls):
        return cls._instance

    def __init__(self, config: Optional[ChatbotConfig] = None):
        ChatbotPage._instance = self
        self.config = config or ChatbotConfig()
        self.core = ChatbotCore(self.config)
        from frontend.chatbot.message_handler import MessageHandler
        self.message_handler = MessageHandler(self.core, self.config)
        self.tool_registry = ToolRegistry()
        self.state_manager = ChatbotStateManager()
        
        from frontend.pages.chatbot.coordinator import MessageFlowCoordinator
        self.message_flow_coordinator = MessageFlowCoordinator(self.state_manager, self.load_and_show_form)
        self.message_flow_coordinator.set_message_handler(self.message_handler)
        self.message_flow_coordinator.set_tool_registry(self.tool_registry)
        
        self.form_handler = self.message_flow_coordinator.form_submit_handler

    async def render(self):
        builder = ChatUIBuilder(
            on_send=self._handle_send_message,
            on_new_conversation=self._handle_new_conversation,
            on_conversation_select=self._handle_conversation_select,
            on_rerun_tool=self._handle_rerun_tool,
            tool_registry=self.tool_registry,
            core=self.core,
            form_submit_handler=self.form_handler,
            status_text_ref=self.state_manager,
            state_manager=self.state_manager
        )
        self.chat_container, self.input_field, _, input_area, _ = builder.build_ui()
        self.message_flow_coordinator.chat_container = self.chat_container
        self.state_manager.set_input_area(input_area)
        self.state_manager.set_input_field(self.input_field)
        
    async def _handle_send_message(self):
        msg = self.input_field.value.strip()
        if not msg:
            return
        await self.message_flow_coordinator.process_user_message(
            message_text=msg,
            input_field=self.input_field,
            is_processing_ref={'value': False},
            add_message_func=self._add_message,
            show_error_func=self._show_error,
            update_status_func=self._update_status,
            core=self.core
        )

    def _add_message(self, message: ChatMessage, scroll_after: bool = True):
        self.state_manager.add_message(message)
        render_message(self.chat_container, message)
        if scroll_after:
            UIOperations.scroll_to_bottom()

    async def _show_error(self, error_message: str):
        show_error_message(self.chat_container, error_message)

    def _update_status(self, status: str, scroll_after: bool = True, scroll_to_form: bool = False):
        self.state_manager.set_status(status)
        if scroll_after:
            if scroll_to_form:
                UIOperations.scroll_form_into_view_with_retries()
            else:
                UIOperations.scroll_to_bottom()

    async def _handle_new_conversation(self):
        self.state_manager.reset_conversation()
        self.chat_container.clear()
        self.state_manager.set_input_enabled(True)
        from frontend.components.chat import render_welcome_message
        render_welcome_message(self.chat_container)

    async def load_and_show_form(self, endpoint, arguments, remaining_calls=None, container=None):
        target_container = container or self.chat_container
        async def _on_submit(request_body, endpoint=endpoint, task_schema=None, **kwargs):
            return await self.form_handler.submit_form(
                request_body, endpoint, task_schema, target_container, self.core, remaining_calls=remaining_calls, **kwargs
            )
        await load_and_show_form(target_container, self.core, endpoint, arguments, _on_submit)
        UIOperations.scroll_form_into_view_with_retries()

    async def _handle_conversation_select(self, conversation_id: str):
        from frontend.database import get_chat_history_db
        from frontend.components.chat import render_welcome_message

        self.state_manager.reset_conversation()
        self.chat_container.clear()
        self.state_manager.set_conversation_id(conversation_id)

        chat_db = get_chat_history_db()
        messages = await chat_db.get_messages(conversation_id)

        render_welcome_message(self.chat_container)

        with self.chat_container:
            separator()
            label("Conversation history").classes(
                "text-xs font-medium text-zinc-500 uppercase tracking-wide"
            )

        i = 0
        n = len(messages)
        while i < n:
            msg = messages[i]
            if i + 1 < n and _is_adjacent_job_started_then_completed(msg, messages[i + 1]):
                self.state_manager.add_message(_history_record_to_chat_message(msg))
                self.state_manager.add_message(
                    _history_record_to_chat_message(messages[i + 1])
                )
                render_merged_job_tool_results(
                    self.chat_container, msg, messages[i + 1]
                )
                i += 2
            else:
                self.state_manager.add_message(_history_record_to_chat_message(msg))
                render_persisted_history_message(self.chat_container, msg)
                i += 1

        UIOperations.scroll_to_bottom()

        # No extra status text; hide the composer so the strip is not shown greyed out.
        self.state_manager.set_status("Ready")
        self.state_manager.set_input_enabled(False, hide_completely=True)

    async def load_conversation_from_data(self, conversation_data: dict):
        """Legacy helper for loading conversation from a data dict."""
        cid = conversation_data.get('conversation_id')
        if cid:
            await self._handle_conversation_select(cid)

    async def _poll_job_status(self, job_id: str, endpoint: str, interval: float | None = None):
        """Poll for job status updates and trigger result rendering."""
        from frontend.pages.chatbot import get_job_db, show_results
        import asyncio
        if interval is None:
            interval = 2.0
        job_db = get_job_db()
        while True:
            job = await job_db.get_job_by_uid(job_id)
            if not job:
                break
            status = getattr(job, 'status', '').lower()
            if status in ('completed', 'failed', 'finished'):
                if status == 'completed' or status == 'finished':
                    response = getattr(job, 'response', None) or getattr(job, 'response_body', None)
                    await show_results(self.chat_container, response, job_id)
                break
            await asyncio.sleep(interval)

    async def _handle_rerun_tool(self, message_id: str):
        """Handle re-running a tool from a specific message."""
        from frontend.database import get_chat_history_db
        chat_db = get_chat_history_db()
        msg = await chat_db.get_tool_call_by_id(message_id)
        if msg and msg.metadata and 'endpoint' in msg.metadata:
            endpoint = msg.metadata['endpoint']
            arguments = msg.metadata.get('arguments', {})
            await self._re_run_tool(endpoint, arguments)
        else:
            UIOperations.safe_notify("Could not find tool metadata for this message.", type="warning")

    async def _re_run_tool(self, endpoint: str, arguments: dict):
        """Re-run a tool with given endpoint and arguments."""
        logger.debug("Re-running tool: %s with args: %s", endpoint, arguments)
        # Try to find input area container or fallback to chat container
        try:
            from frontend.components.chat import get_latest_input_area
            container = get_latest_input_area() or self.chat_container
        except Exception:
            container = self.chat_container
            
        await self.load_and_show_form(endpoint, arguments, container=container)


def _extract_chatbot_query_from_client() -> dict:
    """
    When NiceGUI does not inject ?load_conversation / ?rerun into the page handler,
    parse them from the Starlette request or client page URL (SPA / v3_demo).
    """
    try:
        from nicegui import context

        client = getattr(context, "client", None)
        if client:
            req = getattr(client, "request", None)
            if req is not None and hasattr(req, "query_params"):
                try:
                    qp = dict(req.query_params)
                    if qp:
                        return qp
                except Exception:
                    pass

        if not client:
            return {}
        page = getattr(client, "page", None)
        url = ""
        if page is not None:
            url = str(getattr(page, "url", None) or getattr(page, "path", None) or "")
        if not url:
            return {}
        from urllib.parse import urlparse, parse_qs

        q = parse_qs(urlparse(url).query)
        return {k: v[0] for k, v in q.items() if v}
    except Exception:
        return {}


async def handle_rerun_parameter(message_id: str) -> None:
    """Handle a ``?rerun=`` query param by re-running a tool call message."""
    from frontend.database.chat_history_db import get_chat_history_db

    chat_db = get_chat_history_db()
    msg = await chat_db.get_tool_call_by_id(message_id)
    if not msg:
        ui.notify("Tool call not found for rerun.", type="negative")
        return
    endpoint = getattr(msg, "tool_call_endpoint", None)
    arguments = getattr(msg, "tool_call_arguments", None) or {}
    if not endpoint:
        ui.notify("Tool call not found for rerun.", type="negative")
        return
    chatbot = ChatbotPage.get_instance()
    if not chatbot:
        ui.notify("Chatbot not ready to rerun tool.", type="negative")
        return
    ui.notify(f"Re-running: {endpoint}", type="info")
    await chatbot.load_and_show_form(endpoint, arguments)


@ui.page('/chatbot')
async def chatbot_page(load_conversation: Optional[str] = None, rerun: Optional[str] = None):
    from frontend.utils import ensure_user_id
    if ensure_user_id() is None:
        return
        
    from frontend.utils import apply_saved_theme
    apply_saved_theme()
    create_navbar()
    
    # Global CSS injection for compact UI
    ui.add_head_html('''
        <style>
            .q-header { min-height: 16px !important
            }
            .q-toolbar { min-height: 16px !important
            padding: 0 8px !important
            }
            .q-toolbar__title { font-size: 0.85rem !important
            min-height: unset !important
            line-height: 32px !important
            }
            .q-btn { font-size: 0.7rem !important
            padding: 2px 6px !important
            min-height: unset !important
            }
            body { font-size: 0.8rem !important
            }
        </style>
    ''')
    
    chatbot = ChatbotPage()
    await chatbot.render()

    # Merge injected params with parsed URL (SPA navigations often omit injected kwargs).
    extracted = _extract_chatbot_query_from_client()
    eff_rerun = rerun or extracted.get("rerun")
    eff_load = load_conversation or extracted.get("load_conversation")

    if eff_rerun:
        await chatbot._handle_rerun_tool(eff_rerun)
    elif eff_load:
        await chatbot._handle_conversation_select(eff_load)
    else:
        stored = get_conversation_to_load()
        if stored and stored.get("conversation_id"):
            await chatbot.load_conversation_from_data(stored)

async def create_chat_ui(config: Optional[ChatbotConfig] = None):
    chatbot = ChatbotPage(config)
    await chatbot.render()
    return chatbot

def apply_saved_theme():
    from frontend.utils import apply_saved_theme as _apply
    _apply()

