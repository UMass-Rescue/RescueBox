# 🔊 Speaker Diarization Evaluation Pipeline 

This pipeline evaluates diarization output against the benchmark using the PyAnnote evaluation framework.

---

## Workflow Overview

1. **Run RescueBox** to generate a diarization CSV.
2. **Convert the CSV** to RTTM format using `convert_csv_rttm.py`.
3. **List all `.wav` files** in a `.eval` file.
4. **Configure and run `evaluation.py`** to compute diarization metrics.

---
![image](https://github.com/user-attachments/assets/74be9960-31c4-4228-a85f-eb53166e3375)

## 📁 Step-by-Step Instructions

### 1. Run RescueBox

After running the RescueBox app on one of the datasets, you will get a CSV file:

Use the `convert_csv_rttm.py` script to convert the CSV output to individual `.rttm` files.


### 2. Create custom.eval File
List all .wav filenames (without path) that you want to evaluate. For example:

audio1.wav
audio2.wav
audio3.wav

To aid in this process you can run the following script. Inside the python file modify the path to the folder with the wav files

```
python file_names.py
```
### 3. Configure evaluation.py
Open `evaluation.py` and modify the following variables:

reference_dir = "path/to/Expected_output" (https://huggingface.co/pyannote/speaker-diarization-3.0/blob/main/reproducible_research/VoxConverse.SpeakerDiarization.Benchmark.test.rttm)

hyp_dir = "predicted_rttm/"

eval_file = "custom.eval"

Make sure the filenames in custom.eval match exactly with the corresponding .wav and .rttm files.

### 4. Run Evaluation
Now run the evaluation script: `evaluation.py`

This will print Diarization Error Rate (DER), False Alarm, Missed Detection, Confusion percentage comparing your predictions to ground truth RTTMs.

![image](https://github.com/user-attachments/assets/7a2e3fe7-3957-4966-8f10-482bd6951210)

## Helpful Scripts

To sample a small number of audio files to evaluate (since running too many files takes too long). You can use slect_eavs.py to sample a predefined number. Inside the script file change sample_size to your desired number and update the input out output folder paths before running the function

```
python select_wavs.py
```

Some datasets provide their audio files in the .flac format instead of the tranditional .wav format. The following script quickly coverts .floc to .wav for evaluation. Simply change the input and output folder paths before running the script

```
python flac_to_wav.py
```