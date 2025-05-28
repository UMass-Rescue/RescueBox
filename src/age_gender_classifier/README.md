## Age and Gender Classification

### Additional Setup and Notes

- **XGBoost dependency:** Mac OSX users must have OpenMP runtime installed for XGBoost to work. On Mac OSX run this command to install. 
```
brew install libomp
```

- **Database SQLite:** Using the connection ORMs defined in `src/age_gender_classifier/age_gender_classifier/utils/sqlAlchemy_manager.py`, and a default environment variable in the file that sets the connection string, our project writes model output to a SQLite database called `age_classifier.db` that is created at the project's root.

- **Get the ONNX models**  
In order to run survey_models.py you must download the onnx model files from either this GoogleDrive [link](https://drive.google.com/drive/folders/1IgG6w6lJ9cd8Qlckd7HwdBUjWCd_-gxN), or this shared GoogleDrive [link](https://drive.google.com/drive/folders/1e01jA5WXsukK_NwNnNx4iL50jRCMZQXF), then copy them in their respective directories.

    cp ~/Downloads/v001_model.onnx src/onnx_models/age_classify_v001/v001_model.onnx 
    cp ~/Downloads/vit_model.onnx src/onnx_models/vit_age_classifier/vit_model.onnx
    cp ~/Downloads/fareface_age.onnx src/onnx_models/fareface/fareface_age.onnx  

    Alternatively, you could run the `convert_to_onnx.py` files in each directory to regenerate the respective ONNX files.

You are good to go!

---

### Run on the command line
```
poetry run python src/age_gender_classifier/age_gender_classifier/server/server_onnx.py /age-classifier/age_classifier src/age_gender_classifier/age_gender_classifier/onnx_models/test_images 20
```
