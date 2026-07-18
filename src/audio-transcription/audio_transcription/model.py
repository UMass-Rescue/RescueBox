import logging
import os
import re
import sys
from pathlib import Path

from faster_whisper import WhisperModel, download_model

logger = logging.getLogger(__name__)


DEFAULT_MODEL_SIZE = "base"


def _flat_model_dir(cache: Path, model_size: str) -> Path:
    """Directory with real files (no HF hub symlink layout)."""
    safe = re.sub(r"[^\w.-]+", "_", model_size)
    return cache / f"ct2-{safe}"


def _model_dir_is_ready(model_dir: Path) -> bool:
    model_bin = model_dir / "model.bin"
    config = model_dir / "config.json"
    if not model_bin.is_file() or not config.is_file():
        return False
    try:
        with model_bin.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            return handle.tell() > 0
    except OSError:
        return False


def _bundled_whisper_cache_dir() -> Path | None:
    """``backend/_internal/whisper-models`` next to the PyInstaller backend exe or cwd."""
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(
            Path(sys.executable).resolve().parent / "_internal" / "whisper-models"
        )
    candidates.append(Path.cwd() / "_internal" / "whisper-models")
    for path in candidates:
        if path.is_dir():
            return path.resolve()
    return None


def whisper_cache_dir() -> Path:
    """Directory for faster-whisper / CTranslate2 weights (writable on desktop installs)."""
    env = os.environ.get("RESCUEBOX_WHISPER_CACHE")
    if env:
        return Path(env).expanduser().resolve()
    bundled = _bundled_whisper_cache_dir()
    if bundled is not None:
        return bundled
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg) / "rescuebox" / "whisper-models"
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    if base is None:
        base = str(Path.home() / "AppData" / "Local")
    return Path(base) / "RescueBox" / "whisper-models"


def whisper_local_files_only() -> bool:
    """Offline weights: explicit env or bundled ``models.zip`` extract under ``_internal``."""
    if os.environ.get("RESCUEBOX_WHISPER_CACHE"):
        return True
    return _bundled_whisper_cache_dir() is not None


def ensure_whisper_model_downloaded(
    model_size: str,
    *,
    cache_dir: Path | None = None,
    local_files_only: bool = False,
) -> str:
    """
    Block until ``model_size`` weights are present under ``cache_dir``.

    Returns the local path suitable for ``WhisperModel(...)``.
    """
    cache = cache_dir or whisper_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    model_dir = _flat_model_dir(cache, model_size)

    if not _model_dir_is_ready(model_dir):
        logger.info(
            "Downloading or verifying Whisper model %r into %s",
            model_size,
            model_dir,
        )
        # Use output_dir (flat files). cache_dir uses HF symlinks that CTranslate2
        # often cannot open on Windows.
        download_model(
            model_size,
            output_dir=str(model_dir),
            local_files_only=local_files_only,
        )
        if not _model_dir_is_ready(model_dir):
            raise RuntimeError(
                f"Whisper model download incomplete (missing or empty model.bin): "
                f"{model_dir}"
            )
    else:
        logger.info("Whisper model ready at %s", model_dir)

    return str(model_dir)


class AudioTranscriptionModel:
    def __init__(
        self,
        model_size: str | None = None,
        *,
        cache_dir: Path | None = None,
        local_files_only: bool = False,
    ):
        self._model_size = model_size or os.environ.get(
            "RESCUEBOX_WHISPER_MODEL", DEFAULT_MODEL_SIZE
        )
        self._cache_dir = cache_dir
        self._local_files_only = local_files_only
        self._model: WhisperModel | None = None
        self.audio_extensions = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"}

    def _ensure_model_loaded(self) -> WhisperModel:
        if self._model is None:
            model_path = ensure_whisper_model_downloaded(
                self._model_size,
                cache_dir=self._cache_dir,
                local_files_only=self._local_files_only,
            )
            self._model = WhisperModel(model_path, device="cpu", compute_type="int8")
        return self._model

    def get_audio_files(self, directory: str) -> list[Path]:
        audio_files = []

        directory_path = Path(directory)

        for file_path in directory_path.rglob("*"):
            if file_path.suffix.lower() in self.audio_extensions:
                audio_files.append(file_path)

        return audio_files

    def _validate_audio_path(self, audio_path: str) -> None:
        if audio_path is None:
            raise ValueError("audio_path cannot be None")

    def transcribe(self, audio_path: str, out_dir: str = None) -> str:
        self._validate_audio_path(audio_path)
        whisper = self._ensure_model_loaded()
        segments, _info = whisper.transcribe(str(audio_path))
        res = "".join(segment.text for segment in segments)
        if out_dir:
            self._write_res_to_dir(
                [{"file_path": str(audio_path), "result": res}], out_dir
            )
        return res

    def transcribe_batch(self, audio_paths: list[str]) -> list[dict]:
        return [
            {"file_path": str(audio_path), "result": self.transcribe(audio_path)}
            for audio_path in audio_paths
        ]

    def _write_res_to_dir(self, res: list[dict], out_dir: str) -> None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for r in res:
            stem = Path(r["file_path"]).stem
            with open(out_dir / f"{stem}.txt", "w", encoding="utf-8") as f:
                f.write(r["result"])

    def transcribe_files_in_directory(
        self, input_dir: str, out_dir: str = None
    ) -> list[dict]:
        paths = self.get_audio_files(input_dir)
        res = self.transcribe_batch([str(p) for p in paths])
        if out_dir:
            self._write_res_to_dir(res, out_dir)
        return res
