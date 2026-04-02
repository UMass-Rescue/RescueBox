"""Ordering guarantees for pipeline / batch processing."""

from pathlib import Path

from image_summary.process import iter_image_files


def test_iter_image_files_preserves_file_filter_order(tmp_path: Path) -> None:
    """CLIP / pipeline passes file_filter in search rank order; summarize must match."""
    d = tmp_path / "in"
    d.mkdir()
    for name in ("z.jpg", "a.jpg", "m.jpg"):
        (d / name).write_bytes(b"\xff\xd8\xff")
    order = [d / "m.jpg", d / "a.jpg", d / "z.jpg"]
    got = list(iter_image_files(d, order))
    assert [p.name for p in got] == ["m.jpg", "a.jpg", "z.jpg"]


def test_iter_image_files_empty_filter_scans_sorted_names(tmp_path: Path) -> None:
    d = tmp_path / "in2"
    d.mkdir()
    for name in ("b.jpg", "a.jpg"):
        (d / name).write_bytes(b"\xff\xd8\xff")
    got = list(iter_image_files(d, []))
    assert [p.name for p in got] == ["a.jpg", "b.jpg"]
