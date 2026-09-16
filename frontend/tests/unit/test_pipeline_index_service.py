"""Tests for pipeline index ingestion from image_summary payloads (file_pairs)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from frontend.database.pipeline_index_service import (
    flatten_job_response_to_rows,
    record_image_summary_for_pipeline,
    record_pipeline_job_completion,
)
from frontend.database.pipeline_job_index_db import (
    list_pipeline_job_steps,
    list_pipeline_response_rows,
    lookup_input_for_output,
    lookup_source_image,
)


def _text_response_dict(payload: dict) -> dict:
    return {"root": {"output_type": "text", "value": json.dumps(payload)}}


class TestFlattenJobResponseToRows(unittest.TestCase):
    """Unit tests for flattening API responses into per-row persist payloads."""

    def test_text_top_level_json_array_one_row_per_element(self):
        body = {"root": {"output_type": "text", "value": "[1, 2, 3]"}}
        rows = flatten_job_response_to_rows(body, "ep")
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r["container"] == "text.json[]" for r in rows))
        self.assertEqual([r["payload"] for r in rows], [1, 2, 3])

    def test_text_json_object_lists_and_remainder(self):
        payload = {
            "file_pairs": [{"input_path": "/in/x", "output_path": "/out/x"}],
            "run_id": "abc",
        }
        body = _text_response_dict(payload)
        rows = flatten_job_response_to_rows(body, "ep")
        containers = {r["container"] for r in rows}
        self.assertIn("text.json.file_pairs", containers)
        self.assertIn("text.json.remainder", containers)
        rem = [r for r in rows if r["container"] == "text.json.remainder"][0]
        self.assertEqual(rem["payload"].get("run_id"), "abc")

    def test_text_non_json_value_uses_text_raw_container(self):
        body = {"root": {"output_type": "text", "value": "not valid json {"}}
        rows = flatten_job_response_to_rows(body, "ep")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["container"], "text.raw")
        self.assertIn("not valid json", rows[0]["payload"]["value"])

    def test_batchtext_transcripts_dir_and_each_text_row(self):
        body = {
            "root": {
                "output_type": "batchtext",
                "transcripts_dir": "/data/transcripts",
                "texts": [
                    {"output_type": "text", "value": "hello"},
                    {"output_type": "text", "value": "world"},
                ],
            }
        }
        rows = flatten_job_response_to_rows(body, "audio/transcribe")
        self.assertEqual(len(rows), 3)
        meta = [r for r in rows if r["container"] == "root"][0]
        self.assertEqual(meta["payload"]["transcripts_dir"], "/data/transcripts")
        text_rows = [r for r in rows if r["container"] == "root.texts"]
        self.assertEqual(len(text_rows), 2)

    def test_dict_without_root_key_uses_inner_root_container(self):
        """Wire JSON without ``root`` uses the whole dict as the response root."""
        body = {"foo": 1, "bar": [1, 2]}
        rows = flatten_job_response_to_rows(body, "ep")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["container"], "root")
        self.assertEqual(rows[0]["output_type"], "unknown")

    def test_list_response_data_stored_as_raw_container(self):
        rows = flatten_job_response_to_rows([{"path": "/x"}], "ep")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["container"], "raw")


class TestRecordPipelineSaveResultsDb(unittest.TestCase):
    """Integration: record_pipeline_job_completion persists pipeline_response_rows."""

    def test_second_completion_replaces_rows_for_same_step_job_id(self):
        """Re-run with same step_job_id clears prior flattened rows for that step."""
        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "rr.sqlite"
            with patch(
                "frontend.database.pipeline_job_index_db.index_db_path",
                return_value=db_file,
            ):
                body1 = {
                    "root": {
                        "output_type": "batchfile",
                        "files": [
                            {
                                "output_type": "file",
                                "path": "/one.txt",
                                "file_type": "text",
                            },
                        ],
                    }
                }
                body2 = {
                    "root": {
                        "output_type": "batchfile",
                        "files": [
                            {
                                "output_type": "file",
                                "path": "/two.txt",
                                "file_type": "text",
                            },
                            {
                                "output_type": "file",
                                "path": "/three.txt",
                                "file_type": "text",
                            },
                        ],
                    }
                }
                record_pipeline_job_completion("u", "root", "step-1", "p/e", body1)
                self.assertEqual(
                    len(list_pipeline_response_rows("u", "root", "step-1")), 1
                )
                record_pipeline_job_completion("u", "root", "step-1", "p/e", body2)
                pr = list_pipeline_response_rows("u", "root", "step-1")
                self.assertEqual(len(pr), 2)
                self.assertEqual(
                    {r["payload"].get("path") for r in pr},
                    {"/two.txt", "/three.txt"},
                )


class TestRecordImageSummaryForPipeline(unittest.TestCase):
    def test_skips_when_endpoint_not_image_summary_summarize(self):
        with patch(
            "frontend.database.pipeline_index_service.insert_chunks"
        ) as mock_insert:
            record_image_summary_for_pipeline(
                "u1",
                "job1",
                "text_embeddings/search",
                _text_response_dict({"image_summary": True, "files": []}),
            )
        mock_insert.assert_not_called()

    def test_skips_without_user_or_job(self):
        with patch(
            "frontend.database.pipeline_index_service.insert_chunks"
        ) as mock_insert:
            record_image_summary_for_pipeline(
                "",
                "job1",
                "image_summary/summarize-images",
                _text_response_dict({"image_summary": True, "files": ["/x.txt"]}),
            )
            record_image_summary_for_pipeline(
                "u1",
                "",
                "image_summary/summarize-images",
                _text_response_dict({"image_summary": True, "files": ["/x.txt"]}),
            )
        mock_insert.assert_not_called()

    def test_file_pairs_records_without_input_dir(self):
        """Pipeline payloads may omit input_dir when file_pairs carries provenance."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            out_txt = base / "photo.jpg.txt"
            out_txt.write_text("caption text", encoding="utf-8")
            img = str(base / "photo.jpg")
            payload = {
                "image_summary": True,
                "input_dir": "",
                "files": [str(out_txt)],
                "file_pairs": [
                    {"input_path": img, "output_path": str(out_txt)},
                ],
            }
            db_file = base / "idx.sqlite"
            with patch(
                "frontend.database.pipeline_job_index_db.index_db_path",
                return_value=db_file,
            ):
                record_image_summary_for_pipeline(
                    "user-a",
                    "root-job-1",
                    "image_summary/summarize-images",
                    _text_response_dict(payload),
                )
                found = lookup_source_image("user-a", "root-job-1", str(out_txt))
            self.assertEqual(found, img)

    def test_file_pairs_provenance_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            out_txt = base / "a.jpg.txt"
            out_txt.write_text("hi", encoding="utf-8")
            img = str(base / "a.jpg")
            payload = {
                "image_summary": True,
                "input_dir": "/ignored",
                "files": [str(out_txt)],
                "file_pairs": [
                    {"input_path": img, "output_path": str(out_txt)},
                ],
            }
            captured = []

            def capture(uid, root, rows):
                captured.extend(rows)

            db_file = base / "idx2.sqlite"
            with patch(
                "frontend.database.pipeline_job_index_db.index_db_path",
                return_value=db_file,
            ), patch(
                "frontend.database.pipeline_index_service.insert_chunks",
                side_effect=capture,
            ):
                record_image_summary_for_pipeline(
                    "u",
                    "j",
                    "image_summary/summarize-images",
                    _text_response_dict(payload),
                )
            self.assertEqual(len(captured), 1)
            prov = captured[0]["provenance"]
            self.assertEqual(prov.get("from_payload"), "file_pairs")
            self.assertEqual(prov.get("pipeline_root_job_id"), "j")

    def test_filename_heuristic_when_no_file_pairs(self):
        """Without file_pairs, rows use input_dir + source_image_path_from_summary."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            input_dir = base / "in"
            output_dir = base / "out"
            input_dir.mkdir()
            output_dir.mkdir()
            img = input_dir / "shot.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\n")
            summary_txt = output_dir / "shot.png.txt"
            summary_txt.write_text("desc", encoding="utf-8")
            payload = {
                "image_summary": True,
                "input_dir": str(input_dir),
                "files": [str(summary_txt)],
            }
            db_file = base / "idx3.sqlite"
            with patch(
                "frontend.database.pipeline_job_index_db.index_db_path",
                return_value=db_file,
            ):
                record_image_summary_for_pipeline(
                    "u2",
                    "job2",
                    "image_summary/summarize-images",
                    _text_response_dict(payload),
                )
                found = lookup_source_image("u2", "job2", str(summary_txt))
                self.assertEqual(found, str(img))
                from frontend.database.pipeline_job_index_db import (
                    lookup_metadata_for_output,
                )

                meta = lookup_metadata_for_output("u2", "job2", str(summary_txt))
            self.assertIsNotNone(meta)
            self.assertEqual(meta.get("from_payload"), "filename_heuristic")


class TestRecordPipelineJobCompletion(unittest.TestCase):
    """Unified hook: lineage (pipeline_job_steps) + generic file_pair_rows indexing."""

    def test_records_lineage_and_file_pair_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            inp = base / "in.bin"
            out = base / "out.bin"
            inp.write_text("src", encoding="utf-8")
            out.write_text("dst", encoding="utf-8")
            payload = {
                "file_pair_rows": [
                    {
                        "input_path": str(inp),
                        "output_path": str(out),
                        "metadata": {"score": 0.9},
                    }
                ]
            }
            db_file = base / "pipe.sqlite"
            with patch(
                "frontend.database.pipeline_job_index_db.index_db_path",
                return_value=db_file,
            ):
                record_pipeline_job_completion(
                    "user-x",
                    "root-z",
                    "step-job-1",
                    "my_plugin/run",
                    _text_response_dict(payload),
                )
                steps = list_pipeline_job_steps("user-x", "root-z")
                self.assertEqual(len(steps), 1)
                self.assertEqual(steps[0]["endpoint"], "my_plugin/run")
                self.assertEqual(steps[0]["step_job_id"], "step-job-1")
                self.assertEqual(
                    lookup_input_for_output("user-x", "root-z", str(out)),
                    str(inp),
                )
                pr = list_pipeline_response_rows("user-x", "root-z", "step-job-1")
                self.assertGreaterEqual(len(pr), 1)
                containers = [r["container"] for r in pr]
                self.assertIn("text.json.file_pair_rows", containers)

    def test_lineage_without_json_artifacts(self):
        """Non-text responses still get a pipeline_job_steps row."""
        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "p2.sqlite"
            body = {
                "root": {
                    "output_type": "file",
                    "path": "/tmp/placeholder.txt",
                    "file_type": "text",
                    "title": "out",
                }
            }
            with patch(
                "frontend.database.pipeline_job_index_db.index_db_path",
                return_value=db_file,
            ):
                record_pipeline_job_completion("u1", "r1", "jid", "export/stuff", body)
                steps = list_pipeline_job_steps("u1", "r1")
                self.assertEqual(len(steps), 1)
                self.assertEqual(steps[0]["detail"]["response"]["output_type"], "file")
                pr = list_pipeline_response_rows("u1", "r1", "jid")
                self.assertEqual(len(pr), 1)
                self.assertEqual(pr[0]["container"], "root")

    def test_batchfile_one_row_per_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "bf.sqlite"
            body = {
                "root": {
                    "output_type": "batchfile",
                    "files": [
                        {
                            "output_type": "file",
                            "path": "/out/a.txt",
                            "file_type": "text",
                            "title": "a",
                        },
                        {
                            "output_type": "file",
                            "path": "/out/b.txt",
                            "file_type": "text",
                            "title": "b",
                        },
                    ],
                }
            }
            with patch(
                "frontend.database.pipeline_job_index_db.index_db_path",
                return_value=db_file,
            ):
                record_pipeline_job_completion("u", "root", "s1", "plugin/x", body)
                pr = list_pipeline_response_rows("u", "root", "s1")
            self.assertEqual(len(pr), 2)
            self.assertEqual(
                [r["payload"].get("path") for r in pr],
                ["/out/a.txt", "/out/b.txt"],
            )


if __name__ == "__main__":
    unittest.main()
