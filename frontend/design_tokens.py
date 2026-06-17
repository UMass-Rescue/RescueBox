"""
Canonical Tailwind class strings for RescueBox.

Global primary actions use UMass Maroon (#881c1c); hover is a darker
maroon (#6a1616). Quasar ``--q-primary`` is set in ``frontend/utils/ui_readability_css.py``.
"""

from __future__ import annotations


class Design:
    """Brand-aligned utility classes (NiceGUI + Quasar + Tailwind)."""

    # --- Navigation (UMass Maroon #881c1c with white text) ---
    NAV_HEADER = (
        "rb-brand-nav text-white shadow-lg shadow-black/30 sticky top-0 z-50 "
        "w-full max-w-[100vw] overflow-hidden"
    )
    NAV_LINK = (
        "text-white hover:underline px-1.5 py-0.5 sm:px-2 sm:py-0.5 rounded "
        "hover:bg-white/10 !text-sm sm:!text-base whitespace-nowrap !leading-snug font-semibold"
    )
    NAV_VERSION_MUTED = "!text-sm sm:!text-base font-medium text-slate-400 shrink-0"

    # --- Buttons (UMass Maroon #881c1c; hover #6a1616) ---
    BTN_PRIMARY = (
        "rb-brand-primary text-white px-5 py-2.5 rounded-xl "
        "font-semibold shadow-md shadow-black/20 transition-all active:scale-95"
    )
    BTN_PRIMARY_COMPACT = (
        "rb-brand-primary text-white px-4 py-2 rounded-lg "
        "font-medium shadow-sm transition-colors"
    )
    BTN_PRIMARY_TIGHT = (
        "rb-brand-primary text-white px-3 py-1 rounded text-sm transition-colors"
    )
    BTN_GHOST = (
        "text-slate-600 hover:bg-slate-100 px-4 py-2 rounded-lg transition-colors"
    )
    BTN_SECONDARY_NEUTRAL = (
        "bg-slate-100 hover:bg-slate-200 text-slate-800 px-4 py-2 rounded-lg "
        "font-medium transition-colors border border-slate-200"
    )
    BTN_DISABLED = "bg-slate-200 text-slate-400 cursor-not-allowed"
    # Browse / Cancel-style actions (UMass Maroon #881c1c)
    BTN_MEDIUM_GRAY = (
        "rb-btn-medium-gray text-white rounded-lg font-medium transition-colors"
    )

    # --- Inline links ---
    LINK = "text-[#881c1c] hover:underline"

    # --- Chat bubbles (cards) ---
    CHAT_USER_BUBBLE = (
        "bg-slate-100 text-slate-800 rounded-2xl rounded-tr-none px-4 py-3 shadow-sm "
        "ring-1 ring-slate-200 border-0"
    )
    CHAT_USER_LABEL = (
        "font-medium !text-sm sm:!text-base text-slate-600 uppercase tracking-wide"
    )
    CHAT_ASSISTANT_BUBBLE = (
        "bg-white text-slate-800 ring-1 ring-slate-200 rounded-2xl rounded-tl-none "
        "px-4 py-3 shadow-sm border-0"
    )
    CHAT_ASSISTANT_BUBBLE_WIDTH = "w-full max-w-3xl min-w-0"
    CHAT_SYSTEM_TOOL = (
        "bg-slate-50 border-l-4 border-[#881c1c] p-4 italic text-slate-600 text-sm"
    )
    CHATBOT_PLUGIN_MENU_ROW = (
        "border border-slate-200 bg-white shadow-sm hover:bg-slate-50 "
        "hover:border-[#881c1c] cursor-pointer transition-all duration-150 items-start rounded-xl"
    )

    # --- Form fields (chat / long text) ---
    INPUT_MODERN = (
        "w-full min-w-0 !text-base bg-white text-slate-800 border-none ring-1 ring-slate-200 "
        "focus:ring-2 focus:ring-[#881c1c] rounded-2xl p-4 shadow-sm transition-all"
    )
    INPUT_OUTLINED = (
        "rounded-xl border border-slate-200 bg-white text-slate-800 focus:border-[#881c1c] "
        "focus:ring-2 focus:ring-[#881c1c]/10 transition-all duration-200 resize-none shadow-sm"
    )

    # --- Tool invocation / result (chat tool cards) ---
    CARD_TOOL_CALL = (
        "p-4 my-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800"
    )
    CARD_TOOL_RESULT = (
        "p-4 my-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800"
    )
    LABEL_TOOL_CALL_TITLE = "font-semibold text-slate-800 mt-3"
    LABEL_TOOL_CALL_ARGS = "font-medium text-slate-700 mt-3"
    LABEL_TOOL_RESULT_TITLE = "font-medium text-slate-800 mt-3"
    LABEL_TOOL_RESULT_CONTENT = "text-sm text-slate-600 mt-1 whitespace-pre-wrap"

    # --- Status text ---
    STATUS_PROCESSING = "text-[#881c1c]"
    SPINNER_PROCESSING = "text-[#881c1c]"

    # --- Focused panel shell (dialogs, chat, plugin pickers) ---
    PANEL_SHELL_CARD = (
        "w-full max-w-6xl mx-auto flex flex-col flex-1 min-h-0 "
        "rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-200 p-0 overflow-hidden bg-white"
    )
    PANEL_SHELL_CHAT_CARD = (
        "w-full max-w-6xl mx-auto flex flex-col min-h-0 "
        "rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-200 p-0 overflow-hidden bg-white"
    )
    PANEL_SHELL_CARD_NARROW = (
        "w-full max-w-2xl mx-auto flex flex-col min-h-0 max-h-[85vh] "
        "rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-200 p-0 overflow-hidden bg-white"
    )
    PANEL_SHELL_CARD_MD = (
        "w-full max-w-md min-w-0 mx-auto flex flex-col "
        "rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-200 p-0 overflow-hidden bg-white"
    )
    PANEL_SHELL_CARD_WIDE = (
        "w-[95vw] max-w-[1400px] max-h-[95vh] mx-auto flex flex-col min-h-0 "
        "rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-200 p-0 overflow-hidden bg-white"
    )
    PANEL_SHELL_HEADER = "w-full bg-slate-50 p-4 border-b border-slate-200 items-center justify-between flex-none"
    PANEL_SHELL_HEADER_TITLE = "text-lg font-bold text-slate-800 tracking-tight"
    PANEL_SHELL_HEADER_ICON = "!text-[#881c1c] hover:!text-[#6a1616] transition-colors"
    PANEL_SHELL_BODY = "flex-1 min-h-0 overflow-y-auto bg-slate-50 p-6"
    PANEL_SHELL_FOOTER = (
        "w-full flex-none p-4 bg-white border-t border-slate-200 items-center gap-2"
    )

    @classmethod
    def primary_button(cls) -> str:
        """Primary action button classes."""
        return cls.BTN_PRIMARY

    @classmethod
    def nav_header_classes(cls) -> str:
        """Top navigation bar classes."""
        return cls.NAV_HEADER
