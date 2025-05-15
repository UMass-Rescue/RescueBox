# File to convert the CSV output from RescueBox to rttm for evaluation

import csv
import os

# Input CSV from RescueBox output
input_csv = "diarize_output.csv"


# Output RTTM directory
output_dir = "predicted_rttm"
os.makedirs(output_dir, exist_ok=True)

rttm_entries = {}

with open(input_csv, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        audio_file = row["Audio File"].strip()
        speaker = row["Speaker"].strip()
        time_range = row["Time Range"].strip()

        if not time_range or "Error" in speaker:
            continue

        try:
            start_str, end_str = time_range.split("-")
            start = float(start_str.strip())
            end = float(end_str.strip())
            duration = end - start

            # Format RTTM line
            rttm_line = f"SPEAKER {audio_file.replace('.wav','')} 1 {start:.2f} {duration:.2f} <NA> <NA> {speaker} <NA> <NA>\n"
            rttm_entries.setdefault(audio_file, []).append(rttm_line)
        except Exception as e:
            print(f"⚠️ Failed to process row: {row} — {e}")

# Write RTTM files
for audio_file, lines in rttm_entries.items():
    rttm_path = os.path.join(output_dir, audio_file.replace(".wav", ".rttm"))
    with open(rttm_path, "w") as out:
        out.writelines(lines)
    print(f"✅ Wrote {rttm_path}")
