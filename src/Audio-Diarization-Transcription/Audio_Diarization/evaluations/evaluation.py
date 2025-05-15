# Evaluation file
from pyannote.metrics.diarization import DiarizationErrorRate
from pyannote.core import Annotation, Segment
from pathlib import Path
import tempfile

# Setup paths
ref_rttm_path = Path("AliMeeting.SpeakerDiarization.Benchmark.test.rttm")
hyp_dir = Path("predicted_rttm")
eval_file = Path("ali.eval")

# Load evaluation file list
with open(eval_file, "r") as f:
    eval_files = [line.strip().replace(".wav", "") for line in f]

# Load all reference lines
with open(ref_rttm_path, "r") as f:
    all_rttm_lines = f.readlines()

metric = DiarizationErrorRate()
print(f"\nEvaluating {len(eval_files)} files...\n")

total_der = 0.0
total_components = {"confusion": 0.0, "missed detection": 0.0, "false alarm": 0.0}
total_duration = 0.0
count = 0

for file_id in sorted(eval_files):
    hyp_path = hyp_dir / f"{file_id}.rttm"
    if not hyp_path.exists():
        print(f"Missing prediction: {file_id}.rttm")
        continue

    ref_lines = [line for line in all_rttm_lines if line.split()[1] == file_id]
    if not ref_lines:
        print(f"No reference lines for {file_id}")
        continue

    # Reference annotation
    with tempfile.NamedTemporaryFile(
        "w+", suffix=".rttm", delete=False
    ) as temp_ref_file:
        temp_ref_file.writelines(ref_lines)
        temp_ref_file.flush()
        reference = Annotation()
        with open(temp_ref_file.name, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 9:
                    continue
                start, dur, speaker = float(parts[3]), float(parts[4]), parts[7]
                reference[Segment(start, start + dur)] = speaker

    # Hypothesis annotation
    hypothesis = Annotation()
    with open(hyp_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 9:
                continue
            start, dur, speaker = float(parts[3]), float(parts[4]), parts[7]
            hypothesis[Segment(start, start + dur)] = speaker

    # Compute detailed metrics
    detailed = metric.compute_components(reference, hypothesis)
    file_duration = detailed["total"]
    file_der = metric(reference, hypothesis)

    total_der += file_der
    total_duration += file_duration
    count += 1

    # Accumulate breakdown components
    for k in total_components:
        total_components[k] += detailed[k]

    # Print detailed result
    print(
        f"{file_id}: DER = {100 * file_der:.2f}% | Miss = {100 * detailed['missed detection'] / file_duration:.2f}% | FA = {100 * detailed['false alarm'] / file_duration:.2f}% | Conf = {100 * detailed['confusion'] / file_duration:.2f}%"
    )

# Summary
if count > 0:
    avg_der = 100 * total_der / count
    print(f"\nAverage DER over {count} files: {avg_der:.2f}%")

    print("\nOverall breakdown:")
    for key, value in total_components.items():
        percent = 100 * value / total_duration if total_duration > 0 else 0.0
        print(f"{key.title()} = {percent:.2f}%")
else:
    print("No valid evaluations.")
