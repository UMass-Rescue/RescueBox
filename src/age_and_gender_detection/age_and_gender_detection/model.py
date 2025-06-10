# SPDX-License-Identifier: Apache-2.0

import cv2
import onnxruntime as ort
import argparse
import numpy as np
from pathlib import Path
from age_and_gender_detection.box_utils import predict
from pprint import pprint


# scale current rectangle to box
def scale(box):
    width = box[2] - box[0]
    height = box[3] - box[1]
    maximum = max(width, height)
    dx = int((maximum - width) / 2)
    dy = int((maximum - height) / 2)

    bboxes = [box[0] - dx, box[1] - dy, box[2] + dx, box[3] + dy]
    return bboxes


# crop image
def cropImage(image, box):
    num = image[box[1] : box[3], box[0] : box[2]]
    return num


def get_images_from_dir(image_dir, image_file_extensions):
    image_dir = Path(image_dir)
    image_files = [f for f in image_dir.iterdir() if f.suffix in image_file_extensions]
    return image_files


class AgeGenderDetector:
    def __init__(
        self,
        face_detector_path="models/version-RFB-640.onnx",
        age_classifier_path="models/age_googlenet.onnx",
        gender_classifier_path="models/gender_googlenet.onnx",
    ):
        self.ageList = [
            "(0-2)",
            "(4-6)",
            "(8-12)",
            "(15-20)",
            "(25-32)",
            "(38-43)",
            "(48-53)",
            "(60-100)",
        ]
        session_options = ort.SessionOptions()
        session_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
        # session_options.log_severity_level = 0
        # session_options.enable_profiling = True
        self.runtime_providers = [("CUDAExecutionProvider", {"cudnn_conv_use_max_workspace": '1'}), "CPUExecutionProvider"]
        self.genderList = ["Male", "Female"]
        self.image_file_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]

        self.face_detector_path = face_detector_path
        self.age_classifier_path = age_classifier_path
        self.gender_classifier_path = gender_classifier_path

        self.face_detector = ort.InferenceSession(
            self.face_detector_path, sess_options= session_options, providers=self.runtime_providers
        )
        self.age_classifier = ort.InferenceSession(
            self.age_classifier_path, sess_options= session_options, providers=self.runtime_providers
        )
        self.gender_classifier = ort.InferenceSession(
            self.gender_classifier_path, sess_options= session_options, providers=self.runtime_providers
        )

    def faceDetector(self, orig_image, threshold=0.7):
        image = cv2.cvtColor(orig_image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (640, 480))
        image_mean = np.array([127, 127, 127])
        image = (image - image_mean) / 128
        image = np.transpose(image, [2, 0, 1])
        image = np.expand_dims(image, axis=0)
        image = image.astype(np.float32)

        input_name = self.face_detector.get_inputs()[0].name
        confidences, boxes = self.face_detector.run(None, {input_name: image})
        boxes, labels, probs = predict(
            orig_image.shape[1], orig_image.shape[0], confidences, boxes, threshold
        )
        return boxes, labels, probs

    def genderClassifier(self, orig_image):
        image = cv2.cvtColor(orig_image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (224, 224))
        image_mean = np.array([104, 117, 123])
        image = image - image_mean
        image = np.transpose(image, [2, 0, 1])
        image = np.expand_dims(image, axis=0)
        image = image.astype(np.float32)

        input_name = self.gender_classifier.get_inputs()[0].name
        genders = self.gender_classifier.run(None, {input_name: image})
        gender = self.genderList[genders[0].argmax()]
        return gender

    def ageClassifier(self, orig_image):
        image = cv2.cvtColor(orig_image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (224, 224))
        image_mean = np.array([104, 117, 123])
        image = image - image_mean
        image = np.transpose(image, [2, 0, 1])
        image = np.expand_dims(image, axis=0)
        image = image.astype(np.float32)

        input_name = self.age_classifier.get_inputs()[0].name
        ages = self.age_classifier.run(None, {input_name: image})
        age = self.ageList[ages[0].argmax()]
        return age

    def predict_age_and_gender(self, image_path):
        orig_image = cv2.imread(image_path)
        boxes, labels, probs = self.faceDetector(orig_image)

        preds = []
        for i in range(boxes.shape[0]):
            box = scale(boxes[i, :])
            cropped = cropImage(orig_image, box)
            gender = self.genderClassifier(cropped)
            age = self.ageClassifier(cropped)
            preds.append(
                {
                    "box": [int(e) for e in box],
                    "gender": gender,
                    "age": age,
                }
            )
        return preds

    def predict_age_and_gender_on_dir(self, image_dir):
        image_files = get_images_from_dir(image_dir, self.image_file_extensions)
        preds = {}
        for image_file in image_files:
            pred = self.predict_age_and_gender(image_file)
            preds[str(image_file)] = pred
        return preds


if __name__ == "__main__":
    # Example usage
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_dir", type=str, required=True, help="Image directory")
    args = parser.parse_args()

    detector = AgeGenderDetector()
    preds = detector.predict_age_and_gender_on_dir(args.image_dir)
    pprint(preds)  # Print the predictions for all images in the directory
