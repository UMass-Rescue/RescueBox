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
from frontend.pages.chatbot.chatbot_forms import show_tool_picker, load_and_show_form
from frontend.components.chat.input_area import create_input_area

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
            tuple: (chat_container, input_field, status_label)
        """
        self.logger.info("Building chat UI with proper separation")

        # Create UI state management
        ui_state = self._create_ui_state()

        # Build main container
        with ui.column().classes('min-h-screen w-full flex flex-col -mt-16 bg-gray-50'):
            # Build header
            # Pass history dialog handler so the header can open it when available
            self._build_header(ui_state)

            # Build main content areas inside a centered container so children align
            with ui.column().classes('container mx-auto w-full px-4'):
                chat_container = self._build_chat_area()
                input_area = self._build_input_area()

            # Initialize mode manager now that chat_container exists
            self.mode_manager = UIModeManager(
                mode_indicator=self.mode_indicator,
                models_btn=self.models_btn,
                analyze_btn=self.analyze_btn,
                chat_container=chat_container,
                status_text_ref=self.status_text_ref,
                form_submit_handler=self.form_submit_handler,
                core=self.core,
                state_manager=self.state_manager
            )

            # Setup mode handlers
            self._setup_mode_handlers(ui_state, chat_container, input_area)

        return chat_container, self.input_field, self.status_text_ref

    def _create_ui_state(self):
        """Create initial UI state."""
        return {
            'current_mode': 'analyze',  # Default to analyze mode
            'chat_visible': True,       # Chat always visible for context
            'input_visible': True       # Input visible in analyze mode only
        }

    def _build_header(self, ui_state):
        """Build the toolbar header."""
        try:
            from frontend.components.chat.chat_header import create_chat_header
            mode_indicator, models_btn, analyze_btn = create_chat_header(
                self.on_new_conversation, ui_state, UIStyling, on_show_history=self._show_history_dialog
            )
            # Store references for mode switching
            self.mode_indicator = mode_indicator
            self.models_btn = models_btn
            self.analyze_btn = analyze_btn
            self.ui_state = ui_state
        except Exception as e:
            logger.exception("Failed to create chat header component: %s", e)
            # Fallback to inline header
            with ui.row().classes('bg-white border-b shadow-sm items-center justify-between w-full px-4 py-3 sticky top-0 z-10'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('smart_toy', size='1.5rem').classes('text-blue-600')
                    ui.label('🤖 Assistant').classes('text-lg font-semibold text-gray-800 mr-2')
                    ui.label('RescueBox Assistant').classes('text-sm text-gray-600')
                    mode_indicator = ui.badge('Analyze', color='green').classes('text-xs')
                with ui.row().classes('items-center gap-3'):
                    models_btn = ui.button('📋 Models').classes(UIStyling.BUTTON_ENABLED)
                    analyze_btn = ui.button('🧠 Analyze').classes(UIStyling.BUTTON_ENABLED)
                    ui.button('📜 History', on_click=self._show_history_dialog).classes(UIStyling.BUTTON_ENABLED)
                    ui.button('New Conversation', on_click=self.on_new_conversation).classes(UIStyling.BUTTON_ENABLED)
            self.mode_indicator = mode_indicator
            self.models_btn = models_btn
            self.analyze_btn = analyze_btn
            self.ui_state = ui_state

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
                    await self.form_submit_handler.submit_form(
                        request_body, form_endpoint, task_schema,
                        chat_container, self.core, conversation_id=conversation_id
                    )
                # Render forms into the chat container so the selection message and form
                # appear inline in the conversation (after assistant/tool-selection).
                try:
                    logger.info("ChatUIBuilder loading form: target_chat_container=%r endpoint=%s args=%s", chat_container, endpoint, args)
                except Exception:
                    pass
                await load_and_show_form(chat_container, self.core, endpoint, args or {}, handle_form_submit)
                # Scroll to bottom to show the loaded form
                UIOperations.scroll_to_bottom()

            await show_tool_picker(chat_container, self.tool_registry, on_tool_selected)

        async def handle_analyze_click():
            await switch_mode('analyze')

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
            # Fallback to inline dialog
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl max-h-[80vh]'):
                ui.label('Chat History').classes('text-2xl font-bold mb-4')
                history_panel = create_history_panel(
                    on_conversation_select=lambda conv_id: [self._load_conversation(conv_id), dialog.close()],
                    on_rerun_tool=lambda msg_id: [ui.navigate.to(f'/chatbot?rerun={msg_id}'), dialog.close()]
                )
            dialog.open()

    def _load_conversation(self, conversation_id: str):
        """Load conversation into chat (placeholder)."""
        UIOperations.safe_notify(f'Conversation loading - to be implemented for ID: {conversation_id}', type='info')
