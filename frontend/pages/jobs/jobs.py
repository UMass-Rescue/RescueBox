"""
Jobs Page

This module provides the JobsPage class for displaying and managing job history,
including job details, cancellation, and deletion.
"""

import logging
from nicegui import ui
from typing import List, Dict
from frontend.chatbot.config import ToolRegistry
from frontend.components.shared import create_navbar
from frontend.components.jobs import render_job_row
from frontend.pages.jobs.job_utils import extract_job_fields, get_plugin_name
from frontend.pages.jobs.pipeline_job_grouping import (
    partition_jobs_by_pipeline,
    pipeline_group_root_id,
)
from frontend.database import JobRecord, JobStatus
from frontend.api_client import api_client
from frontend.constants import UI_TITLES, UI_BUTTONS, SUCCESS_MESSAGES, ERROR_MESSAGES
from frontend.utils.error_handling import handle_api_error, show_error_to_user, show_success_to_user

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class JobsPage:
    """
    Jobs listing page.
    
    Displays all jobs in a table format with status, timestamps, and actions
    (view, cancel, delete). Jobs are sorted by start time (newest first).
    
    Usage:
        page = JobsPage()
        await page.render()
    
    Tips:
    - Jobs are automatically loaded on page render
    - Jobs are sorted by start time (newest first)
    - Cancel action only available for running jobs
    - Delete action only available for completed/failed jobs
    """
    
    def __init__(self):
        """
        Initialize JobsPage.
        
        Sets up API client and initializes empty jobs list.
        """
        #logger.info("Initializing JobsPage")
        self.api_client = api_client
        self.jobs: List[JobRecord] = []
        logger.debug("JobsPage initialized successfully")
    
    async def render(self):
        """
        Render the jobs page UI.
        
        Creates the page layout with header, refresh button, and jobs table.
        Automatically loads jobs on render.
        
        Returns:
            None: UI is added directly to the current context
        """
        #logger.info("Rendering jobs page")
        with ui.column().classes('container mx-auto p-8'):
            with ui.row().classes('items-center justify-between mb-6'):
                ui.label(UI_TITLES['jobs']).classes('text-4xl font-bold')
            
            # Jobs table
            #logger.debug("Creating jobs container")
            self.jobs_container = ui.column().classes('space-y-2 w-full')
            await self.load_jobs()
    
    async def load_jobs(self):
        """
        Load jobs from the local SQLite database.
        
        Fetches the list of jobs from the database (jobs are already sorted by
        start time, newest first). Updates internal state and triggers UI refresh.
        
        Returns:
            None
        
        Tips:
        - Jobs are loaded from local SQLite database
        - Jobs are already sorted by startTime descending (newest first)
        - UI is automatically refreshed after loading
        """
        #logger.info("Loading jobs from database")
        try:
            from frontend.database import get_job_db
            job_db = get_job_db()
            jobs_data = await job_db.get_all_jobs()
            #logger.info("Loaded %d jobs from database", len(jobs_data))
            # Ensure newest first (by startTime descending)
            self.jobs = sorted(
                jobs_data,
                key=lambda j: j.get('startTime') or '',
                reverse=True
            )
            #logger.debug("Jobs sorted by start time (newest first)")
            await self.render_jobs()
            #logger.info("Jobs loaded and rendered successfully")
        except Exception as e:
            await handle_api_error(e, "Error loading jobs", user_message=ERROR_MESSAGES['load_jobs'])
    
    async def render_jobs(self):
        """
        Render job rows in the table.
        
        Clears the container and renders table header and job rows with
        appropriate action buttons based on job status.
        
        Returns:
            None
        
        Tips:
        - Table header is fixed at the top
        - Each job row includes model name, timestamps, status, and actions
        - Model names are fetched asynchronously for each job
        - Action buttons vary based on job status
        """
        #logger.info("Rendering jobs in table")
        self.jobs_container.clear()
        
        with self.jobs_container:
            # Table header
            #logger.debug("Creating table header")
            with ui.row().classes(
                'bg-[#505759] border-b border-[#3d4442] p-4 font-semibold text-white '
                'w-full flex-nowrap'
            ):
                ui.label('Job ID').classes('w-40 shrink-0')
                ui.label('Plugin').classes('flex-1 min-w-0')
                ui.label('Time').classes('w-64 shrink-0')
                ui.label('Status').classes('w-32 shrink-0')
                ui.label('Actions').classes('w-48 shrink-0')
        
            # Job rows (group multi-step pipelines under one heading)
            groups = partition_jobs_by_pipeline(self.jobs)
            for group in groups:
                if len(group) > 1:
                    root_id = pipeline_group_root_id(group)
                    with ui.row().classes(
                        'w-full items-center gap-2 py-2 px-3 mb-1 rounded-md '
                        'bg-[#505759] border border-[#3d4442] text-sm text-white'
                    ):
                        ui.label('Pipeline').classes('font-semibold shrink-0')
                        ui.link(
                            root_id,
                            f'/jobs/{root_id}',
                        ).classes('font-mono text-xs text-white/90 hover:underline shrink-0').tooltip(
                            f'{len(group)} steps — open root job'
                        )
                        ui.label(f'({len(group)} steps)').classes('text-xs text-white/75 shrink-0')
                    group_wrap = ui.column().classes(
                        'w-full border-l-2 border-[#505759]/50 pl-3 mb-3 space-y-0'
                    )
                else:
                    group_wrap = self.jobs_container

                for job in group:
                    job_fields = extract_job_fields(job)
                    job_uid = job_fields['uid']

                    plugin_name = await get_plugin_name(self.api_client, job_fields['modelUid'])
                    if not plugin_name and job_fields['endpoint']:
                        plugin_name = ToolRegistry.display_name_for_endpoint(
                            job_fields['endpoint']
                        )

                    render_job_row(
                        group_wrap,
                        job,
                        plugin_name=plugin_name or 'Unknown',
                        on_view=lambda uid=job_uid: ui.navigate.to(f"/jobs/{uid}"),
                        on_cancel=self.cancel_job,
                        on_delete=self.delete_job,
                    )
    
    async def cancel_job(self, job_id: str):
        """
        Cancel a running job.
        
        Updates job status in database to 'Canceled' and refreshes the jobs list.
        
        Args:
            job_id (str): Job unique identifier
        
        Returns:
            None
        
        Tips:
        - Only works for jobs with status 'Running'
        - Updates job status in local database
        - Jobs list is automatically refreshed after cancellation
        - User notification shown on success/failure
        """
        logger.info("Canceling job: %s", job_id)
        try:
            from frontend.database import get_job_db, JobStatus
            job_db = get_job_db()
            await job_db.update_job_status(
                job_id,
                JobStatus.CANCELED,
                status_text='Job canceled by user'
            )
            logger.info("Job %s canceled successfully", job_id)
            show_success_to_user(SUCCESS_MESSAGES['job_canceled'])
            await self.load_jobs()
        except Exception as e:
            await handle_api_error(e, f"Error canceling job {job_id}", user_message=ERROR_MESSAGES['cancel_job'])
    
    async def delete_job(self, job_id: str):
        """
        Delete a job from the database.
        
        Removes job record from local database and refreshes the jobs list.
        
        Args:
            job_id (str): Job unique identifier
        
        Returns:
            None
        
        Tips:
        - Deletes job from local SQLite database
        - Jobs list is automatically refreshed after deletion
        - User notification shown on success/failure
        """
        logger.info("Deleting job: %s", job_id)
        try:
            from frontend.database import get_job_db
            job_db = get_job_db()
            success = await job_db.delete_job(job_id)
            if success:
                logger.info("Job %s deleted successfully", job_id)
                show_success_to_user(SUCCESS_MESSAGES['job_deleted'])
            else:
                logger.warning("Job %s not found for deletion", job_id)
                show_error_to_user('Job not found', type='warning')
            await self.load_jobs()
        except Exception as e:
            await handle_api_error(e, f"Error deleting job {job_id}", user_message=ERROR_MESSAGES['delete_job'])

@ui.page('/jobs')
async def jobs_page():
    """
    Page route handler for /jobs.
    
    Creates the jobs page with navigation bar and renders the JobsPage.
    
    Returns:
        None: Page is rendered directly
    """
    #logger.info("Jobs page route accessed")
    from frontend.utils.nicegui_storage import ensure_user_id
    if ensure_user_id() is None:
        return
    from frontend.utils.theme import apply_saved_theme
    apply_saved_theme()
    create_navbar()
    jobs_page_instance = JobsPage()
    await jobs_page_instance.render()
    #logger.debug("Jobs page route completed")