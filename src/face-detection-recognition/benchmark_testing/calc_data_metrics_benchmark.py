import re
import os
import csv
import argparse
from dotenv import load_dotenv

import pandas as pd


parser = argparse.ArgumentParser(description="To parse text arguments")
load_dotenv()

# detector
parser.add_argument(
    "--detector", required=False, type=str, help="Name of detector", default="yolov8"
)

# embedding
parser.add_argument(
    "--embedding", required=False, type=str, help="Name of embedding", default="arcface"
)

# benchmark results path
parser.add_argument(
    "--results_path",
    required=False,
    type=str,
    help="Parent Results directory",
    default="./benchmark-results",
)

# results_name
parser.add_argument(
    "--results_name",
    required=False,
    type=str,
    help="Name of results output",
    default="results",
)

args = parser.parse_args()


# Extract ground truth names (base names without numeric suffixes)
def extract_ground_truth(x):
    match = re.match(r"(.+?)_\d+\.jpg", x)
    return match.group(1) if match else None


# Add a column to check if the prediction is correct based on whether the predicted names match the ground truth
def is_correct_match(row, top_n=5):
    # If no match was expected and none was found, that's correct
    if not row["true_label"] and not row["predicted"]:
        return True

    # If no match was expected but one was found, that's incorrect
    if not row["true_label"] and row["predicted"]:
        return False

    # If a match was expected but none was found, that's incorrect
    if row["true_label"] and not row["predicted"]:
        return False

    # If a match was expected and found, check if it's the correct person
    if row["true_label"] and row["predicted"]:
        # Get the predicted person names (limited to top-N)
        predicted_person_names = []
        paths = row["result"].split()[:top_n]  # Limit to top-N matches
        for path in paths:
            base_filename = os.path.basename(path.strip())
            match = re.match(r"(.+?)_\d+\.jpg", base_filename)
            if match:
                predicted_person_names.append(match.group(1))

        # Check if the ground truth name is in the predicted names
        return row["ground_truth"] in predicted_person_names

    return False


# A function to check any match was found
def check_match(row):
    # Check for NaN in 'result' column
    if pd.isna(row["result"]) or row["result"].strip() == "":
        # No matches found
        return False

    # Check if the result contains "Collection does not exist"
    if "Collection does not exist" in row["result"]:
        return False

    # Split the result by spaces to get individual file names
    predicted_paths = row["result"].split()

    # Extract base names from each filename
    predicted_base_names = []
    for path in predicted_paths:
        base_filename = os.path.basename(path.strip())
        match = re.match(r"(.+?)_\d+\.jpg", base_filename)
        if match:
            predicted_base_names.append(match.group(1))

    # For checking if a match was found, we only need to know if there's at least one prediction
    return len(predicted_base_names) > 0


# function that creates the true labels (whether there's a match or not)
# assumes queries and db will be sorted in the end
# assumes there will be an underscore split in the file names such that the last element is different and the concatenation of all the
# beginning elements are a unique datapoint identifier (name of an individual)
# e.g. "Bill_Callahan_00001.jpg", where Bill_Callahan is the unique identifier and "_00001.jpg" can be ignored
def calc_true_label():
    queries_path = os.getenv("QUERIES_DIRECTORY")
    db_images_path = os.getenv("DATABASE_DIRECTORY")

    queries, db_images = (
        list(map(lambda x: "_".join(os.path.basename(x).split("_")[:-1]), path_list))
        for path_list in (os.listdir(queries_path), os.listdir(db_images_path))
    )

    queries.sort()
    db_images.sort()

    true_labels = [q in db_images for q in queries]
    return true_labels


true_label_column = calc_true_label()

top_n = ["top_1", "top_5", "top_10"]
N = [1, 5, 10]

abs_results_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "benchmark-results",
)

detector_backend = args.detector
model_name = args.embedding

benchmark_results_dir = os.path.join(
    abs_results_path,
    f"{detector_backend}-{model_name}-{args.results_name}",
    "results-csv",
)
output_directory = os.path.join(
    abs_results_path,
    f"{detector_backend}-{model_name}-{args.results_name}",
    "output-csv-dump",
)

for top_n, n in zip(top_n, N):
    # benchmark results file path
    benchmark_results_path = os.path.join(
        benchmark_results_dir, top_n, f"aggregate_results_{top_n}.csv"
    )
    os.makedirs(os.path.dirname(benchmark_results_path), exist_ok=True)

    with open(benchmark_results_path, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(
            [
                "model",
                "similarity threshold",
                "accuracy",
                "precision",
                "recall",
                "f1",
                "tpr",
                "fpr",
                "tnr",
                "fnr",
            ]
        )

    output_files = os.listdir(output_directory)
    output_files.sort(key=lambda x: float(x.split("_")[-1].split(".")[0]))
    for filename in output_files:
        if not filename.endswith(".csv"):
            continue

        similarity_threshold = os.path.splitext(filename)[0].split("_")[-1]

        data = pd.read_csv(os.path.join(output_directory, filename))

        # Determine the midpoint of the DataFrame
        midpoint = len(data) // 2

        # Set `true_label` column
        data["true_label"] = true_label_column

        data["ground_truth"] = data["filename"].apply(extract_ground_truth)

        # Apply the function to each row to create a 'predicted' column with boolean values

        data["predicted"] = data.apply(lambda row: check_match(row), axis=1)

        data["is_correct"] = data.apply(lambda row: is_correct_match(row, n), axis=1)

        # Calculate basic metrics
        accuracy = data["is_correct"].mean()

        # Calculate TP, FP, TN, FN properly
        true_positives = sum(
            (data["true_label"]) & (data["predicted"]) & (data["is_correct"])
        )
        false_positives = sum((~data["true_label"]) & (data["predicted"]))
        true_negatives = sum((~data["true_label"]) & (~data["predicted"]))
        false_negatives = sum(
            (data["true_label"])
            & ((~data["predicted"]) | ((data["predicted"]) & (~data["is_correct"])))
        )

        # Calculate metrics based on the properly counted values
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0
        )
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        # For compatibility with the output format
        tp, fp, tn, fn = (
            true_positives,
            false_positives,
            true_negatives,
            false_negatives,
        )

        results = [
            detector_backend,
            model_name,
            similarity_threshold,
            accuracy,
            precision,
            recall,
            f1,
            tp,
            fp,
            tn,
            fn,
        ]

        with open(benchmark_results_path, "a", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(results)

        # # Output the results
        # print(f"Accuracy: {accuracy:.4f}")
        # print(f"Precision: {precision:.4f}")
        # print(f"Recall: {recall:.4f}")
        # print(f"F1 Score: {f1:.4f}")
        # print(f"True Positives: {tp}")
        # print(f"False Positives: {fp}")
        # print(f"True Negatives: {tn}")
        # print(f"False Negatives: {fn}")

        # Save detailed results to a file
        detailed_results_path = os.path.join(
            benchmark_results_dir,
            top_n,
            "detailed_results",
            f"{detector_backend}_{model_name}_{similarity_threshold}_results.txt",
        )
        os.makedirs(os.path.dirname(detailed_results_path), exist_ok=True)
        with open(detailed_results_path, "w") as f:
            f.write(
                f"Filename, Expected Match, Found Match (Top-{top_n}), Correct Match?, Matched Names\n"
            )
            for i, row in data.iterrows():
                expected = "Yes" if row["true_label"] else "No"
                found = "Yes" if row["predicted"] else "No"
                correct = "YES" if row["is_correct"] else "NO"

                # Get the matched names for display
                matched_names = ""
                if (
                    row["predicted"]
                    and not pd.isna(row["result"])
                    and "Collection does not exist" not in row["result"]
                ):
                    names = []
                    # Limit to top-N matches
                    for path in row["result"].split()[:n]:
                        base_name = os.path.basename(path.strip())
                        names.append(base_name)
                    matched_names = ", ".join(names)

                f.write(
                    f"{row['filename']}, {expected}, {found}, {correct}, {matched_names}\n"
                )

        # Save metrics to a file
        detailed_metrics_path = os.path.join(
            benchmark_results_dir,
            top_n,
            "detailed_metrics",
            f"{detector_backend}_{model_name}_{similarity_threshold}_metrics.txt",
        )
        os.makedirs(os.path.dirname(detailed_metrics_path), exist_ok=True)
        with open(detailed_metrics_path, "w") as f:
            # f.write(f"Collection Name: {os.getenv('DB_NAME', 'Unknown')}\n")
            f.write(f"Model: {model_name}\n")
            f.write(f"Detector: {detector_backend}\n")
            f.write(f"Similarity Threshold: {similarity_threshold}\n")
            f.write(f"Evaluation: Top-{top_n} matches\n\n")
            f.write(f"Accuracy: {accuracy:.4f}\n")
            f.write(f"Precision: {precision:.4f}\n")
            f.write(f"Recall: {recall:.4f}\n")
            f.write(f"F1 Score: {f1:.4f}\n\n")
            f.write("Confusion Matrix:\n")
            f.write(f"True Positives: {tp} (correctly found matches)\n")
            f.write(f"False Positives: {fp} (incorrectly found matches)\n")
            f.write(f"True Negatives: {tn} (correctly found no matches)\n")
            f.write(f"False Negatives: {fn} (incorrectly found no matches)\n")

generic_detailed_metrics_path = os.path.join(
    benchmark_results_dir, "top_n", "detailed_metrics"
)
generic_detailed_results_path = os.path.join(
    benchmark_results_dir, "top-n", "detailed_results"
)
print(f"\nEasy to Read Metrics saved to:\n\n {generic_detailed_metrics_path}\n\n")
print(f"\nDetailed results saved to:\n\n {generic_detailed_results_path}\n")
