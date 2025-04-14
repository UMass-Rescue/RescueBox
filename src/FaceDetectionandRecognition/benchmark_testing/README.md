# Benchmark Testing

This repository contains scripts and tools to benchmark the performance and accuracy of a face recognition system. The scripts automate testing tasks such as dataset preparation, bulk uploads, response time measurements, and accuracy evaluations.

---

## Dataset

The dataset for testing can be found at [Dataset](https://drive.google.com/file/d/1dpfTxxAbM-3StVNCsA6qQyYNhhlsfPOu/view?usp=sharing).

---

## Single file run benchmark code
- set up .env in root directory with the following variables
    - DATABASE_DIRECTORY = path to directory of images to be uploaded to database
    - QUERIES_DIRECTORY = path to directory of images to be queried
- set detector and embedding model in model_config.json, and DB settings in db_config.json (or leave as whatevers there currently)
- cd benchmark_testing
- run `bash benchmark.sh` for default benchmarking
- run `bash benchmark.sh -h` for options

---

## Other Benchmarking Files
- **`run_face_find_time.sh`**  
  Starts the server and tests the face recognition function by running a single query image against the database, measuring the time taken to return results.

- **`run_face_find_random.sh`**  
Starts the server and tests the face recognition function by running a single random query image against the database, measuring the time taken to return results.

- **`edgecase_testing.py`**
  A script to test edge cases of a face recognition system allowing us to find reasons for failure. It visualizes detected faces by drawing bounding boxes on images and verifies the similarity between two images, providing the distance and the metric used for comparison. 
---

## Folder Structure
- **`test_data_setup.py`**  
  Prepares the test dataset by randomly selecting one image per person for upload and one image for testing. The input directory should be a recursive directory such that each directory contains different images of the same person. It outputs two directories:
    - `sample_database directory`: Contains images to be uploaded to the database.
    - `sample_queries directory`: Contains query images used for face recognition accuracy testing.

Note: One such pair of sample database and queries directories have already been created for testing (available in the dataset download mentioned above).

---