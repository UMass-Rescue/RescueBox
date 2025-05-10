## Age and Gender Classification

### Installation and Setup

**Install `pipx`:** To manage `poetry`, this is recommended as it isolates Poetry in its own virtual environment, preventing conflicts with system-wide Python packages.
    
    # macOS
    brew update
    brew install pipx
    pipx ensurepath

    # linux (debian)
    sudo apt update
    sudo apt install pipx
    export PATH="$HOME/.local/bin:$PATH"

    # alt, not recommended
    python -m pip install --user pipx
    python -m pipx ensurepath

**Install `poetry`:** Restart or refresh your shell, install Poetry, and set desired Python version (>=3.11).

    source ~/.bashrc

    pipx install poetry
    poetry env use 3.11.1

**Activate venv:** Set configurations, create a virtual environment, and activate it. Note: use `poetry init` when starting a new project from scratch, use `poetry install` to set up dependencies from an existing lock file.

    poetry config virtualenvs.create true
    poetry config virtualenvs.in-project true

    poetry install
    # If you are on Mac OS run:
    source .venv/bin/activate
    # If you are on Windows run instead:
    source .venv/Scripts/activate

To install or remove packages, respectively, use `poetry add` and `poetry remove`.

    poetry add [--dev] <package_name>
    poetry remove [--dev] <package_name>

**Set environment variables:** From the project root directory, set the `PYTHONPATH` environment variable to make local directories accessible for import in your venv, and define any other vars in a `.env` file; follow `.env.sample`

    export PYTHONPATH=$(pwd):$PYTHONPATH
    set -a; source .env; set +a

**Get the ONNX models**

In order to run survey_models.py you must download the onnx model files from either this GoogleDrive [link](https://drive.google.com/drive/folders/1IgG6w6lJ9cd8Qlckd7HwdBUjWCd_-gxN), or this GoogleDrive [link](https://drive.google.com/drive/folders/1e01jA5WXsukK_NwNnNx4iL50jRCMZQXF), then copy them in their respective directories.

    cp ~/Downloads/v001_model.onnx src/onnx_models/age_classify_v001/v001_model.onnx 
    cp ~/Downloads/vit_model.onnx src/onnx_models/vit_age_classifier/vit_model.onnx
    cp ~/Downloads/fareface_age.onnx src/onnx_models/fareface/fareface_age.onnx

Alternatively, you could run the `convert_to_onnx.py` files in each directory to regenerate the respective ONNX files.

Your models directory structure should then look like this:
```
/onnx_models
--/age_classify_v001
----convert_to_onnx.py
----model.py
----v001_model.onnx
--/vit_age_classifier
----convert_to_onnx.py
----model.py
----vit_model.onnx
--surbey_models.py
```


You are good to go!

---

### Start the server...
    python src/server/server-onnx.py

**... And open Rescue Box:** With the server running, register the models in the Rescue Box desktop application (`localhost:5000`), and use as inputs test images located in `src/onnx_models/test_images/`. 

Results will be displayed as a JSON blob in the desktop app, and be written to a SQLite database at the project's root directory, in a table named `model_output`. Each run will generate the same `created_at` timestamp in the table (for each image and each model).

To confirm results were successfully written to the DB, simply log into a `venv` interpreter and run the following:

    from src.utils.common import read_db
    df = read_db("model_output", "select * from MODEL_OUTPUT order by created_at desc")
    df.head()


