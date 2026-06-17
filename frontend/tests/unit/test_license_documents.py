"""Tests for License & Copyright document listing (About page)."""

from frontend.components.about import _primary_and_third_party_paths


def test_primary_and_third_party_paths_splits_top_level():
    files = [
        "LICENSE",
        "NOTICE",
        "COPYRIGHT.txt",
        "gemma/LICENSE.txt",
        "deepfake-detection/LICENSES/foo.txt",
    ]
    primary, third = _primary_and_third_party_paths(files)
    assert primary == [
        ("LICENSE", "LICENSE"),
        ("COPYRIGHT", "COPYRIGHT.txt"),
        ("NOTICE", "NOTICE"),
    ]
    assert third == [
        "deepfake-detection/LICENSES/foo.txt",
        "gemma/LICENSE.txt",
    ]


def test_primary_and_third_party_paths_only_nested():
    files = ["pkg/a.txt", "pkg/b.md"]
    primary, third = _primary_and_third_party_paths(files)
    assert primary == []
    assert third == ["pkg/a.txt", "pkg/b.md"]
