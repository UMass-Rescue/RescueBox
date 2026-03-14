import logging
from nicegui import ui
from typing import Callable

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def render_form_actions(container: ui.element, on_cancel: Callable, on_submit: Callable, compact: bool = False):
    """
    Render form action buttons (Cancel / Submit) inside the provided container.
    Returns the submit button element for tests if needed.
    """
    try:
        with container:
            if compact:
                button_row_classes = 'mt-3 gap-2'
            else:
                button_row_classes = 'mt-6 gap-2'

            with ui.row().classes(button_row_classes):
                ui.space()

                def _cancel_wrapper():
                    """
                    Wrapper around the provided on_cancel callback that first attempts
                    to delete an outer form container reference attached to this container
                    (if present). This prevents leaving an empty outer card behind.
                    """
                    logger.debug("Cancel button clicked in container=%r", container)
                    outer = getattr(container, '_outer_form_container', None)
                    def _scan_and_delete_related(start_element):
                        anc = start_element
                        while anc:
                            sel = getattr(anc, '_related_tool_selection_card', None)
                            if sel:
                                try:
                                    logger.debug("Cancel wrapper: deleting related selection card %r found on %r", sel, anc)
                                    sel.delete()
                                except Exception as e:
                                    logger.debug("Cancel wrapper: failed to delete related selection card: %s", e, exc_info=True)
                                try:
                                    delattr(anc, '_related_tool_selection_card')
                                except Exception:
                                    pass
                                return True
                            anc = getattr(anc, 'parent', None)
                        return False

                    if outer:
                        logger.debug("Cancel wrapper: found outer form container=%r", outer)
                        try:
                            # attempt to delete any related selection card attached to outer or its ancestors
                            deleted = _scan_and_delete_related(outer)
                            if not deleted:
                                deleted = _scan_and_delete_related(container) or _scan_and_delete_related(getattr(container, 'parent', None))
                            logger.debug("Cancel wrapper: related selection card deleted=%s", deleted)
                        except Exception as e:
                            logger.debug("Cancel wrapper: error while deleting related selection card: %s", e, exc_info=True)
                        logger.debug("Cancel wrapper: attempting outer.delete()")
                        try:
                            outer.delete()
                            logger.debug("Cancel wrapper: outer.delete() succeeded")
                            return
                        except Exception as e:
                            logger.debug("Cancel wrapper: outer.delete() failed: %s", e, exc_info=True)
                    # Fallback to provided cancel behavior
                    try:
                        logger.debug("Cancel wrapper: invoking on_cancel callback %r", on_cancel)
                        on_cancel()
                        logger.debug("Cancel wrapper: on_cancel completed")
                    except Exception as e:
                        logger.debug("Cancel wrapper: on_cancel raised exception: %s", e, exc_info=True)

                ui.button(
                    'Cancel',
                    on_click=_cancel_wrapper
                ).classes('bg-gray-300')

                submit_btn = ui.button(
                    '▶ Submit Job',
                    on_click=on_submit
                ).classes('bg-green-600 text-white')

            return submit_btn
    except Exception as e:
        logger.exception("Error rendering form actions: %s", e)
        # Fallback inline: create basic buttons without styling
        with container:
            ui.button('Cancel', on_click=on_cancel)
            submit_btn = ui.button('Submit', on_click=on_submit)
        return submit_btn

