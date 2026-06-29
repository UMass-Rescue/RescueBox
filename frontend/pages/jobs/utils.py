"""Re-export job helpers from ``frontend.database.job_field_utils`` for page callers."""

from frontend.database import job_field_utils as _job_field_utils

compute_job_results_title = _job_field_utils.compute_job_results_title
extract_job_fields = _job_field_utils.extract_job_fields
get_plugin_name = _job_field_utils.get_plugin_name
partition_jobs_by_pipeline = _job_field_utils.partition_jobs_by_pipeline
pipeline_group_root_id = _job_field_utils.pipeline_group_root_id

del _job_field_utils
