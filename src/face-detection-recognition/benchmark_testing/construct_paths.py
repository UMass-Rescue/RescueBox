import os
import argparse

parser = argparse.ArgumentParser(description="To parse text arguments")

# Name of desired path
parser.add_argument("--path_name", required=True, type=str, help="Name of desired path")

# detector
parser.add_argument("--detector", required=False, type=str, help="Name of detector")

# embedding
parser.add_argument("--embedding", required=False, type=str, help="Name of embedding")

# benchmark results path
parser.add_argument(
    "--results_path", required=False, type=str, help="Parent Results directory"
)

# results_name
parser.add_argument(
    "--results_name", required=False, type=str, help="Name of results output"
)

args = parser.parse_args()

if args.path_name == "model_config":
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        os.pardir,
        "face_detection_recognition",
        "config",
        "model_config.json",
    )
    print(path)
elif args.path_name == "times_csv":
    # abs_results_path = os.path.abspath(args.results_path)
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "benchmark_testing",
        "benchmark-results",
        f"{args.detector}-{args.embedding}-{args.results_name}",
        "times.csv",
    )
    print(path)
elif args.path_name == "results_dir":
    abs_results_path = os.path.abspath(args.results_path)
    path = os.path.join(
        abs_results_path, f"{args.detector}-{args.embedding}-{args.results_name}"
    )
    print(path)
elif args.path_name == "facematch_server":
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "face_detection_recognition",
        "face_match_server.py",
    )
    print(path)
