"""Tests for shared plugin I/O TypedDicts."""

from rb.lib.plugin_io import ImageSummaryFilePair, InputOutputFilePair


def test_input_output_file_pair_is_image_summary_alias():
    row: InputOutputFilePair = {
        "input_path": "/data/in/a.jpg",
        "output_path": "/out/a.jpg.txt",
    }
    same: ImageSummaryFilePair = row
    assert same["input_path"] == "/data/in/a.jpg"
    assert same["output_path"] == "/out/a.jpg.txt"
