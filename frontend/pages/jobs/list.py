import logging
from nicegui import ui
from typing import List, Dict
from frontend.chatbot.config import ToolRegistry
from frontend.components.shared import create_navbar
from frontend.components.jobs import render_job_row
from frontend.database import get_job_db, JobStatus
from frontend.api_client import api_client
from frontend.constants import UI_TITLES, SUCCESS_MESSAGES, ERROR_MESSAGES
from frontend.utils import handle_api_error, show_success_to_user, show_error_to_user, ensure_user_id, apply_saved_theme
from .utils import (
    partition_jobs_by_pipeline, pipeline_group_root_id, 
    extract_job_fields, get_plugin_name
)

logger = logging.getLogger(__name__)

class JobsPage:
    def __init__(self):
        self.api_client = api_client
        self.jobs = []
    
    async def render(self):
        with ui.column().classes('container mx-auto p-8'):
            with ui.row().classes('items-center justify-between mb-6'):
                ui.label(UI_TITLES['jobs']).classes('text-4xl font-bold')
            self.jobs_container = ui.column().classes('space-y-2 w-full')
            await self.load_jobs()
    
    async def load_jobs(self):
        try:
            job_db = get_job_db()
            jobs_data = await job_db.get_all_jobs()
            self.jobs = sorted(jobs_data, key=lambda j: j.get('startTime') or '', reverse=True)
            await self.render_jobs()
        except Exception as e:
            await handle_api_error(e, "Error loading jobs")
    
    async def render_jobs(self):
        self.jobs_container.clear()
        with self.jobs_container:
            with ui.row().classes('bg-[#505759] border-b border-[#3d4442] p-4 font-semibold text-white w-full'):
                ui.label('Job ID').classes('w-40 shrink-0')
                ui.label('Plugin').classes('flex-1 min-w-0')
                ui.label('Time').classes('w-64 shrink-0')
                ui.label('Status').classes('w-32 shrink-0')
                ui.label('Actions').classes('w-48 shrink-0')
        
            groups = partition_jobs_by_pipeline(self.jobs)
            for group in groups:
                if len(group) > 1:
                    root_id = pipeline_group_root_id(group)
                    with ui.row().classes('w-full items-center gap-2 py-2 px-3 mb-1 rounded-md bg-[#505759] text-white'):
                        ui.label('Pipeline').classes('font-semibold')
                        ui.link(root_id, f'/jobs/{root_id}').classes('text-white/90 hover:underline')
                    group_wrap = ui.column().classes('w-full border-l-2 border-[#505759]/50 pl-3 mb-3')
                else:
                    group_wrap = self.jobs_container

                for job in group:
                    jf = extract_job_fields(job)
                    pname = await get_plugin_name(self.api_client, jf['modelUid']) or ToolRegistry.display_name_for_endpoint(jf['endpoint'])
                    render_job_row(group_wrap, job, plugin_name=pname or 'Unknown', 
                                   on_view=lambda uid=jf['uid']: ui.navigate.to(f"/jobs/{uid}"),
                                   on_cancel=self.cancel_job, on_delete=self.delete_job)
    
    async def cancel_job(self, job_id: str):
        try:
            await get_job_db().update_job_status(job_id, JobStatus.CANCELED, status_text='Job canceled by user')
            show_success_to_user(SUCCESS_MESSAGES['job_canceled'])
            await self.load_jobs()
        except Exception as e:
            await handle_api_error(e, f"Error canceling job {job_id}")

    async def delete_job(self, job_id: str):
        try:
            if await get_job_db().delete_job(job_id):
                show_success_to_user(SUCCESS_MESSAGES['job_deleted'])
            else:
                show_error_to_user('Job not found')
            await self.load_jobs()
        except Exception as e:
            await handle_api_error(e, f"Error deleting job {job_id}")

@ui.page('/jobs')
async def jobs_page_route():
    if ensure_user_id() is None: return
    apply_saved_theme()
    create_navbar()
    await JobsPage().render()
