"""Windows DLL search paths for ONNX Runtime CUDA/cuDNN (before provider load)."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

_CUDNN_INSTALL_ROOT = Path(r"C:\Program Files\NVIDIA\CUDNN")
_CUDA_TOOLKIT_ROOT = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA")

_detected_cuda: Path | None = None
_detected_cudnn: Path | None = None
_detected_toolkit_ver: tuple[int, int] | None = None
_cuda_source: str = ""
_cudnn_source: str = ""


def _parse_dot_version(name: str) -> tuple[int, int] | None:
    parts = name.split(".")
    if not parts or not parts[0].isdigit():
        return None
    major = int(parts[0])
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    return major, minor


def _cuda_version_from_bin(bin_dir: Path) -> tuple[int, int] | None:
    return _parse_dot_version(bin_dir.parent.name.removeprefix("v"))


def _is_cudnn_x64_bin(directory: Path) -> bool:
    if not directory.is_dir():
        return False
    for entry in directory.iterdir():
        if entry.suffix.lower() == ".dll" and entry.name.lower().startswith("cudnn"):
            return True
    return False


def _pick_cudnn_cuda_bin(
    cuda_bins: list[tuple[Path, tuple[int, int]]],
    toolkit_ver: tuple[int, int] | None,
) -> Path | None:
    if not cuda_bins:
        return None
    if toolkit_ver is None:
        cuda_bins.sort(key=lambda item: item[1], reverse=True)
        return cuda_bins[0][0]
    major, minor = toolkit_ver
    candidates = [item for item in cuda_bins if item[1][0] == major]
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (abs(item[1][1] - minor), -item[1][1]),
    )
    return candidates[0][0]


def discover_cudnn_bin_windows(
    toolkit_ver: tuple[int, int] | None = None,
) -> Path | None:
    root = _CUDNN_INSTALL_ROOT
    if not root.is_dir():
        return None
    cudnn_versions: list[tuple[Path, tuple[int, int]]] = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        ver = _parse_dot_version(entry.name.removeprefix("v"))
        if ver is None:
            continue
        cudnn_versions.append((entry, ver))
    cudnn_versions.sort(key=lambda item: item[1], reverse=True)

    for ver_dir, _ in cudnn_versions:
        bin_dir = ver_dir / "bin"
        if not bin_dir.is_dir():
            continue
        cuda_bins: list[tuple[Path, tuple[int, int]]] = []
        for entry in bin_dir.iterdir():
            if not entry.is_dir() or entry.name.lower() == "x64":
                continue
            cuda_ver = _parse_dot_version(entry.name)
            if cuda_ver is None:
                continue
            x64 = entry / "x64"
            if _is_cudnn_x64_bin(x64):
                cuda_bins.append((x64, cuda_ver))
        picked = _pick_cudnn_cuda_bin(cuda_bins, toolkit_ver)
        if picked is not None:
            return picked
        if toolkit_ver.is_none():
            x64 = bin_dir / "x64"
            if _is_cudnn_x64_bin(x64):
                return x64
            if _is_cudnn_x64_bin(bin_dir):
                return bin_dir
    return None


def _is_cuda_toolkit_bin(directory: Path) -> bool:
    if not directory.is_dir():
        return False
    for entry in directory.iterdir():
        if entry.suffix.lower() == ".dll" and entry.name.lower().startswith("cudart64"):
            return True
    return False


def discover_cuda_toolkit_windows() -> tuple[Path, tuple[int, int]] | None:
    root = _CUDA_TOOLKIT_ROOT
    if not root.is_dir():
        return None
    versions: list[tuple[Path, tuple[int, int]]] = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        ver = _parse_dot_version(entry.name.removeprefix("v"))
        if ver is None:
            continue
        bin_dir = entry / "bin"
        if _is_cuda_toolkit_bin(bin_dir):
            versions.append((bin_dir, ver))
    if not versions:
        return None
    versions.sort(key=lambda item: item[1], reverse=True)
    return versions[0]


def discover_cuda_bin_windows() -> Path | None:
    pair = discover_cuda_toolkit_windows()
    return pair[0] if pair else None


def _toolkit_version_for_cudnn() -> tuple[int, int] | None:
    cuda_raw = os.environ.get("RESCUEBOX_CUDA_BIN", "").strip()
    if cuda_raw:
        bin_dir = Path(cuda_raw)
        if bin_dir.is_dir():
            return _cuda_version_from_bin(bin_dir)
    pair = discover_cuda_toolkit_windows()
    return pair[1] if pair else None


def _prepend_windows_path(*dirs: Path | None) -> None:
    front = [str(d) for d in dirs if d is not None and d.is_dir()]
    if not front:
        return
    existing = os.environ.get("PATH", "")
    os.environ["PATH"] = ";".join(front + ([existing] if existing else []))


def _add_dll_directory(add_dll, path: Path | None) -> None:
    if path is not None and path.is_dir():
        add_dll(str(path))


def register_windows_dll_directories() -> None:
    if sys.platform != "win32":
        return
    add_dll = getattr(os, "add_dll_directory", None)
    if add_dll is None:
        return

    cuda_raw = os.environ.get("RESCUEBOX_CUDA_BIN", "").strip()
    if cuda_raw:
        cuda_path = Path(cuda_raw)
        cuda_source = "RESCUEBOX_CUDA_BIN"
    else:
        cuda_path = discover_cuda_bin_windows()
        cuda_source = "auto-detect"

    toolkit_ver = _toolkit_version_for_cudnn()
    cudnn_raw = os.environ.get("RESCUEBOX_CUDNN_BIN", "").strip()
    if cudnn_raw:
        cudnn_path = Path(cudnn_raw)
        cudnn_source = "RESCUEBOX_CUDNN_BIN"
    else:
        cudnn_path = discover_cudnn_bin_windows(toolkit_ver)
        cudnn_source = "auto-detect"

    global _detected_cuda, _detected_cudnn, _detected_toolkit_ver, _cuda_source, _cudnn_source
    _detected_cuda = cuda_path if cuda_path and cuda_path.is_dir() else None
    _detected_cudnn = cudnn_path if cudnn_path and cudnn_path.is_dir() else None
    _detected_toolkit_ver = toolkit_ver
    _cuda_source = cuda_source
    _cudnn_source = cudnn_source

    _add_dll_directory(add_dll, cudnn_path)
    _add_dll_directory(add_dll, cuda_path)
    _prepend_windows_path(cudnn_path, cuda_path)


def log_detected_dll_paths() -> None:
    if sys.platform != "win32":
        return
    log = logging.getLogger("rb.api.dll_paths")
    ver = (
        f"{_detected_toolkit_ver[0]}.{_detected_toolkit_ver[1]}"
        if _detected_toolkit_ver
        else "unknown"
    )
    cuda = _detected_cuda or "not found"
    cudnn = _detected_cudnn or "not found"
    msg = "Windows GPU DLL paths (toolkit CUDA %s): CUDA bin=%s (%s); cuDNN bin=%s (%s)"
    if _detected_cuda or _detected_cudnn:
        msg += "; PATH prepended with detected bins"
    log.info(
        msg,
        ver,
        cuda,
        _cuda_source or "n/a",
        cudnn,
        _cudnn_source or "n/a",
    )


register_windows_dll_directories()
