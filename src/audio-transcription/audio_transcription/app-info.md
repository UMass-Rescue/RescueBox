# Audio Transcription

Audio Transcription uses Whisper to transcribe speech in audio files. It processes all supported audio files in a directory (including subdirectories) and returns the transcription text for each file.
Note : this is a CPU intensive operation and not a GPU load. and hence takes  time per audio file


## Inputs

- **Audio Directory:** Path to a directory containing audio files to transcribe. Supported formats: .mp3, .wav, .flac, .aac.

## Outputs

- **Batch Text Response:** Each audio file is returned with:
  - **Title:** Source file path
  - **Value:** Transcription text for that file

### Sample Output

```json
{
  "file_path": "/path/to/recording.mp3",
  "result": "Hello, this is the transcribed text from the audio file."
}
```

Results can be viewed in the Jobs page. Each transcription is shown with its source file path and the transcribed text.
