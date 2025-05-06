import os
import csv
from collections import defaultdict


def parse_file(file_path):
    """
    Parse a results file and extract the "Correct Match?" status for each image.

    Returns:
        dict: Dictionary mapping filenames to binary results (1 for YES, 0 for NO)
    """
    results = {}

    with open(file_path, "r") as file:
        lines = file.readlines()

        for line in lines[1:]:  # Skip header line
            # Split by comma but handle commas in quoted strings
            parts = line.strip().split(",")

            # Extract filename and correct match status
            if len(parts) >= 4:  # Ensure we have enough parts
                filename = parts[0].strip()
                correct_match = parts[3].strip()

                # Convert YES/NO to 1/0
                if correct_match == "YES":
                    results[filename] = 1
                elif correct_match == "NO":
                    results[filename] = 0

    return results


def weighted_majority_vote(all_results, weights):
    """
    Perform a weighted majority vote on face recognition results.

    Returns:
        dict: Dictionary with weighted majority vote results for each image
    """
    # Initialize structure to hold weighted votes
    weighted_votes = defaultdict(float)
    image_counter = defaultdict(int)

    # Accumulate weighted votes
    for file_name, results in all_results.items():
        weight = weights.get(file_name, 1.0)  # Default weight is 1.0

        for image_name, vote in results.items():
            weighted_votes[image_name] += vote * weight
            image_counter[image_name] += 1

    # Determine majority vote for each image
    final_results = {}
    for image_name, vote_sum in weighted_votes.items():
        # Get total possible weight for this image
        total_possible_weight = sum(
            weights.get(file, 1.0)
            for file in all_results.keys()
            if image_name in all_results[file]
        )

        # Image is correctly classified if weighted sum is more than half of total possible weight
        final_results[image_name] = 1 if vote_sum > total_possible_weight / 2 else 0

    return final_results


def main():
    # Directory containing result files
    results_dir = "best_results/"

    # Define weights for each algorithm file
    weights = {
        "retinaface_Facenet512_0.66_results.txt": 1.2,
        "yolov8_Facenet512_0.64_results.txt": 1.1,
        "retinaface_ArcFace_0.5_results.txt": 1.0,
        "yolov8_ArcFace_0.48_results.txt": 0.9,
    }

    all_results = {}

    # Check if the directory exists
    if not os.path.exists(results_dir):
        print(f"Directory {results_dir} not found. Using current directory.")
        results_dir = "."

    # Find all txt files that match the pattern
    result_files = [f for f in os.listdir(results_dir) if f.endswith("_results.txt")]

    if not result_files:
        print(f"No result files found in {results_dir}.")
        # Use the provided file for testing
        test_file = "retinaface_Facenet512_0.64_results.txt"
        if os.path.exists(test_file):
            result_files = [test_file]
            results_dir = "."
        else:
            print(f"Test file {test_file} not found.")
            return

    print(f"Processing {len(result_files)} result files...")

    # Parse each file
    for file_name in result_files:
        file_path = os.path.join(results_dir, file_name)
        try:
            results = parse_file(file_path)
            all_results[file_name] = results
            print(f"Processed {file_name}: Found {len(results)} image results")
        except Exception as e:
            print(f"Error processing {file_name}: {e}")

    # Perform weighted majority vote
    final_results = weighted_majority_vote(all_results, weights)

    # Output results
    print("\nFinal Results:")
    print(f"Total images evaluated: {len(final_results)}")
    correctly_classified = sum(1 for result in final_results.values() if result == 1)
    print(
        f"Correctly classified: {correctly_classified} ({correctly_classified/len(final_results)*100:.2f}%)"
    )
    incorrectly_classified = sum(1 for result in final_results.values() if result == 0)
    print(
        f"Incorrectly classified: {incorrectly_classified} ({incorrectly_classified/len(final_results)*100:.2f}%)"
    )

    # Save results to CSV
    output_file = "weighted_majority_results.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Correctly Classified (1=YES, 0=NO)"])

        for image_name, result in sorted(final_results.items()):
            writer.writerow([image_name, result])

    print(f"\nResults saved to {output_file}")

    # Return the results as structured data
    return {
        "all_results": all_results,  # Raw results from each file
        "final_results": final_results,  # Weighted majority vote results
        "summary": {
            "total": len(final_results),
            "correct": correctly_classified,
            "incorrect": incorrectly_classified,
            "accuracy": (
                correctly_classified / len(final_results) if final_results else 0
            ),
        },
    }


if __name__ == "__main__":
    main()
