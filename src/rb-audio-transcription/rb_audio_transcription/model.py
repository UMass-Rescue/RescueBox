from pathlib import Path

import whisper


class AudioTranscriptionModel:
    def __init__(self, model_path: str = "base"):
        self.model = whisper.load_model(model_path)
        self.audio_extensions = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"}

    def get_audio_files(self, directory: str) -> list[Path]:
        audio_files = []

        # Convert string path to Path object
        directory_path = Path(directory)

        # Iterate over files in directory and subdirectories
        for file_path in directory_path.rglob("*"):
            if file_path.suffix.lower() in self.audio_extensions:
                audio_files.append(file_path)

        return audio_files

    def _validate_audio_path(self, audio_path: str) -> None:
        if audio_path is None:
            raise ValueError("audio_path cannot be None")

    def transcribe(self, audio_path: str, out_dir: str = None) -> str:
        self._validate_audio_path(audio_path)
        res = self.model.transcribe(str(audio_path), fp16=False)["text"]
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

    def _write_res_to_dir(self, res: list[str], out_dir: str) -> None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for r in res:
            with open(
                out_dir / (r["file_path"].split("/")[-1].split(".")[0] + ".txt"), "w"
            ) as f:
                f.write(r["result"])

    def transcribe_files_in_directory(
        self, input_dir: str, out_dir: str = None
    ) -> list[str]:
        res = self.transcribe_batch(self.get_audio_files(input_dir))
        if out_dir:
            self._write_res_to_dir(res, out_dir)
        return res