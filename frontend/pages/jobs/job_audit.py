"""
Job Audit Trail Export Component

This module provides UI components for exporting job audit trails.
"""

import logging
from datetime import datetime
from nicegui import ui
from frontend.utils.audit_trail import (
    generate_audit_trail_for_job,
    export_audit_trail
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def create_audit_trail_button(job_id: str):
    """
    Create a button to export audit trail for a job.
    
    Args:
        job_id (str): Job unique identifier
    
    Returns:
        ui.button: Button component
    
    Tips:
    - Button triggers audit trail generation and download
    - Shows notification during generation
    - Downloads markdown file with all job information
    """
    logger.debug("Creating audit trail export button for job: %s", job_id)
    
    async def export_audit():
        """Handle audit trail export"""
        try:
            logger.info("Exporting audit trail for job: %s", job_id)
            ui.notify('Generating audit trail...', type='info')
            
            # Generate audit trail
            audit_trail = await generate_audit_trail_for_job(job_id)
            
            if 'error' in audit_trail:
                ui.notify(f"Error: {audit_trail['error']}", type='negative')
                return
            
            # Export as markdown
            markdown_content = await export_audit_trail(audit_trail, format_type='markdown')
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"audit_trail_job_{job_id[:8]}_{timestamp}.md"
            
            # Download file using NiceGUI
            ui.download(markdown_content.encode('utf-8'), filename=filename)
            
            ui.notify(f'Audit trail exported: {filename}', type='positive')
            logger.info("Audit trail exported successfully: %s", filename)
        except Exception as e:
            logger.error("Error exporting audit trail: %s", e, exc_info=True)
            ui.notify(f'Error exporting audit trail: {str(e)}', type='negative')
    
    button = ui.button(
        '📋 Export Audit Trail',
        on_click=export_audit
    ).classes('bg-purple-600 text-white')
    
    return button
