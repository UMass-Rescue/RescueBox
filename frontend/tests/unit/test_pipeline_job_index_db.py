"""Tests for per-pipeline SQLite index (image ↔ summary text path)."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from frontend.database.pipeline_job_index_db import (
    index_db_path,
    insert_chunks,
    insert_pipeline_io_links,
    insert_pipeline_job_step,
    insert_pipeline_response_rows,
    list_pipeline_job_steps,
    list_pipeline_response_rows,
    lookup_input_for_output,
    lookup_metadata_for_output,
    lookup_source_image,
)


class TestPipelineJobIndexDb(unittest.TestCase):
    def test_insert_and_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "idx.sqlite"
            with patch(
                "frontend.database.pipeline_job_index_db.index_db_path",
                return_value=db_file,
            ):
                uid = "user1"
                root = "job-abc-123"
                tp = "/tmp/out/kid.jpg.txt"
                img = "/tmp/in/kid.jpg"
                insert_chunks(
                    uid,
                    root,
                    [
                        {
                            "text_path": tp,
                            "source_image_path": img,
                            "text_excerpt": "hello",
                            "provenance": {"endpoint": "image_summary/x"},
                        }
                    ],
                )
                found = lookup_source_image(uid, root, tp)
                self.assertEqual(found, img)
                self.assertEqual(lookup_input_for_output(uid, root, tp), img)

    def test_insert_pipeline_io_links_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "idx2.sqlite"
            with patch(
                "frontend.database.pipeline_job_index_db.index_db_path",
                return_value=db_file,
            ):
                uid = "u2"
                root = "job-xyz"
                insert_pipeline_io_links(
                    uid,
                    root,
                    [
                        {
                            "input_path": "/in/photo.jpg",
                            "output_path": "/out/row1.json",
                            "metadata": {
                                "age": "(25-32)",
                                "gender": "Female",
                                "box": [1, 2, 3, 4],
                            },
                        }
                    ],
                )
                self.assertEqual(
                    lookup_input_for_output(uid, root, "/out/row1.json"),
                    "/in/photo.jpg",
                )
                meta = lookup_metadata_for_output(uid, root, "/out/row1.json")
                self.assertEqual(meta.get("gender"), "Female")

    def test_index_path_contains_user_and_job(self):
        p = index_db_path("u1", "jid")
        self.assertIn("pipeline_index", str(p))
        self.assertTrue(str(p).endswith(".sqlite"))

    def test_insert_pipeline_job_step_and_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "steps.sqlite"
            with patch(
                "frontend.database.pipeline_job_index_db.index_db_path",
                return_value=db_file,
            ):
                insert_pipeline_job_step(
                    "u1",
                    "root-a",
                    "child-1",
                    "plugin/task",
                    {"response": {"output_type": "text", "text_value_chars": 10}},
                )
                rows = list_pipeline_job_steps("u1", "root-a")
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["step_job_id"], "child-1")
                self.assertEqual(rows[0]["endpoint"], "plugin/task")
                self.assertEqual(rows[0]["detail"]["response"]["output_type"], "text")

    def test_insert_pipeline_response_rows_per_container_ordinals(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "prr.sqlite"
            with patch(
                "frontend.database.pipeline_job_index_db.index_db_path",
                return_value=db_file,
            ):
                insert_pipeline_response_rows(
                    "u1",
                    "root-b",
                    "step-a",
                    "plugin/task",
                    [
                        {"container": "A", "output_type": "x", "payload": {"n": 1}},
                        {"container": "B", "output_type": "x", "payload": {"n": 2}},
                        {"container": "A", "output_type": "x", "payload": {"n": 3}},
                    ],
                )
                rows = list_pipeline_response_rows("u1", "root-b", "step-a")
                self.assertEqual(len(rows), 3)
                a_rows = [r for r in rows if r["container"] == "A"]
                self.assertEqual([r["ordinal"] for r in a_rows], [0, 1])
                self.assertEqual(a_rows[0]["payload"]["n"], 1)
                self.assertEqual(a_rows[1]["payload"]["n"], 3)

    def test_list_pipeline_response_rows_without_step_filter_lists_all_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "prr2.sqlite"
            with patch(
                "frontend.database.pipeline_job_index_db.index_db_path",
                return_value=db_file,
            ):
                insert_pipeline_response_rows(
                    "u",
                    "r",
                    "s1",
                    "a/x",
                    [{"container": "c", "output_type": "t", "payload": {}}],
                )
                insert_pipeline_response_rows(
                    "u",
                    "r",
                    "s2",
                    "b/y",
                    [{"container": "c", "output_type": "t", "payload": {"k": 1}}],
                )
                all_rows = list_pipeline_response_rows("u", "r")
                self.assertEqual(len(all_rows), 2)
                steps = {r["step_job_id"] for r in all_rows}
                self.assertEqual(steps, {"s1", "s2"})


if __name__ == "__main__":
    unittest.main()
