# FACEMATCH

FaceMatch is a system for identifying facial matches within an image database. With FaceMatch, users can create a database of images of people and, by uploading a new image, quickly find any matches for the person of interest within the database. 

Built with a client-server architecture using Flask-ML, FaceMatch provides structured support for efficient client-server communication tailored to ML applications.

---

# Getting started

---
## Download ONNX Models

Link to folder containing ONNX models: https://drive.google.com/drive/folders/1V3H4mcsy44VJNqop9Q2UKm7j0RkT7yba 

To get started, download `arcface_model_new.onnx`, and `yolov8-face-detection.onnx` from the google drive above and put them in a folder called `models` at `<PATH TO PROJECT>/src/face-detection-recognition/face_detection_recognition/models`

---

## Setup .env file
- set up .env in root directory of FaceMatch with the following variables
    - DATABASE_DIRECTORY = path to directory of images to be uploaded to database
    - QUERIES_DIRECTORY = path to directory of images to be queried

# Usage

**Sample dataset to test the model:** The images in the `\resources\sample_db` folder can be used as the database, `\resources\test_image.jpg` can be used as a single query image to test face find (single image), and `\resources\sample_queries` can be used as a set of queries to test face find bulk (multiple images).

## CLI

_Run all below commands from root directory of project._

### Task 1: Upload images to database
```
poetry run python -m ./src/face-detection-recognition/face_detection_recognition/face_match_server.py /face-match/bulkupload "<path_to_directory_of_images>" "<collection_name>"
```
Note: The name of the collection could be a new collection you wish to create or an existing collection you wish to upload to.

_Run with Sample images directory:_

```
poetry run python -m ./src/face-detection-recognition/face_detection_recognition/face_match_server.py /face-match/bulkupload "./resources/sample_db"  "test"

# On Windows: poetry run python -m .\src\face-detection-recognition\face_detection_recognition\face_match_server.py /face-match/bulkupload ".\resources\test_image.jpg" "test,0.5" ".\resources\sample_db" "test"
```

### Task 2: Find matching faces for single image
```
poetry run python -m ./src/face-detection-recognition/face_detection_recognition/face_match_server.py /face-match/findface "<path_to_image>" "<collection_name>,<similarity_threshold>"
```
> Note: The name of the collection needs to be an existing collection you wish to query.
> The default similarity threshold, 0.45 is used if no similarity threshold is provided.


_Run with Sample test image:_

```
poetry run python -m ./src/face-detection-recognition/face_detection_recognition/face_match_server.py /face-match/findface "./resources/test_image.jpg" "test,0.5"

# On Windows: poetry run python -m .\src\face-detection-recognition\face_detection_recognition\face_match_server.py /face-match/findface ".\resources\test_image.jpg" "test,0.5"
```

The correct match for the test image should be outputted with the filename Bill_Belichick_0002

### Task 3: Find matching faces for many images
```
poetry run python -m ./src/face-detection-recognition/face_detection_recognition/face_match_server.py /face-match/findfacebulk   "<path_to_queries>"  "<collection_name>,<similarity_threshold>" 
```
> Note: The name of the collection needs to be an existing collection you wish to query.
> The default similarity threshold, 0.45 is used if no similarity threshold is provided.


_Run with Sample test image:_

```
poetry run python -m ./src/face-detection-recognition/face_detection_recognition/face_match_server.py /face-match/findfacebulk  "./resources/sample_queries" "test,0.5"

# On Windows: poetry run python -m .\src\face-detection-recognition\face_detection_recognition\face_match_server.py /face-match/findfacebulk ".\resources\sample_queries" "test,0.5"
```

Console output will show query filename followed by the found matches file names. The first three images (the ones named Bill) have a match in the database, and the last three do not.


### Use RescueBox Frontend

After you've setup RB and started the RB frontend and server:

- Choose the model from list of available models under the **MODELS** tab.

- Checkout the Inspect page to learn more about using the model.

---


Check out [Testing README](./benchmark_testing/README.md) for complete details on dataset and testing.

Check out this [document](https://docs.google.com/document/d/1CpN__oPgmAvY65s-tWg4X-pZPCPwNEAU-ULrkdKWES4/edit?usp=sharing) for more details on the face detection and recognition models, datasets and testing.

---

# For Developers

## Benchmark Testing

This repository contains scripts and tools to benchmark the performance and accuracy of the face recognition system. The scripts automate testing tasks such as dataset preparation, bulk uploads, response time measurements, and accuracy evaluations.

---

## Dataset

The LFW dataset for testing can be found at [LFW Dataset](https://drive.google.com/file/d/1N8Ym1zqoW875tVIjePWwaxHTN70p6-av/view?usp=share_link). sample_database (840 images) and sample_queries (1680 images) are the preconfigured testing image directories. 

The VGGFace dataset for testing can be found at [VGGFace Dataset](https://drive.google.com/file/d/1YIswaMR87oN9taA97p2dMIzNXUzWZcGe/view?usp=share_link). database (250 images) and queries (500 images) are the preconfigured testing image directories. 

---

## Single file run benchmark code
- *IMPORTANT FOR FUTURE WORK*: The /findfacebulktesting and /listcollections endpoints as they are currently implemented need to exist and be uncommented for this script to work.
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

## Performance Results

![Feature Screenshot](https://private-user-images.githubusercontent.com/98613897/443869197-2e8eb834-5e70-4f40-b5f2-ac76e6c0697c.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDcyNjM0MTgsIm5iZiI6MTc0NzI2MzExOCwicGF0aCI6Ii85ODYxMzg5Ny80NDM4NjkxOTctMmU4ZWI4MzQtNWU3MC00ZjQwLWI1ZjItYWM3NmU2YzA2OTdjLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MTQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTE0VDIyNTE1OFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWJkODQ0YWJlZGI1MzY5ZGY2NGNiNzQ0Nzc0YjNhM2ViOTJhMzc4YTQ3NTNmMTNlNTlmYzk1MmIwZTU3MTYyMGEmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.wtajTyJd8xN5vdTu5xSsscB9ELja-gqabMHsMy8lx3Y)

![Feature Screenshot](https://private-user-images.githubusercontent.com/98613897/443869212-69329284-af0d-4697-82d8-fda328fc28d0.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDcyNjM0MTgsIm5iZiI6MTc0NzI2MzExOCwicGF0aCI6Ii85ODYxMzg5Ny80NDM4NjkyMTItNjkzMjkyODQtYWYwZC00Njk3LTgyZDgtZmRhMzI4ZmMyOGQwLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MTQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTE0VDIyNTE1OFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWU1M2FkYWZmNjZjNzJlMTY4NDhiMzA5Y2RjYjllYWQzYjI3MzNhNmM1NWE0OTg4NmFlMDlmZTU4YTRkMmExNjYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.FKgSNQTvKejNbdth80cOM0pJJ29bQaxABBZQp-oLpls)

![Feature Screenshot](https://private-user-images.githubusercontent.com/98613897/443869224-b2f329f8-5741-4f8c-b079-a40387bd7c61.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDcyNjM0MTgsIm5iZiI6MTc0NzI2MzExOCwicGF0aCI6Ii85ODYxMzg5Ny80NDM4NjkyMjQtYjJmMzI5ZjgtNTc0MS00ZjhjLWIwNzktYTQwMzg3YmQ3YzYxLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA1MTQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNTE0VDIyNTE1OFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTVlYjhjOTRlZWQwYmZmY2U1Njk1ZjYzNzBmODAxMWRmNDM3Njk3YWE3YzdkODA3N2Y5NWE1MzI3ZDRkMzcwMzAmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.xev5KV98mN0HX71q5IP39Acm6d91ilnx8jmlRMYoOEc)

## Folder Structure
- **`test_data_setup.py`**  
  Prepares the test dataset by randomly selecting one image per person for upload and one image for testing. The input directory should be a recursive directory such that each directory contains different images of the same person. It outputs two directories:
    - `sample_database directory`: Contains images to be uploaded to the database.
    - `sample_queries directory`: Contains query images used for face recognition accuracy testing.

Note: One such pair of sample database and queries directories have already been created for testing (available in the dataset download mentioned above).

---

_Run all below commands from root directory of project._

## Run unit tests for facematch

```
poetry run pytest ./src/FaceDetectionandRecognition/test/test_app_main.py -v --capture=no
```

#### Run individual tests

```
poetry run pytest ./src/FaceDetectionandRecognition/test/test_app_main.py::TestFaceMatch::<test function name found in test_app_main.py> -v --capture=no
```


## Other important notes from previous developers (written 5/14/25)
The multipipeline ensemble method endpoints /multi_pipeline_bulkupload  /multi_pipeline_findfacebulk are currently commented out in face_match_server.py. They can be found by using command-F on the endpoint routes listed here and uncommented to try out. The same goes for /listcollections.

As mentioned before, /deletecollection and /listcollections are both required to be uncommented in face_match_server.py to run the benchmark.sh script in the benchmark_testing directory.

The bulkfacefind improved RB output is on the branch FaceMatch_Bulk_Find_Frontend and is up to date with the current state of the project

The ensemble method uploads to 4 collections for every user defined collection. These collection names are handled separately than the single pipeline collections 
(ones created by using /bulkupload). The vision for the multipipeline ensemble approach is to have these two workflows merged into one upload endpoint and one facefind endpoint, where every image uploaded goes to all of the pipeline collections, and the user has the option to select whether they wish to query against all four pipelines using the ensemble approach (slower but more accurate) or simply use one pipeline (faster but less accurate).

