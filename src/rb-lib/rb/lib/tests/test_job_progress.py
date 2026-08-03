"""Tests for file-based job progress percent."""

from rb.lib.job_progress import report_file_progress


def test_report_file_progress_four_files(tmp_path, monkeypatch):
    monkeypatch.setenv("RESCUEBOX_PROGRESS_DIR", str(tmp_path))
    job_id = "JOB_test1"
    last = 0
    for processed, expected in ((1, 25), (2, 50), (3, 75), (4, 100)):
        last = report_file_progress(job_id, processed, 4, last)
        assert last == expected


def test_report_file_progress_hundred_files(tmp_path, monkeypatch):
    monkeypatch.setenv("RESCUEBOX_PROGRESS_DIR", str(tmp_path))
    job_id = "JOB_test2"
    last = 0
    for processed in range(1, 101):
        last = report_file_progress(job_id, processed, 100, last)
    assert last == 100
