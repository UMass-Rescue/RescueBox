import sys

from rb.lib.ml_service import (
    RESCUEBOX_MODEL_DIR_ENV,
    plugin_onnx_models,
    whisper_models_dir,
)


def test_plugin_onnx_models_uses_env(tmp_path, monkeypatch):
    internal = tmp_path / "_internal"
    bundled = internal / "image_embeddings" / "onnx_models"
    bundled.mkdir(parents=True)
    monkeypatch.setenv(RESCUEBOX_MODEL_DIR_ENV, str(internal))
    resolved = plugin_onnx_models("image_embeddings")
    assert resolved == bundled.resolve()


def test_plugin_onnx_models_frozen_internal(tmp_path, monkeypatch):
    monkeypatch.delenv(RESCUEBOX_MODEL_DIR_ENV, raising=False)
    backend_root = tmp_path / "backend"
    internal_models = (
        backend_root / "_internal" / "age_and_gender_detection" / "onnx_models"
    )
    internal_models.mkdir(parents=True)
    fake_exe = backend_root / "rescuebox.exe"
    fake_exe.touch()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))
    resolved = plugin_onnx_models("age_and_gender_detection")
    assert resolved == internal_models.resolve()


def test_whisper_models_dir_frozen_internal(tmp_path, monkeypatch):
    monkeypatch.delenv(RESCUEBOX_MODEL_DIR_ENV, raising=False)
    backend_root = tmp_path / "backend"
    whisper_dir = backend_root / "_internal" / "whisper-models"
    whisper_dir.mkdir(parents=True)
    fake_exe = backend_root / "rescuebox.exe"
    fake_exe.touch()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))
    resolved = whisper_models_dir()
    assert resolved == whisper_dir.resolve()


def test_whisper_models_dir_uses_env(tmp_path, monkeypatch):
    internal = tmp_path / "_internal"
    bundled = internal / "whisper-models"
    bundled.mkdir(parents=True)
    monkeypatch.setenv(RESCUEBOX_MODEL_DIR_ENV, str(internal))
    resolved = whisper_models_dir()
    assert resolved == bundled.resolve()
