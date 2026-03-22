# Age and Gender Classifier

Age and Gender Classifier detects faces in images and predicts the gender and age range of each face.

## Inputs

- **Image Directory:** Path to a directory containing images to analyze.

## Outputs

- **Batch File Response:** Each detected face is returned with metadata:
  - **Image Path:** Source image path for several files in this directory
  - **Gender:** Male or Female
  - **Age:** Age range (e.g. "25-32")
  - **Bounding Box:** Coordinates [x, y, w, h] of the face region

### Sample Output one for each file in source path

```json
{
  "/path/to/source_image.jpg",
  ["box": [51, 122, 328, 399],
  "gender": "Male",
  "age": "(25-32)"]
}
```

Results can be viewed in the Jobs page. Each face is shown with its bounding box overlay and metadata.
