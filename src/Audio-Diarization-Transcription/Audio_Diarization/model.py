import whisper
import numpy as np
from pyannote.audio import Pipeline
from pyannote.core import Segment
from pyannote.audio import Audio
from utils import diarize_text, load_pyannote_pipeline_from_pretrained

# Load the pre-trained speaker diarization pipeline and whisper model
#pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0")
PATH_TO_CONFIG = "./models/pyannote_diarization_config.yaml"
pipeline = load_pyannote_pipeline_from_pretrained(PATH_TO_CONFIG)
asr_model = whisper.load_model("medium.en")

# Path to your audio file
audio_file = "input/TOEFL.mp3"

# Perform diarization on the whole file
print("Performing diarization on the whole file...")
diarization = pipeline(audio_file)
asr_result = asr_model.transcribe(audio_file)

# # Print the diarization output
# for turn, _, speaker in diarization.itertracks(yield_label=True):
#     print(f"Speaker {speaker} speaks from {turn.start:.1f}s to {turn.end:.1f}s")

#Final result
print("\n\nFINAL RESULT---------")
final_result = diarize_text(asr_result, diarization)

for seg, spk, sent in final_result:
    line = f'{seg.start:.2f} {seg.end:.2f} {spk} {sent}'
    print(line)

# Perform diarization on an excerpt (e.g., from 1.0s to 2.0s)
print("\nPerforming diarization on an excerpt...")
excerpt = Segment(start=1.0, end=2.0)

# Load the audio excerpt
waveform, sample_rate = Audio().crop(audio_file, excerpt)

# Perform diarization on the excerpt
excerpt_diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate})

# Print the diarization output for the excerpt
for turn, _, speaker in excerpt_diarization.itertracks(yield_label=True):
    print(f"Speaker {speaker} speaks from {turn.start:.1f}s to {turn.end:.1f}s")