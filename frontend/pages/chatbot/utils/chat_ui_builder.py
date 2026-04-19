"""
Chat UI Builder.

Builds the complete chat UI with proper separation of concerns.
"""

import logging
from nicegui import ui

from frontend.pages.chatbot.utils.ui_operations import UIOperations
from frontend.pages.chatbot.utils.ui_styling import UIStyling
from frontend.pages.chatbot.utils.ui_mode_manager import UIModeManager
from frontend.components.chat import create_history_panel
from frontend.design_tokens import Design
from frontend.pages.chatbot.chatbot_forms import show_tool_picker, load_and_show_form
from frontend.components.chat.input_area import create_input_area

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Single reference for the chat header History button (one client / builder instance at a time per page)
_chat_history_button_ref = None


def register_chat_history_button(btn) -> None:
    """Remember the History button so we can show it after the first job is created."""
    global _chat_history_button_ref
    if btn is None:
        return
    _chat_history_button_ref = btn


def refresh_chat_history_button_visibility() -> None:
    """Show the History button only when the current user has at least one job."""
    global _chat_history_button_ref
    btn = _chat_history_button_ref
    if btn is None:
        return
    try:
        from frontend.components.chat.chat_header import user_has_job_history

        btn.visible = user_has_job_history()
    except Exception:
        pass


class ChatUIBuilder:
    """Builds the complete chat UI with proper separation of concerns."""

    def __init__(self, on_send, on_new_conversation, tool_registry, core, form_submit_handler, status_text_ref=None, state_manager=None):
        """
        Initialize chat UI builder.

        Args:
            on_send: Callback for send button/action
            on_new_conversation: Callback for new conversation button
            tool_registry: Tool registry for direct tool picker access
            core: Chatbot core for form loading
            form_submit_handler: Form submit handler
            status_text_ref: Reactive state reference for status text
            state_manager: ChatbotStateManager for clearing messages when switching modes
        """
        self.on_send = on_send
        self.on_new_conversation = on_new_conversation
        self.tool_registry = tool_registry
        self.core = core
        self.form_submit_handler = form_submit_handler
        self.status_text_ref = status_text_ref
        self.state_manager = state_manager

        # Initialize UI components
        self.mode_indicator = None
        self.models_btn = None
        self.analyze_btn = None
        self.mode_manager = None
        self.input_field = None  # Store the actual input field

        self.logger = logging.getLogger(__name__)

    def build_ui(self):
        """
        Build and return the complete chat UI.

        Returns:
            tuple: (chat_container, input_field, status_label, input_area, below_input_area)
        """
        self.logger.info("Building chat UI with proper separation")

        # Create UI state management
        ui_state = self._create_ui_state()

        # Build main container
        with ui.column().classes('min-h-screen w-full flex flex-col -mt-16 bg-zinc-50'):
            # Sticky toolbar (Menu / Chat / History only; title is on the card below).
            self._build_header(ui_state)

            # Centered chat card: header strip + scrollable messages + input (matches product shell).
            with ui.column().classes(
                'container mx-auto w-full px-4 flex-1 flex flex-col min-h-0 pb-4'
            ):
                with ui.card().classes(Design.PANEL_SHELL_CHAT_CARD):
                    with ui.row().classes(Design.PANEL_SHELL_HEADER):
                        ui.label('RescueBox Assistant').classes(Design.PANEL_SHELL_HEADER_TITLE)
                        self.mode_indicator = ui.badge('Chat mode', color=None).classes(
                            'text-xs font-medium rb-chat-mode-badge'
                        )

                    chat_container = self._build_chat_area()

                    # Below the message list, above the composer (still only while is_processing).
                    if self.state_manager is not None:
                        with ui.row().classes(
                            'rb-chat-processing-hint w-full items-center gap-2 px-6 py-2 '
                            'border-t border-zinc-100 bg-zinc-50 flex-none'
                        ) as processing_hint:
                            ui.spinner(size='1rem').classes(
                                f'{Design.SPINNER_PROCESSING} shrink-0'
                            )
                            ui.label('Processing…').classes('!text-sm text-zinc-600')
                        self.state_manager.attach_processing_strip(processing_hint)

                    input_area = self._build_input_area()

                # Outside the card: wide job results / re-run output below the composer strip.
                below_input_area = ui.column().classes(
                    'rb-chat-below-input-area w-full max-w-none space-y-4 mt-2 mb-4'
                )

            # Initialize mode manager now that chat_container exists
            from frontend.components.chat.chat_window import render_welcome_message
            self.mode_manager = UIModeManager(
                mode_indicator=self.mode_indicator,
                models_btn=self.models_btn,
                analyze_btn=self.analyze_btn,
                chat_container=chat_container,
                status_text_ref=self.status_text_ref,
                form_submit_handler=self.form_submit_handler,
                core=self.core,
                state_manager=self.state_manager,
                show_welcome_callback=render_welcome_message
            )

            # Setup mode handlers
            self._setup_mode_handlers(ui_state, chat_container, input_area)

        return chat_container, self.input_field, self.status_text_ref, input_area, below_input_area

    def _create_ui_state(self):
        """Create initial UI state."""
        return {
            'current_mode': 'assistant',  # Default to Assistant mode
            'chat_visible': True,        # Chat always visible for context
            'input_visible': True        # Input visible in Assistant mode only
        }

    def _build_header(self, ui_state):
        """Build the toolbar header."""
        try:
            from frontend.components.chat.chat_header import create_chat_header
            models_btn, analyze_btn, history_btn = create_chat_header(
                self.on_new_conversation, ui_state, UIStyling, on_show_history=self._show_history_dialog
            )
            # mode_indicator is created on the chat card in build_ui()
            self.models_btn = models_btn
            self.analyze_btn = analyze_btn
            self.history_btn = history_btn
            register_chat_history_button(history_btn)
            ui.timer(0.35, refresh_chat_history_button_visibility, once=True)
            ui.timer(1.5, refresh_chat_history_button_visibility, once=True)
            self.ui_state = ui_state
        except Exception as e:
            logger.exception("Failed to create chat header component: %s", e)

    def _build_chat_area(self):
        """Build the main chat container using a reusable ChatWindow component."""
        from frontend.components.chat.chat_window import create_chat_window
        chat_container = create_chat_window()
        self.chat_container = chat_container
        return chat_container

    def _build_input_area(self):
        """Build the input area with controls using reusable component."""
        input_area = create_input_area(self.status_text_ref, self.on_send)
        # Expose the actual textarea for callers/tests
        self.input_field = getattr(input_area, 'input_field', None)
        return input_area

    def _setup_mode_handlers(self, ui_state, chat_container, input_area):
        """Setup mode switching logic."""
        async def switch_mode(mode: str):
            """Switch between different UI modes."""
            ui_state['current_mode'] = mode
            await self.mode_manager.switch_mode(mode, input_area)

        # Define button click handlers
        async def handle_models_click():
            await switch_mode('models')
            # Diagnostic log: record which containers will be used to render the picker/form
            try:
                logger.info("handle_models_click invoked: chat_container=%r input_area=%r global_chat=%r",
                            chat_container, input_area, getattr(self, 'chat_container', None))
            except Exception:
                pass
            # Directly show tool picker instead of going through command processing
            # Create a tool selected handler that directly loads the form
            async def on_tool_selected(endpoint, args):
                # Directly load the form for the selected tool
                # Create a callable for form submission
                async def handle_form_submit(request_body, form_endpoint, task_schema):
                    # Get current conversation_id from state manager
                    conversation_id = getattr(self.status_text_ref, 'conversation_id', None) if self.status_text_ref else None
                    return await self.form_submit_handler.submit_form(
                        request_body, form_endpoint, task_schema,
                        chat_container, self.core, conversation_id=conversation_id
                    )
                # Render forms into the chat container so the selection message and form
                # appear inline in the conversation (after assistant/tool-selection).
                try:
                    logger.info("ChatUIBuilder loading form: target_chat_container=%r endpoint=%s args=%s", chat_container, endpoint, args)
                except Exception:
                    pass
                def _on_cancel():
                    if self.state_manager:
                        self.state_manager.set_input_enabled(True)

                await load_and_show_form(
                    chat_container, self.core, endpoint, args or {},
                    handle_form_submit, on_form_cancel=_on_cancel
                )
                # Scroll form into view instead of page bottom
                UIOperations.scroll_form_into_view()

            await show_tool_picker(chat_container, self.tool_registry, on_tool_selected)

        async def handle_analyze_click():
            await switch_mode('assistant')

        # Bind button handlers
        self.models_btn.on_click(handle_models_click)
        self.analyze_btn.on_click(handle_analyze_click)

    def _show_history_dialog(self):
        """Show chat history dialog."""
        try:
            from frontend.components.chat.history_dialog import show_history_dialog

            def _on_conv_select(conv_id):
                self._load_conversation(conv_id)

            def _on_rerun(msg_id):
                ui.navigate.to(f'/chatbot?rerun={msg_id}')

            show_history_dialog(on_conversation_select=_on_conv_select, on_rerun_tool=_on_rerun)
        except Exception as e:
            logger.exception("Failed to open history dialog component: %s", e)
            # Fallback to inline dialog (same shell as history_dialog module)
            with ui.dialog() as dialog, ui.card().classes(Design.PANEL_SHELL_CARD_NARROW):
                with ui.row().classes(Design.PANEL_SHELL_HEADER):
                    ui.label('Chat History').classes(Design.PANEL_SHELL_HEADER_TITLE)
                with ui.column().classes(f'{Design.PANEL_SHELL_BODY} flex flex-col min-h-0 max-h-[60vh]'):
                    create_history_panel(
                        on_conversation_select=lambda conv_id: [
                            self._load_conversation(conv_id),
                            dialog.close(),
                        ],
                        on_rerun_tool=lambda msg_id: [
                            ui.navigate.to(f'/chatbot?rerun={msg_id}'),
                            dialog.close(),
                        ],
                        show_title=False,
                    )
            dialog.open()

    def _load_conversation(self, conversation_id: str):
        """Load conversation into chat (placeholder)."""
        UIOperations.safe_notify(f'Conversation loading - to be implemented for ID: {conversation_id}', type='info')
