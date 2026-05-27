"""
Canonical Tailwind class strings for RescueBox.

Global primary actions use UMass Maroon (PMS 202, #881c1c, RGB 136 28 28); hover is a darker
maroon (#6a1616). Quasar ``--q-primary`` is set in ``frontend/utils/ui_readability_css.py``.
See https://www.umass.edu/brand/visual-identity/brand-colors and ``frontend/design.json``.
"""

from __future__ import annotations


class Design:
    """Brand-aligned utility classes (NiceGUI + Quasar + Tailwind)."""

    # --- Navigation (Medium Gray #505759 — background from .rb-brand-nav in ui_readability_css) ---
    NAV_HEADER = (
        "rb-brand-nav text-white shadow-lg shadow-black/30 sticky top-0 z-50 "
        "w-full max-w-[100vw] overflow-hidden"
    )
    NAV_LINK = (
        "text-white hover:underline px-1.5 py-0.5 sm:px-2 sm:py-0.5 rounded "
        "hover:bg-white/10 !text-sm sm:!text-base whitespace-nowrap !leading-snug"
    )
    NAV_VERSION_MUTED = "!text-sm sm:!text-base font-medium text-zinc-400 shrink-0"

    # --- Buttons (Maroon #881c1c; hover #6a1616 — see :root / .rb-brand-primary in ui_readability_css) ---
    BTN_PRIMARY = (
        "rb-brand-primary text-white px-5 py-2.5 rounded-xl "
        "font-semibold shadow-md shadow-black/20 transition-all active:scale-95"
    )
    BTN_PRIMARY_COMPACT = (
        "rb-brand-primary text-white px-4 py-2 rounded-lg "
        "font-medium shadow-sm transition-colors"
    )
    BTN_PRIMARY_TIGHT = (
        "rb-brand-primary text-white px-3 py-1 rounded text-sm "
        "transition-colors"
    )
    BTN_GHOST = "text-zinc-600 hover:bg-zinc-100 px-4 py-2 rounded-lg transition-colors"
    BTN_SECONDARY_NEUTRAL = (
        "bg-zinc-100 hover:bg-zinc-200 text-zinc-800 px-4 py-2 rounded-lg "
        "font-medium transition-colors border border-zinc-200"
    )
    BTN_DISABLED = "bg-zinc-300 text-zinc-500 cursor-not-allowed"
    # Browse / Cancel-style actions (UMass Medium Gray #505759 — see .rb-btn-medium-gray in ui_readability_css)
    BTN_MEDIUM_GRAY = (
        "rb-btn-medium-gray text-white rounded-lg font-medium transition-colors"
    )

    # --- Inline links ---
    LINK = "text-[#881c1c] hover:underline"

    # --- Chat bubbles (cards) ---
    # User bubble: no tinted fill — white surface + zinc ring (assistant-style, right tail)
    CHAT_USER_BUBBLE = (
        "bg-white text-zinc-900 rounded-2xl rounded-tr-none px-4 py-3 shadow-sm "
        "ring-1 ring-zinc-200 border-0"
    )
    CHAT_USER_LABEL = (
        "font-medium !text-xs sm:!text-sm text-zinc-900 uppercase tracking-wide"
    )
    CHAT_ASSISTANT_BUBBLE = (
        "bg-white text-zinc-800 ring-1 ring-zinc-200 rounded-2xl rounded-tl-none "
        "px-4 py-3 shadow-sm border-0"
    )
    # Use with CHAT_ASSISTANT_BUBBLE so assistant text, markdown, and tool-call cards share one column width.
    CHAT_ASSISTANT_BUBBLE_WIDTH = "w-full max-w-3xl min-w-0"
    CHAT_SYSTEM_TOOL = (
        "bg-zinc-50 border-l-4 border-[#505759] p-4 italic text-zinc-600 text-sm"
    )
    # Plugins mode tool list rows (/chatbot Menu) — UMass Medium Gray #505759 (not indigo)
    CHATBOT_PLUGIN_MENU_ROW = (
        "border-2 border-[#505759]/35 bg-white shadow-sm hover:bg-[#505759]/10 "
        "hover:border-[#505759] cursor-pointer transition-colors duration-150 items-start"
    )

    # --- Form fields (chat / long text) ---
    INPUT_MODERN = (
        "w-full min-w-0 !text-base bg-white border-none ring-1 ring-zinc-300 "
        "focus:ring-2 focus:ring-[#881c1c] rounded-2xl p-4 shadow-inner transition-all"
    )
    # Legacy-compatible: bordered field (jobs, forms)
    INPUT_OUTLINED = (
        "rounded-xl border-2 border-zinc-200 focus:border-[#881c1c] "
        "focus:ring-2 focus:ring-[#881c1c]/10 transition-all duration-200 resize-none shadow-sm"
    )

    # --- Tool invocation / result (chat tool cards) ---
    CARD_TOOL_CALL = "p-4 my-2 bg-zinc-50 border border-zinc-200 rounded-lg"
    CARD_TOOL_RESULT = "p-4 my-2 bg-zinc-50 border border-zinc-200 rounded-lg"
    LABEL_TOOL_CALL_TITLE = "font-semibold text-black mt-3"
    LABEL_TOOL_CALL_ARGS = "font-medium text-black mt-3"
    LABEL_TOOL_RESULT_TITLE = "font-medium text-black mt-3"
    LABEL_TOOL_RESULT_CONTENT = "text-sm text-black mt-1 whitespace-pre-wrap"

    # --- Status text ---
    STATUS_PROCESSING = "text-[#881c1c]"
    SPINNER_PROCESSING = "text-[#881c1c]"

    # --- Focused panel shell (dialogs, chat, plugin pickers) ---
    # Outer card: rounded container, soft zinc shadow, no padding (header/body/footer own regions).
    PANEL_SHELL_CARD = (
        "w-full max-w-4xl mx-auto flex flex-col flex-1 min-h-0 "
        "rounded-3xl shadow-xl shadow-zinc-200/50 border border-zinc-100 p-0 overflow-hidden"
    )
    # Chat page only: no flex-1 on the card so short threads do not leave a tall empty band
    # between messages and the input; scrolling is handled on the message column (max-h).
    PANEL_SHELL_CHAT_CARD = (
        "w-full max-w-4xl mx-auto flex flex-col min-h-0 "
        "rounded-3xl shadow-xl shadow-zinc-200/50 border border-zinc-100 p-0 overflow-hidden"
    )
    PANEL_SHELL_CARD_NARROW = (
        "w-full max-w-2xl mx-auto flex flex-col min-h-0 max-h-[85vh] "
        "rounded-3xl shadow-xl shadow-zinc-200/50 border border-zinc-100 p-0 overflow-hidden"
    )
    PANEL_SHELL_CARD_MD = (
        "w-full max-w-md min-w-0 mx-auto flex flex-col "
        "rounded-3xl shadow-xl shadow-zinc-200/50 border border-zinc-100 p-0 overflow-hidden"
    )
    PANEL_SHELL_CARD_WIDE = (
        "w-[95vw] max-w-[1400px] max-h-[95vh] mx-auto flex flex-col min-h-0 "
        "rounded-3xl shadow-xl shadow-zinc-200/50 border border-zinc-100 p-0 overflow-hidden"
    )
    PANEL_SHELL_HEADER = (
        "w-full bg-zinc-50 p-4 border-b border-zinc-100 items-center justify-between flex-none"
    )
    PANEL_SHELL_HEADER_TITLE = "text-lg font-bold text-zinc-900 tracking-tight"
    # Icon-only close on dialogs (Medium Gray #505759; hover matches .rb-btn-medium-gray hover)
    PANEL_SHELL_HEADER_ICON = "!text-[#505759] hover:!text-[#3d4442] transition-colors"
    PANEL_SHELL_BODY = "flex-1 min-h-0 overflow-y-auto bg-white p-6"
    PANEL_SHELL_FOOTER = (
        "w-full flex-none p-4 bg-white border-t border-zinc-100 items-center gap-2"
    )
